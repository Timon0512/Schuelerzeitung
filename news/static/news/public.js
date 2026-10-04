// Keep configurable publication names on one line within the masthead.
(() => {
  const wordmark = document.querySelector('.wordmark');
  const name = wordmark?.querySelector('a');
  if (!name) return;
  function fitName() {
    name.style.removeProperty('font-size');
    let size = parseFloat(getComputedStyle(name).fontSize);
    let width = name.getBoundingClientRect().width;
    const available = wordmark.clientWidth;
    // Variable fonts can change their optical metrics as their size changes.
    for (let pass = 0; pass < 4 && width > available && available > 0; pass++) {
      size *= (available - 1) / width;
      name.style.fontSize = `${size}px`;
      width = name.getBoundingClientRect().width;
    }
  }
  fitName();
  if ('ResizeObserver' in window) {
    new ResizeObserver(fitName).observe(wordmark);
  } else {
    window.addEventListener('resize', fitName);
  }
  document.fonts?.ready.then(fitName);
})();

// Reading and navigation work without JS; this adds a mobile focus-managed menu.
(() => {
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#main-nav');
  const close = nav?.querySelector('.menu-close');
  if (!toggle || !nav || !close) return;
  document.documentElement.classList.add('js-nav');
  toggle.hidden = false;
  const mobile = matchMedia('(max-width: 1023px)');
  const background = [document.querySelector('.masthead'), document.querySelector('main'), document.querySelector('footer')];
  function setOpen(open, restore = true) {
    nav.classList.toggle('is-open', open);
    document.body.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    close.hidden = !open;
    background.forEach(element => { if (element) element.inert = open; });
    if (open) close.focus();
    else if (restore && mobile.matches) toggle.focus();
  }
  toggle.addEventListener('click', () => setOpen(true));
  close.addEventListener('click', () => setOpen(false));
  nav.addEventListener('keydown', event => {
    if (!nav.classList.contains('is-open')) return;
    if (event.key === 'Escape') { event.preventDefault(); setOpen(false); }
    if (event.key === 'Tab') {
      const elements = [...nav.querySelectorAll('a[href],button:not([hidden])')];
      const first = elements[0], last = elements.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  mobile.addEventListener('change', () => setOpen(false, false));
})();
