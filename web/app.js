'use strict';
const $ = selector => document.querySelector(selector);
const roles = [
  ['financial_analyst', 'Financial analysis'],
  ['business_analyst', 'Industry & business analysis'],
  ['deal_structure_analyst', 'Deal structure analysis'],
  ['credit_reviewer', 'Independent credit review']
];
const statuses = {queued:'Awaiting Credit Lead',working:'In progress',research_complete:'Research complete',review_blocked:'Review blocked',answered:'Answered',failed:'Failed',invalidated:'Review invalidated'};
let jobs = [], selected = location.hash.slice(1), current = null, connected = false, refreshing = false;
let lastView = '';
function node(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (className) result.className = className;
  return result;
}
async function api(path, value) {
  const response = await fetch(path, value === undefined ? {cache:'no-store'} : {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(value)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return result;
}
function stateText(status) { return statuses[status] || status; }
function select(id) {
  selected = id || ''; current = null; lastView = '';
  location.hash = selected;
  $('#newView').hidden = Boolean(selected);
  $('#caseView').hidden = !selected;
  drawList(); refresh();
}
function drawList() {
  const container = $('#caseList'); container.replaceChildren();
  const cases = jobs.filter(j => j.kind === 'analysis');
  if (!cases.length) container.append(node('p','No cases yet. Start a request or ask the Credit Lead in this chat.','muted'));
  for (const job of cases) {
    const button = node('button',undefined,'case-button' + (selected === job.id ? ' active' : ''));
    button.append(node('strong',job.case.company),node('small',stateText(job.status)+' · '+job.mode),node('small',new Date(job.created_at).toLocaleString()));
    button.addEventListener('click',()=>select(job.id)); container.append(button);
  }
}
function addList(parent, items) {
  const list = node('ul');
  for (const item of items || []) list.append(node('li',item));
  parent.append(list);
}
function drawAgent(role, title, job) {
  const card = node('article',undefined,'card agent-card'); card.dataset.role = role;
  const header = node('header'); header.append(node('h3',title)); card.append(header);
  const orders = job.work_orders.map(o=>o.role);
  const skipped = role === 'deal_structure_analyst' && !job.case.deal_in_scope;
  const artifact = role === 'credit_reviewer' ? job.review : job.analyses[role];
  const published = Boolean(job.result);
  const label = skipped ? 'Not in scope' : artifact ? (role === 'credit_reviewer' ? (published ? artifact.status : 'Not finalized') : (published ? 'Reviewed' : 'Awaiting review')) : 'Pending';
  header.append(node('span',label,'badge'));
  if (skipped) card.append(node('p','No debt or transaction analysis requested.'));
  else if (!artifact) card.append(node('p',role==='credit_reviewer' ? 'The reviewer will independently assess the specialist outputs.' : orders.includes(role) ? 'Work order prepared. Awaiting this specialist’s output.' : 'The Credit Lead will prepare this work order when the case is claimed.','muted'));
  else if (role === 'credit_reviewer') {
    card.append(node('p',artifact.summary)); addList(card,artifact.issues);
  } else {
    const findings = node('ul');
    for (const finding of artifact.findings || []) {
      const li = node('li',finding.claim);
      for (const ref of finding.evidence_ids || []) li.append(node('span',ref,'reference'));
      findings.append(li);
    }
    card.append(findings,node('h4','Missing information'));
    if (artifact.missing_inputs?.length) addList(card,artifact.missing_inputs);
    else card.append(node('p','No additional gaps recorded by this analyst.','muted'));
  }
  return card;
}
function drawMessages(job) {
  const list = $('#chatMessages'); const nearBottom = list.scrollHeight-list.scrollTop-list.clientHeight<60;
  list.replaceChildren();
  const first = node('div',undefined,'message user');first.append(node('small','Your initial instruction'),node('span',job.message));list.append(first);
  if (job.lead) list.append(node('div',job.lead.summary,'message'));
  const thread = jobs.filter(j=>j.parent_id===job.id).sort((a,b)=>a.created_at.localeCompare(b.created_at));
  for (const item of thread) {
    const message = node('div',undefined,'message user');
    message.append(node('small',item.kind==='question'?'Question':'Follow-up assignment'),node('span',item.message));list.append(message);
    if (item.reply) list.append(node('div',item.reply,'message'));
    else if (item.kind === 'analysis') {
      const result = node('div',undefined,'message');result.append(node('span',stateText(item.status)+'. '));
      const link = node('button','Open follow-up results','secondary');link.addEventListener('click',()=>select(item.id));result.append(link);list.append(result);
    } else list.append(node('div',item.error || stateText(item.status)+'. Ask the Credit Lead in this chat to process the inbox.','message'));
  }
  if (nearBottom) list.scrollTop = list.scrollHeight;
}
function drawCase(job) {
  current = job;
  $('#caseCompany').textContent = job.case.company;
  $('#caseInstruction').textContent = job.message;
  $('#caseStatus').textContent = stateText(job.status)+' · '+job.mode;
  const notice = job.status === 'queued' ? 'Saved to the inbox. Tell the Credit Lead in this chat: “Process the Credit Pilot inbox.”' : job.status==='working' ? 'The Credit Lead has claimed this request. Each output appears as it is saved; findings are provisional until review and publication.' : job.status==='review_blocked' ? 'The independent reviewer blocked this run. See objections below; the Credit Lead cannot override them.' : job.status==='failed' ? job.error : job.status==='invalidated' ? 'Published artifacts changed after review. The verdict is no longer valid; create a new run.' : 'Reviewed research published by the Credit Lead. No credit rating has been assigned.';
  $('#caseNotice').textContent = [notice,...job.artifact_errors].join('\n');
  $('#leadSummary').textContent = job.lead?.summary || 'Awaiting the Credit Lead’s synthesis of the specialist outputs and independent review.';
  $('#openQuestions').replaceChildren();
  for (const question of job.lead?.open_questions || []) $('#openQuestions').append(node('li',question));
  $('#agentResults').replaceChildren(...roles.map(([role,title])=>drawAgent(role,title,job)));
  const evidence = $('#evidenceList');evidence.replaceChildren();
  for (const item of job.case.evidence) evidence.append(node('h4','['+item.id+'] '+item.source),node('p',item.text));
  drawMessages(job);
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    const [status, nextJobs] = await Promise.all([api('/api/status'),api('/api/jobs')]);
    if (status.mode !== 'codex_chat') throw new Error('Unsupported server mode');
    connected = true; jobs = nextJobs;
    $('#connection').textContent = 'Connected · Lead operates in chat';$('#connection').classList.remove('offline');
    drawList();
    if (selected) {
      const id = selected;
      const job = await api('/api/jobs/'+encodeURIComponent(id));
      if (id !== selected) return;
      const view = JSON.stringify([job,jobs.filter(j=>j.parent_id===id)]);
      if (view !== lastView) {drawCase(job);lastView=view;}
    }
  } catch (error) {
    connected = false;$('#connection').textContent = 'Disconnected · Start the Credit Pilot server';$('#connection').classList.add('offline');
    if (selected) $('#caseNotice').textContent='Could not refresh this case: '+error.message+'. Existing results may be stale.';
  } finally {refreshing=false;}
}
$('#newCase').addEventListener('click',()=>select(''));
window.addEventListener('hashchange',()=>{const id=location.hash.slice(1);if(id!==selected)select(id);});
$('#requestForm').addEventListener('submit',async event=>{
  event.preventDefault();$('#requestError').textContent='';const button=$('#submitRequest');button.disabled=true;
  try {
    if (!connected) throw new Error('The server is disconnected. Start it before submitting.');
    const job = await api('/api/jobs',{kind:'analysis',mode:$('#depth').value,message:$('#request').value.trim(),case:{company:$('#company').value.trim(),scope:'Corporate credit research',deal_in_scope:$('#deal').checked,evidence:[{id:'E1',source:'User-supplied source material; source details in text',text:$('#evidence').value.trim()}]}});
    jobs.unshift(job);$('#requestForm').reset();select(job.id);
  } catch(error) {$('#requestError').textContent=error.message;}
  finally {button.disabled=false;}
});
$('#caseChat').addEventListener('submit',async event=>{
  event.preventDefault();$('#chatError').textContent='';const button=$('#sendMessage');button.disabled=true;
  try {
    if (!connected || !current) throw new Error('Reconnect to the server before sending.');
    const parent = current.id;
    const job = await api('/api/jobs',{kind:$('#messageKind').value,parent_id:parent,mode:current.mode,message:$('#caseQuestion').value.trim()});
    jobs.unshift(job);$('#caseQuestion').value='';lastView='';await refresh();
  } catch(error) {$('#chatError').textContent=error.message;}
  finally {button.disabled=false;}
});
$('#newView').hidden=Boolean(selected);$('#caseView').hidden=!selected;
refresh();setInterval(refresh,2500);
