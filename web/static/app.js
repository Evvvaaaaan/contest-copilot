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
  const encoded=JSON.stringify([data.phase,data.summary,data.next_action,data.preview_url,data.status,data.progress,data.progress_error,data.files]);
  if(encoded===previousDetails)return;previousDetails=encoded;
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
      const reasons={no_result:'아직 검증하지 않았습니다.',contract_changed:'목표 조건이 바뀌어 재검증이 필요합니다.',artifact_changed_or_missing:'대상 파일이 바뀌거나 없어졌습니다.',evidence_changed_or_missing:'근거 파일이 바뀌거나 없어졌습니다.'};
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
}
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
