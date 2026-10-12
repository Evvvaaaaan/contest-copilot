#!/usr/bin/env python3
"""Build evidence-linked local submission files; never submit or certify consent."""

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import tempfile
import zipfile

import manage_state


ASSETS = Path(__file__).resolve().parents[1] / "assets"
KINDS = {"implemented": "구현 결과", "measured": "측정 결과",
         "simulated": "가상 실험 결과", "planned": "계획 및 예상"}


class Report:
    """Render known report blocks without interpreting user text as markup."""

    def __init__(self):
        self.lines, self.fragments = [], []
        self.list_open = False

    def close_list(self):
        if self.list_open:
            self.fragments.append("</ul>")
            self.list_open = False

    def heading(self, text, level=2):
        self.close_list()
        escaped = html.escape(str(text))
        self.lines.extend(["", "#" * level + " " + escaped, ""])
        self.fragments.append(f"<h{level}>{escaped}</h{level}>")

    def paragraph(self, text):
        self.close_list()
        escaped = html.escape(str(text))
        self.lines.extend([escaped, ""])
        self.fragments.append("<p>" + escaped + "</p>")

    def item(self, text, label=None, detail=False):
        escaped = html.escape(str(text))
        prefix = "<strong>" + html.escape(label) + "</strong>: " if label else ""
        md_prefix = "**" + html.escape(label) + "**: " if label else ""
        self.lines.append(("  - " if detail else "- ") + md_prefix + escaped)
        if not self.list_open:
            self.fragments.append("<ul>")
            self.list_open = True
        self.fragments.append(('<li class="detail">' if detail else '<li>') + prefix + escaped + "</li>")

    def render(self):
        self.close_list()
        return "\n".join(self.lines).strip() + "\n", "\n".join(self.fragments)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, raw):
    require(isinstance(raw, str) and raw.strip(), "A file path is required.")
    relative = Path(raw)
    require(not relative.is_absolute() and ".." not in relative.parts,
            "File paths must be relative and cannot traverse outside the workspace.")
    resolved = (root / relative).resolve()
    require(resolved.is_relative_to(root), "File resolves outside the workspace.")
    require(resolved.is_file(), f"File does not exist: {raw}")
    return resolved


def indexed(records, field):
    items = records.get(field, [])
    require(isinstance(items, list), f"records.{field} must be an array.")
    return {item["id"]: item for item in items}


