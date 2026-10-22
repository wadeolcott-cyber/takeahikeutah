const currentPage = location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('nav a').forEach(link => {
  if (link.getAttribute('href') === currentPage) link.setAttribute('aria-current', 'page');
});
const checks = [...document.querySelectorAll('.checklist input')];
checks.forEach(check => check.addEventListener('change', () => {
  const count = checks.filter(item => item.checked).length;
  document.querySelector('#check-status').textContent = `${count} of ${checks.length} ready${count === checks.length ? ' — enjoy your outing, and keep checking conditions.' : ''}`;
}));

// Filter pre-rendered HTML. The full collection remains usable without JavaScript.
const filterForm = document.querySelector('#hike-filters');
if (filterForm) {
  const fields = [...filterForm.querySelectorAll('select')];
  const cards = [...document.querySelectorAll('#hike-results .hike-card')];
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#no-results');
  function applyFilters(updateURL = true) {
    const selected = Object.fromEntries(fields.map(field => [field.name, field.value]));
    let visible = 0;
    cards.forEach(card => {
      const tagsMatch = ['experience', 'landscape', 'season', 'terrain'].every(key =>
        !selected[key] || card.dataset[key].split(' ').includes(selected[key]));
      const distance = Number(card.dataset.distance);
      const elevation = Number(card.dataset.elevation);
      const distanceMatch = !selected.distance || (card.dataset.distance !== '' && (
        selected.distance === 'short' ? distance <= 3 : selected.distance === 'medium' ? distance > 3 && distance <= 8 : distance > 8));
      const elevationMatch = !selected.elevation || (card.dataset.elevation !== '' && (
        selected.elevation === 'low' ? elevation <= 500 : selected.elevation === 'moderate' ? elevation > 500 && elevation <= 1500 : elevation > 1500));
      card.hidden = !(tagsMatch && distanceMatch && elevationMatch);
      if (!card.hidden) visible++;
    });
    document.querySelectorAll('.result-group').forEach(group => {
      group.hidden = ![...group.querySelectorAll('.hike-card')].some(card => !card.hidden);
    });
    count.textContent = `${visible} of ${cards.length} entries shown`;
    empty.hidden = visible !== 0;
    if (updateURL) {
      const url = new URL(location.href);
      fields.forEach(field => {
        if (field.value) url.searchParams.set(field.name, field.value);
        else url.searchParams.delete(field.name);
      });
      history.replaceState(null, '', url);
    }
  }
  function readURL() {
    const params = new URLSearchParams(location.search);
    fields.forEach(field => {
      const requested = params.get(field.name) || '';
      field.value = [...field.options].some(option => option.value === requested) ? requested : '';
    });
    applyFilters(false);
  }
  filterForm.hidden = false;
  readURL();
  filterForm.addEventListener('change', () => applyFilters());
  filterForm.addEventListener('submit', event => event.preventDefault());
  filterForm.addEventListener('reset', () => {
    // Wait for the native reset to complete before updating results.
    setTimeout(() => applyFilters(), 0);
  });
  window.addEventListener('popstate', readURL);
}
