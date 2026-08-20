(() => {
  'use strict';
  const preview = document.getElementById('markdownPreview');
  const download = document.getElementById('downloadSource');
  const back = document.getElementById('backToSource');
  const file = new URLSearchParams(window.location.search).get('file') || '';
  const allowed = /^(README|REFERENCES)\.md$/.test(file) || (/^docs\/[A-Z0-9_-]+\.md$/.test(file) && !file.includes('..'));
  const escapeHtml = (value='') => value.replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const inline = value => escapeHtml(value).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');

  let fallback = 'index.html';
  if (document.referrer) {
    try { const referrer = new URL(document.referrer); if (referrer.origin === window.location.origin) fallback = referrer.href; } catch (_) {}
  }
  back.href = fallback;
  back.addEventListener('click', event => { event.preventDefault(); window.close(); window.setTimeout(() => window.location.assign(fallback),100); });

  function render(source) {
    const output=[]; let list=''; let inCode=false; let code=[];
    const closeList=()=>{if(list)output.push(`</${list}>`);list='';};
    for(const line of source.replace(/\r\n?/g,'\n').split('\n')) {
      if(line.startsWith('```')) { closeList(); if(inCode){output.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);code=[];} inCode=!inCode; continue; }
      if(inCode){code.push(line);continue;}
      const heading=line.match(/^(#{1,3})\s+(.+)$/);
      if(heading){closeList();const level=heading[1].length;output.push(`<h${level}>${inline(heading[2])}</h${level}>`);continue;}
      const unordered=line.match(/^[-*]\s+(.+)$/); const ordered=line.match(/^\d+\.\s+(.+)$/);
      if(unordered||ordered){const next=unordered?'ul':'ol';if(list!==next){closeList();list=next;output.push(`<${list}>`);}output.push(`<li>${inline((unordered||ordered)[1])}</li>`);continue;}
      closeList(); if(line.trim())output.push(`<p>${inline(line.trim())}</p>`);
    }
    closeList(); if(inCode)output.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`); return output.join('\n');
  }

  if(!allowed){preview.innerHTML='<p class="preview-error"><strong>Preview unavailable.</strong> The requested Markdown path is not allowed.</p>';download.hidden=true;return;}
  download.href=file;download.download=file.split('/').pop();
  fetch(file).then(response=>{if(!response.ok)throw new Error();return response.text();}).then(source=>{const title=source.match(/^#\s+(.+)$/m)?.[1];if(title)document.title=`${title} · Active Inference Recommender Research`;preview.innerHTML=render(source);}).catch(()=>{preview.innerHTML='<p class="preview-error"><strong>Preview unavailable.</strong> The Markdown file could not be loaded.</p>';});
})();