def build(workspace, spec):
    """Return a manifest. Invalid/stale input raises ValueError; limits block readiness."""
    root = Path(workspace).resolve()
    require(root.is_dir(), "Workspace does not exist.")
    spec = manage_state.read_json(spec) if isinstance(spec, (str, Path)) else spec
    require(isinstance(spec, dict), "Submission specification must be an object.")
    # The shipped schema is also the runtime field/format contract.
    schema = manage_state.read_json(ASSETS / "submission-spec.json")
    for field in schema["required"]:
        require(field in spec, f"Missing submission field: {field}")
    for field in ("project", "title"):
        require(manage_state.nonempty(spec[field]), f"{field} must not be blank.")
    progress_path = inside(root, "progress.json")
    watched = {progress_path: manage_state.fingerprint(progress_path)}
    state = manage_state.read_json(progress_path)
    status = manage_state.report(state)
    require(status["status"] == "ready_for_user_review",
            "All required conditions must currently pass before packaging.")
    require(spec["project"] == status["project"], "Project does not match acceptance contract.")
    accepted = spec["accepted"]
    require(isinstance(accepted, dict), "accepted must be an object.")
    require(manage_state.nonempty(accepted.get("decision_reference")),
            "An explicit user acceptance decision reference is required.")
    for field in ("artifact_version", "contract_version", "iteration"):
        require(accepted.get(field) == status[field], f"Stale acceptance: {field} differs.")
    # Check all accepted files again at the end, including evidence omitted from prose.
    current = state["iterations"][-1]
    for item in current["artifacts"]:
        watched[Path(item["path"])] = item["sha256"]
    for result in current["results"].values():
        for item in result["evidence"]:
            watched[Path(item["path"])] = item["sha256"]

    records_path = root / "records.json"
    records = manage_state.read_json(inside(root, "records.json")) if records_path.exists() else {}
    if records_path.exists():
        watched[records_path] = manage_state.fingerprint(records_path)
    sources, decisions = indexed(records, "sources"), indexed(records, "decisions")
    document = Report()
    document.heading(spec["title"], 1)
    document.paragraph("상태: 로컬 제출 준비 자료 — 외부 제출되지 않음")
    document.paragraph("승인된 결과물 버전: " + str(accepted["artifact_version"]))
    document.heading("공식 제출 요구사항")
    instructions = spec["official_instructions"]
    require(isinstance(instructions, list) and instructions, "Official instructions are required.")
    referenced_sources, blockers = set(), []
    conditions = {item["id"]: item for item in status["conditions"]}
    for rule in instructions:
        require(isinstance(rule, dict) and manage_state.nonempty(rule.get("id"))
                and manage_state.nonempty(rule.get("text")), "Official rules require id and text.")
        if rule.get("source_id"):
            require(rule["source_id"] in sources, f"Unknown official source: {rule['source_id']}")
            referenced_sources.add(rule["source_id"])
        mapped = rule.get("condition_ids", [])
        require(isinstance(mapped, list), "Official condition_ids must be an array.")
        if not mapped or any(key not in conditions or conditions[key]["verdict"] != "pass" for key in mapped):
            blockers.append({"instruction_id": rule["id"], "reason": "official_requirement_not_verified"})
        document.item(rule["id"] + ": " + rule["text"])
    document.heading("검증 결과")
    for condition in status["conditions"]:
        verdict_labels = {"pass": "통과", "fail": "실패", "unverified": "미검증", "waived": "제외"}
        document.item(f"{condition['id']}: {condition['requirement']} — {verdict_labels.get(condition['verdict'], condition['verdict'])}")
    require(isinstance(spec["sections"], list) and spec["sections"], "At least one section is required.")
    claim_count = 0
    for section in spec["sections"]:
        require(manage_state.nonempty(section.get("title")), "Section title is required.")
        document.heading(section["title"])
        require(isinstance(section.get("claims"), list), "Section claims must be an array.")
        for claim in section["claims"]:
            require(claim.get("kind") in KINDS and manage_state.nonempty(claim.get("text")),
                    "Each claim needs a supported kind and text.")
            evidence = claim.get("evidence", [])
            require(isinstance(evidence, list), "Claim evidence must be an array.")
            require(claim["kind"] == "planned" or evidence,
                    "Implemented, measured and simulated claims require evidence files.")
            document.item(claim["text"], label=KINDS[claim["kind"]])
            for entry in evidence:
                path = inside(root, entry.get("path"))
                require(manage_state.fingerprint(path) == entry.get("sha256"),
                        f"Stale or missing evidence hash: {entry.get('path')}")
                watched[path] = entry["sha256"]
                document.item(entry["path"] + " (SHA-256: " + entry["sha256"] + ")", label="근거", detail=True)
            for source_id in claim.get("source_ids", []):
                require(source_id in sources, f"Unknown source ID: {source_id}")
                referenced_sources.add(source_id)
                document.item(source_id, label="출처", detail=True)
            claim_count += 1
    require(claim_count > 0, "At least one substantive claim is required.")
    document.heading("사용자 기여 및 선택")
    for decision_id in spec.get("user_decision_ids", []):
        require(decision_id in decisions, f"Unknown decision ID: {decision_id}")
        decision = decisions[decision_id]
        require(decision.get("actor") == "user", f"Decision is not attributed to the user: {decision_id}")
        document.item(decision_id, label="사용자 결정")
        for field, label in (("original", "처음 생각"), ("revised", "선택한 내용"),
                             ("reason", "변경 이유"), ("message_ref", "대화 참조"), ("revision", "기록 버전")):
            if decision.get(field) is not None:
                document.item(decision[field], label=label, detail=True)
    if not spec.get("user_decision_ids"):
        document.paragraph("참조된 사용자 기여 기록 없음. 승인 참조만으로 기여 내용을 추정하지 않음.")
    document.heading("출처")
    for source_id in sorted(referenced_sources):
        source = sources[source_id]
        if source.get("status") != "inspected":
            blockers.append({"source_id": source_id, "reason": "source_not_inspected"})
        if source.get("path"):
            path = inside(root, source["path"])
            require(manage_state.fingerprint(path) == source.get("sha256"),
                    f"Source file changed since inspection: {source_id}")
            watched[path] = source["sha256"]
        document.item(str(source.get("title", source_id)) + " [" + source_id + "]")
        for field, label in (("url", "주소"), ("path", "파일"), ("locator", "원문 위치"),
                             ("accessed_at", "확인 날짜"), ("published_at", "발행 날짜"),
                             ("excerpt", "확인한 원문"), ("revision", "기록 버전"), ("sha256", "파일 SHA-256")):
            if source.get(field) not in (None, ""):
                document.item(source[field], label=label, detail=True)
    document.heading("해석상의 한계")
    document.paragraph("가상 실험은 실제 사용자 조사나 채택률이 아닙니다. 계획은 구현·측정 결과가 아닙니다.")
    document.paragraph("파일 해시와 기록을 확인했으며, 주장 자체의 타당성이나 사용자 승인의 진위는 이 도구가 판정하지 않습니다.")
    markdown, body = document.render()
    template = (ASSETS / "report.html").read_text(encoding="utf-8")
    replacements = {"title": html.escape(spec["title"]), "content": body}
    rendered = re.sub(r"\{\{(title|content)\}\}", lambda match: replacements[match.group(1)], template)
    formats = spec["formats"]
    require(isinstance(formats, list) and formats, "At least one output format is required.")
    names, outputs = set(), []
    destination = root / "submission"
    require(not destination.is_symlink(), "Submission destination cannot be a symlink.")
    destination.mkdir(exist_ok=True)
    previous = {}
    manifest_path = destination / "manifest.json"
    if manifest_path.exists():
        require(not manifest_path.is_symlink(), "Manifest cannot be a symlink.")
        for output in manage_state.read_json(manifest_path).get("outputs", []):
            name = output["filename"]
            require(Path(name).name == name and name not in (".", "..", "manifest.json"),
                    "Previous manifest has an unsafe filename.")
            previous[name] = output["sha256"]
    for name, digest in previous.items():
        path = destination / name
        require(not path.is_symlink() and (not path.exists() or manage_state.fingerprint(path) == digest),
                "Previously generated output was edited; preserve it before rebuilding.")
    with tempfile.TemporaryDirectory(prefix=".submission-", dir=root) as temporary:
        staging = Path(temporary)
        for request in formats:
            fmt, name = request.get("format"), request.get("filename")
            require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9가-힣][A-Za-z0-9가-힣_. -]*", name)
                    and name not in ("manifest.json", ".", "..") and name not in names,
                    "Output filenames must be unique safe basenames, excluding manifest.json.")
            names.add(name)
            if fmt not in schema["supported_formats"]:
                blockers.append({"filename": name, "reason": "unsupported_format", "format": fmt})
                continue
            require(name.lower().endswith("." + fmt), "Output extension must match its actual format.")
            path = staging / name
            if fmt == "zip":
                files = spec.get("source_files", [])
                require(isinstance(files, list) and files, "A source ZIP requires explicit source_files.")
                with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    for raw in dict.fromkeys(files):
                        source = inside(root, raw)
                        require("submission" not in Path(raw).parts, "Do not include generated packages in source ZIP.")
                        watched[source] = manage_state.fingerprint(source)
                        if not any(Path(item["path"]).resolve() == source for item in current["artifacts"]):
                            blockers.append({"path": raw, "reason": "source_file_not_in_accepted_snapshot"})
                        archive.write(source, Path(raw).as_posix())
                with zipfile.ZipFile(path) as archive:
                    require(archive.testzip() is None, "ZIP verification failed.")
            else:
                path.write_text(markdown if fmt == "md" else rendered, encoding="utf-8")
                require(path.read_text(encoding="utf-8") == (markdown if fmt == "md" else rendered),
                        "Written report did not match rendered content.")
            size = path.stat().st_size
            if "max_bytes" in request:
                require(type(request["max_bytes"]) is int and request["max_bytes"] > 0,
                        "max_bytes must be a positive integer.")
                if size > request["max_bytes"]:
                    blockers.append({"filename": name, "reason": "size_limit_exceeded"})
            if any(key in request for key in ("max_pages", "min_pages", "exact_pages")):
                blockers.append({"filename": name, "reason": "page_count_requires_rendered_format_check"})
            outputs.append({"filename": name, "format": fmt, "bytes": size,
                            "sha256": manage_state.fingerprint(path)})
        for path, digest in watched.items():
            require(path.is_file() and manage_state.fingerprint(path) == digest,
                    f"Input changed during packaging: {path.name}")
        for output in outputs:
            target = destination / output["filename"]
            require(not target.is_symlink(), "Output file cannot be a symlink.")
            require(not target.exists() or output["filename"] in previous,
                    "Refusing to overwrite an output not tracked by the previous manifest.")
            require(target.resolve() not in {path.resolve() for path in watched},
                    "An output cannot overwrite a submission input.")
        for output in outputs:
            target = destination / output["filename"]
            (staging / output["filename"]).replace(target)
        for name in set(previous) - {output["filename"] for output in outputs}:
            stale = destination / name
            if stale.exists():
                stale.unlink()
    manifest = {"schema_version": 1, "project": spec["project"], "title": spec["title"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "not_ready" if blockers else "ready_for_local_review",
                "externally_submitted": False, "accepted": accepted,
                "spec_sha256": hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                "official_instructions": instructions, "outputs": outputs, "blockers": blockers,
                "input_files": [{"path": str(path), "sha256": digest} for path, digest in watched.items()],
                "checks": {"required_conditions_pass": True, "acceptance_version_matches": True,
                           "input_hashes_match": True, "output_readback": True,
                           "user_consent_authenticated": False, "visual_render_review": "not_performed"}}
    manage_state.save(destination / "manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.workspace, args.spec), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"Submission build failed: {exc}\n")


if __name__ == "__main__":
    main()
