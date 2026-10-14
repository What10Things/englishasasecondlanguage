(() => {
  const dialog = document.querySelector('#language-dialog');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  let opener;
  document.querySelectorAll('[data-language-open]').forEach(link => {
    link.addEventListener('click', event => { event.preventDefault(); opener = link; dialog.showModal(); });
  });
  dialog.querySelector('[data-language-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { if (opener) opener.focus(); });
  if (dialog.dataset.firstVisit === 'true') dialog.showModal();
})();
