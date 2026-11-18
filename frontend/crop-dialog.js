const ratios = { 'original': 0, '4-3': 4 / 3, '1-1': 1, '16-9': 16 / 9 };
const defaults = { ratio: 'original', x: 50, y: 50, zoom: 100 };
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

export function readCrop(value) {
  const match = /^(original|4-3|1-1|16-9)\/([0-9]{1,3})\/([0-9]{1,3})\/([0-9]{3})$/.exec(value || '');
  if (!match) return { ...defaults };
  const [x, y, zoom] = match.slice(2).map(Number);
  if (x > 100 || y > 100 || zoom < 100 || zoom > 300) return { ...defaults };
  return { ratio: match[1], x, y, zoom };
}

export function writeCrop(crop) {
  if (crop.ratio === 'original' && Math.round(crop.zoom) === 100) return null;
  return [crop.ratio, Math.round(crop.x), Math.round(crop.y), Math.round(crop.zoom)].join('/');
}

export function createCropDialog() {
  const dialog = document.createElement('dialog');
  dialog.className = 'editor-dialog';
  dialog.setAttribute('aria-labelledby', 'crop-title');
  dialog.innerHTML = `
    <div class="editor-dialog-head"><h2 id="crop-title">Bildausschnitt</h2><button type="button" data-cancel>Abbrechen</button></div>
    <div class="editor-dialog-body">
      <div class="crop-format">
        <label data-text>Bildformat
          <select aria-label="Bildformat">
            <option value="original">Original</option><option value="4-3">4:3</option>
            <option value="1-1">1:1</option><option value="16-9">16:9</option>
          </select>
        </label>
        <label data-cover>Vorschau
          <select aria-label="Vorschauformat">
            <option value="article">Artikelseite</option><option value="lead">Aufmacher</option>
            <option value="card">Kachel</option><option value="compact">Kompakte Kachel</option>
            <option value="latest">Kachel unter „Gerade neu“</option>
          </select>
        </label>
        <label data-device>Ansicht
          <select aria-label="Gerät">
            <option value="desktop">Desktop</option><option value="tablet">Tablet</option><option value="phone">Smartphone</option>
          </select>
        </label>
      </div>
      <p data-load role="status"></p>
      <div class="crop-stage" tabindex="0" role="region" aria-label="Bild unter dem Raster verschieben" aria-describedby="crop-help" hidden>
        <img alt="" draggable="false"><div class="crop-frame" aria-hidden="true"></div>
      </div>
      <p class="crop-help" id="crop-help">Ziehe das Foto oder verschiebe es mit den Pfeiltasten.</p>
      <div class="crop-zoom">
        <button type="button" data-minus aria-label="Verkleinern">−</button>
        <label for="crop-zoom">Zoom</label>
        <input type="range" id="crop-zoom" min="100" max="300" step="1" value="100">
        <output for="crop-zoom">100 %</output>
        <button type="button" data-plus aria-label="Vergrößern">+</button>
      </div>
    </div>
    <div class="editor-dialog-foot"><button type="button" data-reset>Zurücksetzen</button><button type="button" class="editorial-action-button editorial-primary" data-apply>Übernehmen</button></div>
  `;
  document.body.append(dialog);
  const stage = dialog.querySelector('.crop-stage');
  const photo = stage.querySelector('img');
  const frame = stage.querySelector('.crop-frame');
  const status = dialog.querySelector('[data-load]');
  const slider = dialog.querySelector('input');
  const output = dialog.querySelector('output');
  const apply = dialog.querySelector('[data-apply]');
  const reset = dialog.querySelector('[data-reset]');
  const minus = dialog.querySelector('[data-minus]');
  const plus = dialog.querySelector('[data-plus]');
  const textPicker = dialog.querySelector('[data-text]');
  const coverPicker = dialog.querySelector('[data-cover]');
  const devicePicker = dialog.querySelector('[data-device]');
  const textRatio = textPicker.querySelector('select');
  const layout = coverPicker.querySelector('select');
  const device = devicePicker.querySelector('select');
  const pointers = new Map();
  let crop;
  let cover;
  let geometry;
  let naturalRatio;
  let onApply;
  let focusTarget;
  let imageLoad = 0;

  function frameRatio() {
    if (!cover) return ratios[crop.ratio] || naturalRatio;
    if (layout.value === 'lead') return 2;
    if (layout.value === 'card') return 2.4;
    if (layout.value === 'compact') return { desktop: 2.4, tablet: 1.5, phone: 1.4 }[device.value];
    if (layout.value === 'latest') return device.value === 'desktop' ? 2.4 : 1.5;
    if (device.value === 'phone') return naturalRatio;
    const width = device.value === 'tablet' ? 720 : 960;
    return Math.max(naturalRatio, width / 640);
  }

  function draw() {
    if (stage.hidden || !dialog.open) return;
    const zoom = Math.round(crop.zoom);
    slider.value = zoom;
    slider.setAttribute('aria-valuetext', zoom + ' Prozent');
    output.value = zoom + ' %';
    minus.disabled = zoom <= 100;
    plus.disabled = zoom >= 300;
    const ratio = frameRatio();
    const width = Math.min(stage.clientWidth - 24, (stage.clientHeight - 18) * ratio);
    const height = width / ratio;
    const left = (stage.clientWidth - width) / 2;
    const top = (stage.clientHeight - height) / 2;
    const imageWidth = Math.max(width, height * naturalRatio) * crop.zoom / 100;
    const imageHeight = imageWidth / naturalRatio;
    const extraX = Math.max(0, imageWidth - width);
    const extraY = Math.max(0, imageHeight - height);
    const photoX = left - extraX * crop.x / 100;
    const photoY = top - extraY * crop.y / 100;
    geometry = { left, top, width, height, imageWidth, imageHeight, extraX, extraY, photoX, photoY };
    Object.assign(frame.style, { left: left + 'px', top: top + 'px', width: width + 'px', height: height + 'px' });
    Object.assign(photo.style, {
      left: photoX + 'px', top: photoY + 'px', width: imageWidth + 'px', height: imageHeight + 'px',
    });
  }

  function move(dx, dy) {
    if (geometry.extraX > 0.01) crop.x = clamp(crop.x - dx * 100 / geometry.extraX, 0, 100);
    if (geometry.extraY > 0.01) crop.y = clamp(crop.y - dy * 100 / geometry.extraY, 0, 100);
    draw();
  }

  function changeZoom(zoom) {
    crop.zoom = clamp(zoom, 100, 300);
    draw();
  }

  const observe = new ResizeObserver(draw);
  observe.observe(stage);
  const position = event => ({ x: event.clientX, y: event.clientY });
  const midpoint = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  stage.addEventListener('pointerdown', event => {
    if (event.button !== 0 || pointers.size === 2) return;
    stage.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, position(event));
  });
  stage.addEventListener('pointermove', event => {
    const before = pointers.get(event.pointerId);
    if (!before || !geometry) return;
    const after = position(event);
    const other = pointers.size === 2 && [...pointers.entries()].find(([id]) => id !== event.pointerId)[1];
    pointers.set(event.pointerId, after);
    if (!other) {
      move(after.x - before.x, after.y - before.y);
      return;
    }
    const prior = midpoint(before, other);
    const next = midpoint(after, other);
    const rect = stage.getBoundingClientRect();
    const anchorX = (prior.x - rect.left - geometry.photoX) / geometry.imageWidth;
    const anchorY = (prior.y - rect.top - geometry.photoY) / geometry.imageHeight;
    const factor = distance(after, other) / Math.max(1, distance(before, other));
    changeZoom(crop.zoom * factor);
    const newPhotoX = next.x - rect.left - anchorX * geometry.imageWidth;
    const newPhotoY = next.y - rect.top - anchorY * geometry.imageHeight;
    move(newPhotoX - geometry.photoX, newPhotoY - geometry.photoY);
  });
  for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) {
    stage.addEventListener(event, pointer => pointers.delete(pointer.pointerId));
  }
  stage.addEventListener('keydown', event => {
    const movement = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
    if (!movement) return;
    const step = event.shiftKey ? 20 : 5;
    event.preventDefault();
    move(movement[0] * step, movement[1] * step);
  });

  textRatio.addEventListener('change', () => { crop.ratio = textRatio.value; draw(); });
  layout.addEventListener('change', draw);
  device.addEventListener('change', draw);
  slider.addEventListener('input', () => changeZoom(Number(slider.value)));
  minus.addEventListener('click', () => changeZoom(crop.zoom - 10));
  plus.addEventListener('click', () => changeZoom(crop.zoom + 10));
  reset.addEventListener('click', () => { crop = { ...defaults }; textRatio.value = crop.ratio; draw(); });
  apply.addEventListener('click', () => {
    dialog.close();
    onApply({ ratio: crop.ratio, x: Math.round(crop.x), y: Math.round(crop.y), zoom: Math.round(crop.zoom) });
  });
  dialog.querySelector('[data-cancel]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { pointers.clear(); focusTarget?.focus(); });

  return (image, initial, isCover, callback) => {
    const current = ++imageLoad;
    crop = { ...initial };
    cover = isCover;
    onApply = callback;
    focusTarget = document.activeElement;
    textPicker.hidden = cover;
    coverPicker.hidden = devicePicker.hidden = !cover;
    textRatio.value = crop.ratio;
    layout.value = 'article';
    device.value = window.matchMedia('(max-width: 767px)').matches ? 'phone' : 'desktop';
    stage.hidden = true;
    apply.disabled = reset.disabled = slider.disabled = minus.disabled = plus.disabled = true;
    status.textContent = 'Foto wird geladen …';
    dialog.showModal();
    const preview = new Image();
    preview.onload = () => {
      if (current !== imageLoad || !dialog.open) return;
      naturalRatio = preview.naturalWidth / preview.naturalHeight;
      photo.src = preview.src;
      status.textContent = '';
      stage.hidden = false;
      apply.disabled = reset.disabled = slider.disabled = false;
      draw();
    };
    preview.onerror = () => {
      if (current === imageLoad) status.textContent = 'Das Foto konnte nicht geladen werden.';
    };
    preview.src = image.src;
  };
}
