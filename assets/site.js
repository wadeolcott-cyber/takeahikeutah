const currentPage = location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('nav a').forEach(link => {
  if (link.getAttribute('href') === currentPage) link.setAttribute('aria-current', 'page');
});
const checks = [...document.querySelectorAll('.checklist input')];
checks.forEach(check => check.addEventListener('change', () => {
  const count = checks.filter(item => item.checked).length;
  document.querySelector('#check-status').textContent = `${count} of ${checks.length} ready${count === checks.length ? ' — enjoy your outing, and keep checking conditions.' : ''}`;
}));
