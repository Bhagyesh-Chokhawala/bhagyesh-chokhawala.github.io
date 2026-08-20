document.addEventListener('DOMContentLoaded', () => {
  const portalPath = '/api-policy-portal/';
  const returnPageKey = 'api-policy-portal-return-page';
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
  document.querySelectorAll('.original-site-link').forEach(link => {
    link.href = returnPage;
    link.removeAttribute('target');
    link.removeAttribute('rel');
  });

  const search = document.querySelector('#report-search');
  const status = document.querySelector('#status-filter');
  const rows = [...document.querySelectorAll('#report-table tbody tr')];
  const apply = () => {
    const q = (search?.value || '').toLowerCase().trim();
    const s = status?.value || '';
    rows.forEach(row => {
      const matchesText = !q || (row.dataset.search || '').toLowerCase().includes(q);
      const matchesStatus = !s || row.dataset.status === s;
      row.hidden = !(matchesText && matchesStatus);
    });
  };
  search?.addEventListener('input', apply);
  status?.addEventListener('change', apply);
  document.querySelector('.nav-toggle')?.addEventListener('click', () => {
    const nav = document.querySelector('.nav');
    if (nav) nav.style.display = nav.style.display === 'flex' ? 'none' : 'flex';
  });
});
