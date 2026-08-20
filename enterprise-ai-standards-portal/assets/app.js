(() => {
  const portalPath = '/enterprise-ai-standards-portal/';
  const returnPageKey = 'enterprise-ai-standards-portal-return-page';
  let returnPage = `${window.location.origin}/`;
  try {
    if (document.referrer) {
      const referrer = new URL(document.referrer);
      if (referrer.origin === window.location.origin && !referrer.pathname.startsWith(portalPath)) {
        sessionStorage.setItem(returnPageKey, referrer.href);
      }
    }
    returnPage = sessionStorage.getItem(returnPageKey) || returnPage;
  } catch (_) {
    // Use the site root when referrer or session storage is unavailable.
  }
  document.getElementById('originalSite').addEventListener('click', () => {
    window.location.assign(returnPage);
  });

  const artifacts = window.AI_ARTIFACTS || [];
  const evidenceAssets = window.AI_EVIDENCE_ASSETS || [];
  const policyAssets = window.AI_POLICY_ASSETS || [];

  const views = [...document.querySelectorAll('.view')];
  const navBtns = [...document.querySelectorAll('.nav-btn[data-view]')];
  const go = (id) => {
    views.forEach(v => v.classList.toggle('active', v.id === id));
    navBtns.forEach(b => b.classList.toggle('active', b.dataset.view === id));
    window.scrollTo({top:0,behavior:'smooth'});
  };
  navBtns.forEach(b => b.addEventListener('click', () => go(b.dataset.view)));
  document.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click', () => go(b.dataset.go)));

  const controlArtifacts = artifacts.filter(a => a.type === 'Standard');
  const mustCount = controlArtifacts.filter(a => a.requirement === 'MUST').length;
  const domains = [...new Set(controlArtifacts.map(a => a.domain))];
  const phases = [...new Set(controlArtifacts.flatMap(a => a.phases))];
  document.getElementById('metrics').innerHTML = [
    [controlArtifacts.length,'Normative controls'],
    [mustCount,'Mandatory production controls'],
    [domains.length,'Control domains'],
    [phases.length,'Lifecycle stages']
  ].map(([v,l]) => `<div class="metric"><div class="value">${v}</div><div class="label">${l}</div></div>`).join('');

  // Filters
  const searchBox = document.getElementById('searchBox');
  const domainFilter = document.getElementById('domainFilter');
  const phaseFilter = document.getElementById('phaseFilter');
  const requirementFilter = document.getElementById('requirementFilter');
  const riskFilter = document.getElementById('riskFilter');
  domains.sort().forEach(d => domainFilter.insertAdjacentHTML('beforeend', `<option>${d}</option>`));
  phases.sort().forEach(p => phaseFilter.insertAdjacentHTML('beforeend', `<option>${p}</option>`));
  [...new Set(controlArtifacts.map(a=>a.requirement))].sort().forEach(r => requirementFilter.insertAdjacentHTML('beforeend', `<option>${r}</option>`));

  const artifactGrid = document.getElementById('artifactGrid');
  const catalogSummary = document.getElementById('catalogSummary');
  const dialog = document.getElementById('artifactDialog');
  const dialogContent = document.getElementById('dialogContent');
  document.getElementById('dialogClose').addEventListener('click',()=>dialog.close());

  const escapeHtml = (s='') => s.replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

  function renderCatalog(){
    const q = searchBox.value.trim().toLowerCase();
    const d = domainFilter.value, p = phaseFilter.value, req = requirementFilter.value, risk = riskFilter.value;
    const filtered = controlArtifacts.filter(a => {
      const hay = [a.id,a.title,a.summary,a.domain,a.framework.join(' '),a.tags.join(' '),a.evidence.join(' ')].join(' ').toLowerCase();
      return (!q || hay.includes(q)) && (d==='all'||a.domain===d) && (p==='all'||a.phases.includes(p)) && (req==='all'||a.requirement===req) && (risk==='all'||a.riskTiers.includes(risk));
    });
    catalogSummary.textContent = `${filtered.length} standards shown · ${filtered.filter(a=>a.requirement==='MUST').length} mandatory`;
    artifactGrid.innerHTML = filtered.map(a => `
      <article class="artifact-card">
        <div class="artifact-top"><span class="control-id">${escapeHtml(a.id)}</span><span class="req ${a.requirement.toLowerCase()}">${a.requirement}</span></div>
        <h3>${escapeHtml(a.title)}</h3>
        <p>${escapeHtml(a.summary)}</p>
        <div class="tags">${a.framework.slice(0,3).map(t=>`<span class="tag">${escapeHtml(t)}</span>`).join('')}</div>
        <div class="artifact-actions"><button data-id="${a.id}">View control</button><a href="preview.html?file=${encodeURIComponent(a.artifactPath)}" target="_blank" rel="noopener noreferrer">Preview MD</a></div>
      </article>`).join('');
    artifactGrid.querySelectorAll('button[data-id]').forEach(btn=>btn.addEventListener('click',()=>openArtifact(btn.dataset.id)));
  }
  [searchBox,domainFilter,phaseFilter,requirementFilter,riskFilter].forEach(el=>el.addEventListener('input',renderCatalog));

  function openArtifact(id){
    const a = artifacts.find(x=>x.id===id); if(!a)return;
    dialogContent.innerHTML = `<div class="dialog-body">
      <div class="eyebrow">${escapeHtml(a.domain.toUpperCase())} · ${escapeHtml(a.id)}</div>
      <h2>${escapeHtml(a.title)}</h2>
      <p>${escapeHtml(a.summary)}</p>
      <div class="dialog-meta"><span class="req ${a.requirement.toLowerCase()}">${a.requirement}</span>${a.riskTiers.map(t=>`<span class="tag">${t}</span>`).join('')}${a.phases.map(t=>`<span class="tag">${escapeHtml(t)}</span>`).join('')}</div>
      <div class="dialog-section"><h3>Required controls</h3><ul>${a.checks.map(c=>`<li>${escapeHtml(c)}</li>`).join('')}</ul></div>
      <div class="dialog-section"><h3>Evidence expected</h3><ul>${a.evidence.map(c=>`<li>${escapeHtml(c)}</li>`).join('')}</ul></div>
      <div class="dialog-section"><h3>Framework mapping</h3><div class="tags">${a.framework.map(t=>`<span class="tag">${escapeHtml(t)}</span>`).join('')}</div></div>
      <div class="dialog-section"><a class="download-btn" href="preview.html?file=${encodeURIComponent(a.artifactPath)}" target="_blank" rel="noopener noreferrer">Preview standard</a></div>
    </div>`;
    dialog.showModal();
  }
  renderCatalog();

  // Evidence downloads
  document.getElementById('evidenceDownloads').innerHTML = evidenceAssets.map(a => {
    const href = `preview.html?file=${encodeURIComponent(a.path)}`;
    return `<div class="download-row"><div><b>${escapeHtml(a.title)}</b><small>${escapeHtml(a.description)}</small></div><a href="${href}" target="_blank" rel="noopener noreferrer">Preview</a></div>`;
  }).join('');
  document.getElementById('policyDownloads').innerHTML = policyAssets.map(a=>`<a href="preview.html?file=${encodeURIComponent(a.path)}" target="_blank" rel="noopener noreferrer">${escapeHtml(a.title)}</a>`).join('');

  // Checkpoint console
  const assessmentRisk = document.getElementById('assessmentRisk');
  const stages = ['Architecture','Implementation','Build & Evaluation','Deployment','Runtime'];
  const storageKey = 'enterprise-ai-standards-assessment-v1';
  let state = JSON.parse(localStorage.getItem(storageKey) || '{}');
  const stageContainer = document.getElementById('checkpointStages');
  const relevantArtifacts = () => controlArtifacts.filter(a=>a.riskTiers.includes(assessmentRisk.value));

  function renderAssessment(){
    const rel = relevantArtifacts();
    stageContainer.innerHTML = stages.map(stage => {
      const items = rel.filter(a=>a.phases.includes(stage));
      return `<section class="checkpoint-stage"><header><div><h3>${stage}</h3><small>${items.length} applicable controls for ${assessmentRisk.value}</small></div></header>${items.map(a=>`<label class="checkpoint-item"><input type="checkbox" data-control="${a.id}" ${state[a.id]?'checked':''}/><div><b>${a.id} — ${escapeHtml(a.title)}</b><p>${escapeHtml(a.summary)}</p></div><span class="status-pill ${a.requirement==='MUST'?'blocker':''}">${a.requirement}${a.requirement==='MUST'?' · blocker':''}</span></label>`).join('')}</section>`;
    }).join('');
    stageContainer.querySelectorAll('input[data-control]').forEach(cb=>cb.addEventListener('change',()=>{state[cb.dataset.control]=cb.checked;localStorage.setItem(storageKey,JSON.stringify(state));updateScore();}));
    updateScore();
  }

  function updateScore(){
    const rel = relevantArtifacts();
    const mandatory = rel.filter(a=>a.requirement==='MUST');
    const checkedAll = rel.filter(a=>state[a.id]).length;
    const checkedMust = mandatory.filter(a=>state[a.id]).length;
    const score = rel.length ? Math.round((checkedAll/rel.length)*100) : 0;
    const blockers = mandatory.length - checkedMust;
    const ring = document.getElementById('readinessRing');
    ring.style.setProperty('--score',score);
    let color = '#d73535', label='Blocked';
    if(blockers===0 && score>=90){color='#28a745';label='Ready';}
    else if(blockers===0 && score>=70){color='#e3a008';label='Conditionally ready';}
    ring.style.setProperty('--ring',color);
    document.getElementById('scoreNumber').textContent = `${score}%`;
    document.getElementById('readinessLabel').textContent = label;
    document.getElementById('readinessDetail').textContent = blockers ? `${blockers} mandatory control${blockers===1?'':'s'} not satisfied.` : 'No mandatory blockers remain.';
    document.getElementById('stageSummary').innerHTML = stages.map(stage=>{
      const items=rel.filter(a=>a.phases.includes(stage)); const done=items.filter(a=>state[a.id]).length;
      return `<div class="stage-chip"><b>${stage}</b><small>${done}/${items.length} complete</small></div>`;
    }).join('');
  }
  assessmentRisk.addEventListener('change',renderAssessment);
  document.getElementById('resetAssessment').addEventListener('click',()=>{if(confirm('Reset all checkpoint selections?')){state={};localStorage.removeItem(storageKey);renderAssessment();}});
  document.getElementById('exportAssessment').addEventListener('click',()=>{
    const rel = relevantArtifacts();
    const result={framework:'Balanced Enterprise Architecture Framework for Secure and Ethical AI Adoption',generatedAt:new Date().toISOString(),riskTier:assessmentRisk.value,controls:rel.map(a=>({id:a.id,title:a.title,requirement:a.requirement,satisfied:!!state[a.id],domain:a.domain,phases:a.phases,evidence:a.evidence}))};
    const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`ai-readiness-${assessmentRisk.value.toLowerCase()}-${new Date().toISOString().slice(0,10)}.json`;a.click();URL.revokeObjectURL(url);
  });
  renderAssessment();
})();
