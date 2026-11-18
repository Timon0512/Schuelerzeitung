(() => {
  const menu = document.getElementById('editorial-menu');
  const navigation = document.getElementById('editorial-nav');
  if (menu && navigation) {
    const mobile = window.matchMedia('(max-width: 860px)');
    const setMenu = open => {
      menu.hidden = !mobile.matches;
      menu.setAttribute('aria-expanded', String(open));
      navigation.hidden = mobile.matches && !open;
    };
    setMenu(false);
    mobile.addEventListener('change', () => setMenu(false));
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      setMenu(open);
      if (open) navigation.querySelector('[aria-current]')?.focus();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        menu.focus();
      }
    });
  }

  const filters = document.querySelectorAll('.editorial-filters details');
  const closeFilters = except => filters.forEach(filter => { if (filter !== except) filter.open = false; });
  filters.forEach(filter => {
    filter.open = false;
    const summary = filter.querySelector('summary');
    const selected = filter.querySelector('li.selected:not(:first-child)');
    const name = filter.dataset.filterTitle;
    summary.textContent = name.charAt(0).toLocaleUpperCase('de') + name.slice(1);
    if (selected) {
      summary.textContent += ': ' + selected.textContent.trim();
      filter.classList.add('has-selection');
    }
    filter.addEventListener('toggle', () => { if (filter.open) closeFilters(filter); });
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.editorial-filters')) closeFilters();
  });

  const authors = document.getElementById('id_authors');
  if (authors) {
    const options = [...authors.querySelectorAll('label')];
    if (options.length) {
      const search = document.createElement('input');
      search.type = 'search';
      search.placeholder = 'Namen suchen';
      search.setAttribute('aria-label', 'Autorendarstellungen suchen');
      const status = document.createElement('span');
      status.className = 'author-search-status';
      status.setAttribute('role', 'status');
      authors.before(search);
      authors.after(status);
      search.addEventListener('input', () => {
        const query = search.value.trim().toLocaleLowerCase('de');
        let matches = 0;
        options.forEach(option => {
          const visible = option.textContent.toLocaleLowerCase('de').includes(query);
          if (visible) matches++;
          option.parentElement.hidden = !visible && !option.querySelector('input').checked;
        });
        status.textContent = query && !matches ? 'Keine passenden Namen.' : '';
      });
    }
  }

  const article = document.getElementById('article_form');
  const dirtyMessage = article?.querySelector('.editorial-dirty');
  let dirty = false;
  const unload = event => {
    event.preventDefault();
    event.returnValue = '';
  };
  const setDirty = state => {
    if (state === dirty) return;
    dirty = state;
    if (dirtyMessage) dirtyMessage.textContent = state ? 'Ungespeicherte Änderungen' : '';
    if (state) window.addEventListener('beforeunload', unload);
    else window.removeEventListener('beforeunload', unload);
  };
  if (dirtyMessage) {
    const markDirty = event => {
      if (event.target.name) setDirty(true);
    };
    article.addEventListener('input', markDirty);
    article.addEventListener('change', markDirty);
    const invalid = article.querySelector('.errorlist');
    if (invalid) {
      setDirty(true);
      const collapsed = invalid.closest('details');
      if (collapsed) collapsed.open = true;
    }
  }
  document.querySelectorAll('form:has(.editorial-actions)').forEach(form => {
    form.addEventListener('submit', event => {
      const button = event.submitter;
      let message = button?.dataset.confirm;
      if (button?.hasAttribute('data-separate-action') && dirty) {
        message += ' Ungespeicherte Änderungen im Artikel werden verworfen.';
      }
      if (message && !window.confirm(message)) {
        event.preventDefault();
      } else if (form === article && button?.formTarget !== '_blank') {
        setDirty(false);
      }
    });
  });
})();
