document.addEventListener('DOMContentLoaded', () => {
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
