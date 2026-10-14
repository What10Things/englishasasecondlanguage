(() => {
  const dialog = document.querySelector('#language-dialog');
  const banner = document.querySelector('[data-privacy-banner]');
  const saved = document.cookie.split('; ').find(value => value.startsWith('efl_cookie_consent='));
  let choice = saved ? saved.split('=')[1] : '';
  let opener;
  const showPrivacy = () => {
    if (banner) banner.hidden = ['essential', 'optional'].includes(choice) || !!dialog?.open;
  };
  document.querySelectorAll('[data-privacy-choice]').forEach(button => {
    button.addEventListener('click', () => {
      choice = button.dataset.privacyChoice;
      document.cookie = 'efl_cookie_consent=' + choice + '; Max-Age=31536000; Path=/; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '');
      showPrivacy();
    });
  });
  document.querySelectorAll('[data-privacy-open]').forEach(button => {
    button.addEventListener('click', () => { if (banner) { banner.hidden = false; banner.querySelector('button').focus(); } });
  });
  if (dialog && typeof dialog.showModal === 'function') {
    document.querySelectorAll('[data-language-open]').forEach(link => {
      link.addEventListener('click', event => { event.preventDefault(); opener = link; dialog.showModal(); showPrivacy(); });
    });
    dialog.querySelector('[data-language-close]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => { if (opener) opener.focus(); showPrivacy(); });
    if (dialog.dataset.firstVisit === 'true') dialog.showModal();
  }
  showPrivacy();
})();
