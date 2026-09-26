(() => {
  function init() {
    const select = document.getElementById('id_hero_image');
    const x = document.getElementById('id_hero_focus_x');
    const y = document.getElementById('id_hero_focus_y');
    const selectedImage = document.getElementById('id_hero_focus_image');
    if (!select || !x || !y || !selectedImage) return;
    const panel = document.createElement('section');
    panel.className = 'image-focus';
    panel.setAttribute('aria-label', 'Bildausschnitt festlegen');
    panel.innerHTML = `<h2>Bildausschnitt festlegen</h2>
      <p id="focus-help">Den wichtigen Bildbereich antippen oder den Fokuspunkt ziehen. Alternativ die Prozentfelder verwenden.</p>
      <p class="focus-status" role="status"></p>
      <div class="focus-content" hidden>
        <div class="focus-source"><img alt="Titelbild zum Festlegen des Bildfokus" draggable="false">
          <button type="button" class="focus-point" aria-label="Bildfokus verschieben" aria-describedby="focus-keys"></button>
        </div>
        <p id="focus-keys">Fokuspunkt: mit den Pfeiltasten bewegen, mit Umschalt in größeren Schritten.</p>
        <button type="button" class="focus-reset">Bildmitte verwenden</button>
        <div class="focus-previews"></div>
      </div>`;
    const row = y.closest('.form-row') || y.parentElement;
    row.after(panel);
    const content = panel.querySelector('.focus-content');
    const source = panel.querySelector('.focus-source');
    const image = source.querySelector('img');
    const point = panel.querySelector('.focus-point');
    const status = panel.querySelector('.focus-status');
    const previews = panel.querySelector('.focus-previews');
    const layouts = [
      ['Aufmacher · Desktop', 2], ['Aufmacher · Mobil', 2],
      ['Artikelkachel · Desktop', 2.4], ['Kompakte Kachel · Desktop', 1.5],
      ['Kompakte Kachel · Mobil', 1.4], ['Artikelseite · Desktop', null],
      ['Artikelseite · Mobil', null],
    ];
    const samples = layouts.map(([label, ratio]) => {
      const figure = document.createElement('figure');
      const img = document.createElement('img');
      img.alt = '';
      if (ratio) img.style.aspectRatio = ratio;
      const caption = document.createElement('figcaption');
      caption.textContent = label;
      figure.append(img, caption);
      previews.append(figure);
      return img;
    });
    const number = field => Math.max(0, Math.min(100, Number(field.value) || 0));
    function draw() {
      const left = number(x), top = number(y);
      point.style.left = `${left}%`;
      point.style.top = `${top}%`;
      point.setAttribute('aria-label', `Bildfokus verschieben: horizontal ${left} Prozent, vertikal ${top} Prozent`);
      samples.forEach(img => { img.style.objectPosition = `${left}% ${top}%`; });
    }
    function set(left, top) {
      x.value = Math.max(0, Math.min(100, Math.round(left)));
      y.value = Math.max(0, Math.min(100, Math.round(top)));
      draw();
    }
    let version = 0;
    function load(reset) {
      const current = ++version;
      if (reset) set(50, 50);
      selectedImage.value = select.value;
      content.hidden = true;
      if (!select.value) {
        status.textContent = 'Für die Ausschnittvorschau zuerst ein Titelbild auswählen.';
        return;
      }
      status.textContent = 'Bildvorschau wird geladen …';
      const url = `/redaktion/medien/${encodeURIComponent(select.value)}/large`;
      const pending = new Image();
      pending.onload = () => {
        if (current !== version) return;
        image.src = url;
        samples.forEach((img, index) => {
          img.src = url;
          if (index >= 5) {
            const width = index === 5 ? 960 : 358;
            img.style.aspectRatio = index === 5
              ? width / Math.min(640, width * pending.naturalHeight / pending.naturalWidth)
              : pending.naturalWidth / pending.naturalHeight;
          }
        });
        status.textContent = '';
        content.hidden = false;
        draw();
      };
      pending.onerror = () => {
        if (current === version) status.textContent = 'Bildvorschau nicht verfügbar. Auswahl und Bildberechtigung prüfen. Die Prozentfelder bleiben verwendbar.';
      };
      pending.src = url;
    }
    function move(event) {
      const rect = source.getBoundingClientRect();
      set((event.clientX - rect.left) / rect.width * 100, (event.clientY - rect.top) / rect.height * 100);
    }
    source.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      event.preventDefault();
      source.setPointerCapture(event.pointerId);
      point.focus({ preventScroll: true });
      move(event);
    });
    source.addEventListener('pointermove', event => {
      if (source.hasPointerCapture(event.pointerId)) move(event);
    });
    point.addEventListener('keydown', event => {
      const step = event.shiftKey ? 10 : 1;
      const delta = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[event.key];
      if (!delta) return;
      event.preventDefault();
      set(number(x) + delta[0], number(y) + delta[1]);
    });
    panel.querySelector('.focus-reset').addEventListener('click', () => set(50, 50));
    [x, y].forEach(field => field.addEventListener('input', draw));
    select.addEventListener('change', () => load(true));
    load(false);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
