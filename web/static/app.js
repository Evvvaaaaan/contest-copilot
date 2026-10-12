const $ = (id) => document.getElementById(id);
const phases = [['research','공고 조사'],['idea_assessment','아이디어 평가'],['planning','기획'],['simulation','영향 검토'],['development','개발'],['validation','검증'],['user_feedback','결과 확인'],['finalization','제출물 준비']];
let token, selected = localStorage.getItem('contest-project'), current = null, busy = false, connected = false;
let previousMessages = '', previousProjects = '', polling = false;
let previousDetails = '';
const drafts = new Map();

async function api(path, body) {
  const options = body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-Local-Token':token},body:JSON.stringify(body)};
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '요청을 처리하지 못했습니다.');
  return data;
}
function notice(message) { $('notice').textContent = message || ''; $('notice').hidden = !message; }
function node(tag, content, className) { const el = document.createElement(tag); if (content !== undefined) el.textContent = content; if(className) el.className = className; return el; }
function safeUrl(raw) { try { const url = new URL(raw); return ['http:','https:'].includes(url.protocol) ? url.href : null; } catch { return null; } }
function inline(parent, value) {
  const pattern = /(\[[^\]]+\]\(https?:\/\/[^\s)]+\)|\*\*[^*]+\*\*|`[^`]+`|https?:\/\/[^\s<>]+)/g;
  let offset = 0;
  for (const match of value.matchAll(pattern)) {
    parent.append(document.createTextNode(value.slice(offset, match.index)));
    const part = match[0];
    if (part.startsWith('**')) parent.append(node('strong', part.slice(2,-2)));
    else if (part.startsWith('`')) parent.append(node('code', part.slice(1,-1)));
    else {
      const md = part.match(/^\[([^\]]+)\]\((.+)\)$/), label = md ? md[1] : part, url = safeUrl(md ? md[2] : part);
      if (url) { const a = node('a',label); a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; parent.append(a); }
      else parent.append(document.createTextNode(part));
    }
    offset = match.index + part.length;
  }
  parent.append(document.createTextNode(value.slice(offset)));
}
function markdown(parent, value) {
  let code = null, list = null;
  for (const line of value.split('\n')) {
    if (line.startsWith('```')) { if(code) code=null; else {code=node('pre','');parent.append(code);} list=null; continue; }
    if (code) { code.textContent += line+'\n'; continue; }
    if (!line.trim()) {list=null;continue;}
    const heading = line.match(/^(#{1,4})\s+(.+)$/), bullet = line.match(/^(?:[-*]|\d+[.)])\s+(.+)$/);
    if(heading) {const h=node('h'+Math.min(heading[1].length+1,4));inline(h,heading[2]);parent.append(h);list=null;}
    else if(bullet) {if(!list){list=node(/^\d/.test(line)?'ol':'ul');parent.append(list);} const li=node('li');inline(li,bullet[1]);list.append(li);}
    else {const p=node('p');inline(p,line);parent.append(p);list=null;}
  }
}
async function connection() {
  try {const result=await api('/api/session');token=result.token;connected=result.connection.available;$('connection').textContent=result.connection.message;$('connection-dot').classList.toggle('online',connected);if(!connected)notice(result.connection.message);controls();}
  catch(error){connected=false;$('connection').textContent='앱 연결 끊김';notice('로컬 앱에 연결할 수 없습니다. 서버 실행 상태를 확인해 주세요.');controls();}
}
function controls() {
  const running=current?.status==='running';
  $('send').disabled=!connected || busy || !$('message').value.trim();
  $('send').textContent=running?'중단 후 보내기':'보내기 ↑';
  $('stop').hidden=!running; $('stop').disabled=busy;
  $('attach').disabled=busy || running;
  document.querySelectorAll('.workflow-action').forEach(button=>{
    button.disabled=busy || running || !connected || button.dataset.unavailable==='true';
  });
}
async function listProjects() {
  const projects=await api('/api/projects');
  const encoded=JSON.stringify([selected,projects]);
  if(encoded===previousProjects)return projects;
  previousProjects=encoded;$('project-list').replaceChildren();
  if(!projects.length)$('project-list').append(node('p','아직 프로젝트가 없습니다.','nav-empty'));
  for(const project of projects){const button=node('button',undefined,'project'+(project.id===selected?' active':''));button.append(node('span',project.title));button.title=project.title;button.onclick=()=>select(project.id);$('project-list').append(button);}
  return projects;
}
async function select(id) {
  if(selected)drafts.set(selected,$('message').value);
  $('message').value=drafts.get(id)||'';
  selected=id;localStorage.setItem('contest-project',id);previousMessages='';current=null;
  previousDetails='';
  $('welcome').hidden=true;$('workspace').hidden=false;notice('');
  await refresh();await listProjects();$('message').focus();
}
function renderMessages(messages) {
  const encoded=JSON.stringify(messages);if(encoded===previousMessages)return;
  previousMessages=encoded;const area=$('messages'),nearBottom=area.scrollHeight-area.scrollTop-area.clientHeight<100;
  area.replaceChildren();
  if(!messages.length){const empty=node('div',undefined,'conversation-empty');empty.append(node('h2','어떤 공모전을 준비하고 있나요?'),node('p','공고 링크나 자료를 보내 주세요. 먼저 조건과 심사 기준을 조사하고, 당신의 생각을 듣겠습니다.'));area.append(empty);}
  for(const message of messages){const article=node('article',undefined,'message '+message.role);if(message.role==='system'){article.textContent=message.text;}else{const author=node('div',message.role==='user'?'나':message.role==='error'?'실행 오류':'Contest Copilot','author');const body=node('div',undefined,'body');if(message.role==='assistant')markdown(body,message.text);else body.textContent=message.text;article.append(author,body);}area.append(article);}
  if(nearBottom || messages.at(-1)?.role==='user')area.scrollTop=area.scrollHeight;
}
function renderDetails(data) {
  const encoded=JSON.stringify([data.phase,data.summary,data.next_action,data.preview_url,data.status,data.progress,data.progress_error,data.files,data.workflow,data.proposal,data.records,data.simulations,data.submission,data.simulation_plan,data.submission_spec]);
  if(encoded===previousDetails)return;previousDetails=encoded;
  const expanded=new Set([...document.querySelectorAll("details[open]")].map(el=>el.id||el.querySelector("summary")?.textContent));
  $('phases').replaceChildren();
  phases.forEach(([key,label],i)=>{const li=node('li',undefined,key===data.phase?'current':'');li.append(node('span',String(i+1).padStart(2,'0'),'phase-number'),node('span',label));if(key===data.phase)li.append(node('small','현재 단계'));$('phases').append(li);});
  $('summary').textContent=data.summary;$('next-action').textContent=data.next_action || '대화를 시작하면 다음 작업이 정해집니다.';
  $('run-label').textContent=({running:'작업 중',idle:'대기',failed:'오류 확인',interrupted:'중단됨'})[data.status]||'대기';
  $('checks').replaceChildren();const progress=data.progress;
  $('iteration').textContent=progress?`${progress.iteration}회 검토`:'';
  if(data.progress_error)$('checks').append(node('p',data.progress_error,'muted'));
  else if(!progress)$('checks').append(node('p','목표와 통과 조건을 합의하면 여기에 표시됩니다.','muted'));
  else {
    const statuses={pass:'통과',fail:'실패',unverified:'미검증',waived:'제외'};
    for(const condition of progress.conditions){
      const detail=node('details',undefined,'check-detail'),row=node('summary',undefined,'check '+condition.verdict);
      row.append(node('span',statuses[condition.verdict]),node('b',(condition.requirement||condition.id)+(condition.required?' · 필수':'')));detail.append(row);
      for(const [label,value] of [['통과 기준',condition.target],['검증 방법',condition.method],['확인 내용',condition.record?.note]])if(value)detail.append(node('p',`${label}: ${value}`,'status-note'));
      const reasons={feedback_pending:'추가 의견을 반영한 재검증을 기다립니다.',no_result:'아직 검증하지 않았습니다.',contract_changed:'목표 조건이 바뀌어 재검증이 필요합니다.',artifact_changed_or_missing:'대상 파일이 바뀌거나 없어졌습니다.',evidence_changed_or_missing:'근거 파일이 바뀌거나 없어졌습니다.'};
      if(condition.reason)detail.append(node('p',reasons[condition.reason]||condition.reason,'status-note'));
      for(const evidence of condition.record?.evidence||[]){if(evidence.path.startsWith(data.workspace+'/')){const path=evidence.path.slice(data.workspace.length+1);const link=node('a','근거: '+path,'file');link.href=`/api/projects/${data.id}/file?path=${encodeURIComponent(path)}`;link.download='';detail.append(link);}}
      $('checks').append(detail);
    }
    const labels={ready_for_user_review:'필수 조건을 충족했습니다. 결과를 확인해 주세요.',limit_reached:'반복 한도에 도달했습니다. 미충족 조건을 확인해 주세요.',in_progress:`남은 필수 조건 ${progress.unmet_required.length}개`};
    $('checks').append(node('p',labels[progress.status],'status-note'));
  }
  const preview=safeUrl(data.preview_url);$('preview').hidden=!preview;if(preview)$('preview').href=preview;
  $('files').replaceChildren();$('file-count').textContent=data.files.length||'';
  if(!data.files.length)$('files').append(node('p','첨부 자료와 생성된 결과물이 표시됩니다.','muted'));
  for(const file of data.files){const a=node('a',undefined,'file');a.append(node('span',file.path),node('small',`${Math.max(1,Math.round(file.size/1024))} KB`));a.href=`/api/projects/${selected}/file?path=${encodeURIComponent(file.path)}`;a.download='';$('files').append(a);}
  $('workspace-path').textContent=data.workspace;
  renderWorkflow(data);renderRecords(data);renderSimulations(data);renderSubmission(data);
  document.querySelectorAll("details").forEach(el=>{if(expanded.has(el.id||el.querySelector("summary")?.textContent))el.open=true;});
}
function recordText(parent,label,value) {
  if(value===undefined || value===null || value==='')return;
  const text=Array.isArray(value)?value.map(item=>typeof item==='string'?item:JSON.stringify(item)).join(' · '):typeof value==='object'?JSON.stringify(value):String(value);
  parent.append(node('p',`${label}: ${text}`,'status-note'));
}
function recordsList(value) {return Array.isArray(value)?value:value && typeof value==='object'?Object.values(value):[];}
function recordGroup(parent,label,items,render) {
  if(!items.length)return;
  parent.append(node('h3',`${label} · ${items.length}`));
  for(const item of items){const entry=node('div',undefined,'record-entry');render(entry,item);parent.append(entry);}
}
function renderWorkflow(data) {
  const workflow=data.workflow,proposal=data.proposal;
  $('workflow-section').hidden=!workflow&&!proposal;
  const statuses={running:'자동 진행 중',interrupted:'중단됨',needs_user:'의견 필요',failed:'오류 확인 필요',limit_reached:'실행 한도 도달',stalled:'개선 정체',ready_for_user_review:'필수 조건 충족 · 결과 확인 필요'};
  const roles={developer:'개발 담당',reviewer:'검토 담당',simulation:'시뮬레이션 담당'};
  $('workflow-role').textContent=roles[workflow?.role]||'';
  const details=[];
  if(workflow){details.push(statuses[workflow.status]||'진행 상태 확인 중');if(workflow.turns!==undefined)details.push(`${workflow.turns}회 실행`);if(workflow.elapsed_seconds!==undefined)details.push(`${Math.floor(workflow.elapsed_seconds/60)}분 경과`);if(workflow.reason)details.push(workflow.reason);}
  else details.push('목표와 실행 한도를 확인해 주세요. 승인 후에는 조건을 충족할 때까지 개발과 검토를 반복합니다.');
  $('workflow-status').textContent=details.join(' · ');
  const body=$('contract-content');body.replaceChildren();
  const contract=proposal?.value?.contract||workflow?.contract,limits=proposal?.value?.limits||workflow?.limits;
  $('contract-details').hidden=!contract&&!limits;
  if(contract){recordText(body,'목적',contract.intent);recordText(body,'검토 한도',contract.max_iterations===undefined?undefined:`${contract.max_iterations}회`);
    for(const condition of contract.conditions||[]){const entry=node('div',undefined,'record-entry');entry.append(node('p',`${condition.required?'필수':'선택'} · ${condition.requirement||condition.id}`,'record-title'));recordText(entry,'통과 기준',condition.target);recordText(entry,'확인 방법',condition.method);body.append(entry);}}
  if(limits){recordText(body,'실행 한도',limits.max_turns===undefined?undefined:`${limits.max_turns}회`);recordText(body,'시간 한도',limits.max_seconds===undefined?undefined:`${Math.round(limits.max_seconds/60)}분`);recordText(body,'정체 판단',limits.stagnation_rounds===undefined?undefined:`${limits.stagnation_rounds}회 연속 개선 없음`);}
  $('approve-workflow').hidden=!proposal || proposal.hash===workflow?.proposal_hash;
  $('resume-workflow').hidden=!workflow || !['interrupted','needs_user','failed'].includes(workflow.status);
}
function renderRecords(data) {
  const records=data.records||{},sources=recordsList(records.sources),claims=recordsList(records.claims),decisions=recordsList(records.decisions),documents=recordsList(records.documents);
  $('records-section').hidden=!(sources.length+claims.length+decisions.length+documents.length);
  $('record-count').textContent=`근거 ${sources.length} · 결정 ${decisions.length}`;
  const body=$('records');body.replaceChildren();
  recordGroup(body,'출처',sources,(entry,item)=>{const title=item.title||item.id||'자료',url=safeUrl(item.url);if(url){const link=node('a',title,'record-link');link.href=url;link.target='_blank';link.rel='noopener noreferrer';entry.append(link);}else entry.append(node('p',title,'record-title'));recordText(entry,'확인일',item.accessed_at||item.retrieved_at||item.checked_at);recordText(entry,'위치',item.locator||item.location);});
  const labels={confirmed:'확인됨',needs_research:'추가 조사 필요',no_public_evidence_found:'공개 근거 미확인',conflicting:'근거 충돌',measured:'실측',inferred:'추론',predicted:'예측',hypothesis:'가설'};
  recordGroup(body,'주장과 근거',claims,(entry,item)=>{entry.append(node('p',item.text||item.claim||item.statement||item.id,'record-title'));recordText(entry,'구분',({fact:'사실',interpretation:'해석',prediction:'예측'})[item.kind]);recordText(entry,'상태',labels[item.status]||item.status);recordText(entry,'근거',item.source_ids||item.sources);recordText(entry,'한계',item.limitations||item.uncertainty);});
  recordGroup(body,'사용자 생각과 결정',decisions,(entry,item)=>{recordText(entry,'작성자',({user:'사용자',assistant:'AI'})[item.actor]);recordText(entry,'원안',item.user_input||item.user_idea||item.original);recordText(entry,'제안',item.proposal||item.ai_proposal);recordText(entry,'변경 내용',item.revised);recordText(entry,'결정',item.decision||item.choice||item.selected);recordText(entry,'이유',item.reason||item.rationale);if(!entry.children.length)recordText(entry,'내용',item.text||item.id);});
  recordGroup(body,'첨부 문서 확인',documents,(entry,item)=>{entry.append(node('p',item.path||item.name||item.id,'record-title'));recordText(entry,'읽기 상태',({read:'읽음',complete:'읽음',partial:'일부만 읽음',unread:'미확인',failed:'읽기 실패',extracted:'텍스트 추출됨',unsupported:'직접 확인 필요',unavailable:'내용 확인 불가'})[item.status]||item.status);recordText(entry,'확인 범위',item.pages_read||item.coverage);if(item.pages)recordText(entry,'기록된 분량',`${item.pages.length}개 페이지 또는 논리 구간`);recordText(entry,'미확인 범위',item.unread_pages||item.missing_pages);recordText(entry,'제약',item.note||item.limitations||item.error);});
}
function renderSimulations(data) {
  const plan=data.simulation_plan,runs=data.simulations||[];
  $('simulation-section').hidden=!plan&&!runs.length;
  $('simulation-count').textContent=runs.length?`${runs.length}회 기록`:'';
  const planBody=$('simulation-plan');planBody.replaceChildren();
  if(plan){const config=plan.value;recordText(planBody,'질문',config.question);recordText(planBody,'대상',`${config.candidate_id} · ${config.candidate_version}`);recordText(planBody,'구성',`${config.participants?.length||0}명 · 최대 ${config.max_rounds}라운드`);recordText(planBody,'환경',config.baseline);for(const actor of config.participants||[]){const entry=node('details',undefined,'record-entry');entry.append(node('summary',actor.role||actor.id));recordText(entry,'목표',actor.goals);recordText(entry,'제약',actor.constraints);recordText(entry,'자원',actor.resources);recordText(entry,'구성 근거',actor.basis);planBody.append(entry);}}
  $('start-simulation').hidden=!plan;
  const body=$('simulations');body.replaceChildren();
  const statuses={running:'실행 중',completed:'라운드 종료',stopped:'중단됨',failed:'실행 오류'};
  for(const run of runs){const entry=node('div',undefined,'record-entry');entry.append(node('p',`${run.candidate_id} · ${run.candidate_version}`,'record-title'));recordText(entry,'진행',`${statuses[run.status]||run.status} · ${run.completed_rounds||0}라운드 완료`);recordText(entry,'가상 반응',`접촉 ${run.exposed_participants||0}명 중 현재 채택 ${run.current_adopters||0}명 · 거절 ${run.current_rejecters||0}명`);recordText(entry,'기록',run.run_id);body.append(entry);}
}
function renderSubmission(data) {
  const spec=data.submission_spec,manifest=data.submission;
  $('submission-section').hidden=!spec&&!manifest;
  const body=$('submission');body.replaceChildren();
  if(spec){recordText(body,'준비할 결과물',spec.value.title||spec.value.project||spec.value.deliverables||spec.value.outputs);recordText(body,'파일 형식',spec.value.formats?.map(item=>item.filename||item.format));}
  if(manifest){recordText(body,'대상 버전',manifest.version||manifest.artifact_version||manifest.candidate_version||manifest.accepted?.artifact_version);recordText(body,'생성 상태',({complete:'생성 완료',completed:'생성 완료',prepared:'준비됨',draft:'초안',failed:'오류 확인 필요',ready_for_local_review:'파일 생성됨 · 최종 확인 필요',not_ready:'미충족 사항 확인 필요'})[manifest.status]||manifest.status);recordText(body,'미충족 사항',manifest.blockers?.length?manifest.blockers:null);for(const file of manifest.outputs||[]){if(file.filename){const link=node('a',file.filename,'file');link.href=`/api/projects/${data.id}/file?path=${encodeURIComponent('submission/'+file.filename)}`;link.download='';body.append(link);}}if(manifest.checks?.visual_render_review==='not_performed')body.append(node('p','파일 화면의 최종 시각 검토는 아직 수행하지 않았습니다.','status-note'));}
  $('finalize-project').hidden=!spec;
  $('finalize-project').dataset.unavailable=String(data.progress?.status!=='ready_for_user_review');
  if(spec&&data.progress?.status!=='ready_for_user_review')body.append(node('p','필수 검증 조건을 충족한 뒤 생성할 수 있습니다.','status-note'));
}
async function workflowAction(endpoint,field) {
  if(busy||!selected||current?.status==='running')return;
  const id=selected,payload=field?{hash:current?.[field]?.hash}:{};
  if(field&&!payload.hash)return;
  busy=true;controls();notice('');
  try{await api(`/api/projects/${id}/${endpoint}`,payload);if(selected===id)await refresh();await listProjects();}
  catch(error){if(selected===id)notice(error.message);}finally{busy=false;controls();}
}
$('approve-workflow').onclick=()=>workflowAction('approve','proposal');
$('resume-workflow').onclick=()=>workflowAction('resume');
$('start-simulation').onclick=()=>workflowAction('simulate','simulation_plan');
$('finalize-project').onclick=()=>workflowAction('finalize','submission_spec');
async function refresh() {
  if(!selected)return;
  const id=selected;const data=await api(`/api/projects/${id}`);if(id!==selected)return;
  current=data;$('project-title').textContent=data.title;renderMessages(data.messages);renderDetails(data);
  $('activity-text').textContent=data.activity;$('activity').classList.toggle('running',data.status==='running');controls();
}
function showDialog(){$('project-dialog').showModal();$('project-name').focus();}
$('new-project').onclick=showDialog;$('welcome-start').onclick=showDialog;
$('close-dialog').onclick=()=>$('project-dialog').close();
$('project-form').onsubmit=async(event)=>{event.preventDefault();const button=event.submitter;button.disabled=true;try{const project=await api('/api/projects',{title:$('project-name').value});$('project-dialog').close();$('project-name').value='';await select(project.id);}catch(error){notice(error.message);}finally{button.disabled=false;}};
$('refresh-connection').onclick=connection;
$('message').oninput=controls;
$('message').onkeydown=(event)=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();if(!$('send').disabled)$('message-form').requestSubmit();}};
async function stopAndWait(id) {
  await api(`/api/projects/${id}/stop`,{});
  for(let i=0;i<20;i++){await new Promise(resolve=>setTimeout(resolve,350));const data=await api(`/api/projects/${id}`);if(id===selected)await refresh();if(data.status!=='running')return;}
  throw new Error('중단을 기다리고 있습니다. 잠시 후 다시 보내 주세요.');
}
$('message-form').onsubmit=async(event)=>{event.preventDefault();if(busy||!selected||!$('message').value.trim())return;busy=true;controls();notice('');const content=$('message').value,id=selected;
  try{if(current?.status==='running')await stopAndWait(id);await api(`/api/projects/${id}/message`,{text:content});drafts.delete(id);if(selected===id&&$('message').value===content)$('message').value='';await refresh();await listProjects();}
  catch(error){notice(error.message);}finally{busy=false;controls();}};
$('stop').onclick=async()=>{const id=selected;busy=true;controls();try{await stopAndWait(id);}catch(error){notice(error.message);}finally{busy=false;controls();}};
$('attach').onclick=()=>$('file-input').click();
$('file-input').onchange=async(event)=>{const file=event.target.files[0],id=selected;if(!file||!id)return;if(file.size>10*1024*1024){notice('파일은 10MB 이하로 첨부해 주세요.');return;}busy=true;controls();$('upload-status').textContent='첨부 중';
  try{const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});await api(`/api/projects/${id}/upload`,{name:file.name,data});await refresh();notice('');}
  catch(error){notice(error.message||'파일을 첨부하지 못했습니다.');}finally{busy=false;event.target.value='';$('upload-status').textContent='';controls();}};
async function boot(){await connection();try{const projects=await listProjects();if(selected&&projects.some(p=>p.id===selected))await select(selected);else{selected=null;localStorage.removeItem('contest-project');}}catch(error){notice(error.message);}}
setInterval(async()=>{if(polling||document.hidden)return;polling=true;try{await refresh();await listProjects();}catch(error){notice('진행 상황을 갱신하지 못했습니다. '+error.message);}finally{polling=false;}},2000);
boot();
