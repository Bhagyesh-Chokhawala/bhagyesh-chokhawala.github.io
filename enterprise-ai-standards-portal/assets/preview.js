(() => {
  'use strict';

  const preview = document.getElementById('markdownPreview');
  const download = document.getElementById('downloadSource');
  const previewType = document.getElementById('previewType');
  const backToSource = document.getElementById('backToSource');
  const file = new URLSearchParams(window.location.search).get('file') || '';
  const extension = file.split('.').pop().toLowerCase();
  const allowedExtension = ['md', 'yaml', 'json'].includes(extension);
  const artifactPath = /^artifacts\/[a-z0-9-]+\/[A-Za-z0-9._-]+\.(md|yaml|json)$/.test(file);
  const schemaPath = /^schemas\/[A-Za-z0-9._-]+\.json$/.test(file);
  const allowed = file === 'README.md' || (allowedExtension && (artifactPath || schemaPath) && !file.includes('..'));

  let fallbackUrl = 'index.html';
  if (document.referrer) {
    try {
      const referrer = new URL(document.referrer);
      if (referrer.origin === window.location.origin) fallbackUrl = referrer.href;
    } catch (_) { /* Use the portal fallback. */ }
  }
  backToSource.href = fallbackUrl;
  backToSource.addEventListener('click', event => {
    event.preventDefault();
    window.close();
    window.setTimeout(() => window.location.assign(fallbackUrl), 100);
  });

  const escapeHtml = (value = '') => value.replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));

  const inline = (value) => escapeHtml(value)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  function renderMarkdown(source) {
    const lines = source.replace(/\r\n?/g, '\n').split('\n');
    const output = [];
    let list = '';
    let inCode = false;
    let code = [];

    const closeList = () => {
      if (list) output.push(`</${list}>`);
      list = '';
    };

    for (const line of lines) {
      if (line.startsWith('```')) {
        closeList();
        if (inCode) {
          output.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
          code = [];
        }
        inCode = !inCode;
        continue;
      }
      if (inCode) { code.push(line); continue; }

      const heading = line.match(/^(#{1,3})\s+(.+)$/);
      if (heading) {
        closeList();
        const level = heading[1].length;
        output.push(`<h${level}>${inline(heading[2])}</h${level}>`);
        continue;
      }

      const unordered = line.match(/^[-*]\s+(.+)$/);
      const ordered = line.match(/^\d+\.\s+(.+)$/);
      if (unordered || ordered) {
        const nextList = unordered ? 'ul' : 'ol';
        if (list !== nextList) { closeList(); list = nextList; output.push(`<${list}>`); }
        let item = (unordered || ordered)[1];
        const task = item.match(/^\[([ xX])\]\s+(.+)$/);
        if (task) item = `<input type="checkbox" disabled${task[1].toLowerCase() === 'x' ? ' checked' : ''}>${inline(task[2])}`;
        else item = inline(item);
        output.push(`<li>${item}</li>`);
        continue;
      }

      closeList();
      if (line.trim()) output.push(`<p>${inline(line.trim())}</p>`);
    }
    closeList();
    if (inCode) output.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
    return output.join('\n');
  }

  if (!allowed) {
    preview.innerHTML = '<p class="preview-error"><strong>Preview unavailable.</strong> The requested Markdown path is not allowed.</p>';
    download.hidden = true;
    return;
  }

  download.href = file;
  download.download = file.split('/').pop();
  download.textContent = `Download ${extension.toUpperCase()}`;
  previewType.textContent = `${extension.toUpperCase()} PREVIEW`;
  fetch(file)
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.text();
    })
    .then(source => {
      const title = extension === 'md' ? source.match(/^#\s+(.+)$/m)?.[1] : file.split('/').pop();
      if (title) document.title = `${title} · Enterprise AI Standards Portal`;
      if (extension === 'md') {
        preview.innerHTML = renderMarkdown(source);
      } else {
        let code = source;
        if (extension === 'json') {
          try { code = JSON.stringify(JSON.parse(source), null, 2); } catch (_) { /* Show the original source. */ }
        }
        preview.innerHTML = `<pre class="artifact-code"><code>${escapeHtml(code)}</code></pre>`;
      }
    })
    .catch(() => {
      preview.innerHTML = '<p class="preview-error"><strong>Preview unavailable.</strong> The Markdown file could not be loaded.</p>';
    });
})();
