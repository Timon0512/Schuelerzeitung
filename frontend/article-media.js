import { createCropDialog } from './crop-dialog.js';

export function mountArticleMedia(form, config, select) {
  const editCrop = createCropDialog();
  const dialog = document.createElement('dialog');
  dialog.className = 'editor-dialog';
  dialog.setAttribute('aria-labelledby', 'media-title');
  dialog.innerHTML = `
    <div class="editor-dialog-head"><h2 id="media-title"></h2><button type="button" data-media-close>Abbrechen</button></div>
    <div class="editor-dialog-body">
      <div class="media-modes" role="group" aria-label="Fotoquelle">
        <button type="button" data-upload>Foto hochladen</button>
        <button type="button" data-library>Aus Mediathek wählen</button>
      </div>
      <form class="media-upload">
        <label class="media-drop">
          <strong>Foto auswählen oder hier ablegen</strong>
          <span data-limits></span>
          <input name="file" type="file" accept="image/jpeg,image/png,image/webp" aria-label="Fotodatei auswählen" required>
          <span class="media-file-choose">Datei auswählen</span><span data-filename></span>
          <span class="media-error" id="media-file-error"></span>
        </label>
        <img class="media-local-preview" alt="Vorschau des ausgewählten Fotos" hidden>
        <label>Alternativtext
          <input name="alt_text" type="text" maxlength="300" required placeholder="Was ist auf dem Foto zu sehen?" aria-describedby="media-alt-error">
          <span class="media-error" id="media-alt-error"></span>
        </label>
        <label><span class="media-label">Bildunterschrift <small>(optional)</small></span>
          <input name="caption" type="text" maxlength="500" aria-describedby="media-caption-error">
          <span class="media-error" id="media-caption-error"></span>
        </label>
        <div class="media-upload-action">
          <button type="submit" class="editorial-action-button editorial-primary">Hochladen und einfügen</button>
          <progress aria-label="Uploadfortschritt" max="100" hidden></progress>
        </div>
        <p class="media-feedback" role="status"></p>
      </form>
      <section class="media-library" aria-label="Mediathek" hidden>
        <form class="media-search" role="search">
          <input type="search" aria-label="Bilder suchen" maxlength="300" placeholder="Alternativtext oder Bildunterschrift">
          <button type="submit">Suchen</button>
        </form>
        <p class="media-feedback" role="status"></p>
        <ul class="media-tiles"></ul>
        <div class="media-pagination" hidden>
          <button type="button" data-previous>Zurück</button><span></span><button type="button" data-next>Weiter</button>
        </div>
      </section>
    </div>
  `;
  document.body.append(dialog);
  const upload = dialog.querySelector('.media-upload');
  const library = dialog.querySelector('.media-library');
  const uploadMode = dialog.querySelector('[data-upload]');
  const libraryMode = dialog.querySelector('[data-library]');
  const uploadAllowed = config.dataset.canUpload === 'true';
  const file = upload.elements.file;
  const drop = file.closest('label');
  const fileName = drop.querySelector('[data-filename]');
  const localPreview = upload.querySelector('.media-local-preview');
  const startUpload = upload.querySelector('button[type="submit"]');
  const progress = upload.querySelector('progress');
  const uploadFeedback = upload.querySelector('.media-feedback');
  const searchForm = library.querySelector('form');
  const search = searchForm.querySelector('input');
  const libraryFeedback = library.querySelector('.media-feedback');
  const tiles = library.querySelector('ul');
  const pagination = library.querySelector('.media-pagination');
  const previous = pagination.querySelector('[data-previous]');
  const next = pagination.querySelector('[data-next]');
  const known = new Map();
  const maximum = Number(config.dataset.maxBytes);
  file.setAttribute('aria-describedby', 'media-limits media-file-error');
  const limits = dialog.querySelector('[data-limits]');
  limits.id = 'media-limits';
  limits.textContent = 'JPEG, PNG oder WebP · bis ' + new Intl.NumberFormat('de').format(maximum / 1024 / 1024)
    + ' MB · ' + config.dataset.maxMegapixels.replace('.', ',') + ' Megapixel';
  uploadMode.hidden = !uploadAllowed;
  let uploadRequest;
  let searchRequest;
  let localUrl;
  let currentPage;
  let onChoose;
  let focusTarget;
  let confirmed;

  const privateUrl = id => config.dataset.privateLarge.replace('00000000-0000-0000-0000-000000000000', id);
  const info = id => known.get(id) || {
    id, alt: [...select.options].find(option => option.value === id)?.textContent || '',
    src: privateUrl(id), thumb: privateUrl(id).replace(/\/large$/, '/small'),
  };

  function choose(image) {
    known.set(image.id, image);
    if (![...select.options].some(option => option.value === image.id)) {
      select.add(new Option(image.alt || 'Foto ohne Alternativtext', image.id));
    }
    confirmed = true;
    dialog.close();
    onChoose(image);
  }

  function setFilePreview() {
    if (localUrl) URL.revokeObjectURL(localUrl);
    localPreview.hidden = true;
    localPreview.removeAttribute('src');
    localUrl = undefined;
    fileName.textContent = file.files[0]?.name || '';
    if (file.files[0] && file.files[0].size <= maximum) {
      localUrl = URL.createObjectURL(file.files[0]);
      localPreview.src = localUrl;
      localPreview.hidden = false;
    }
  }

  function uploadError(name, text) {
    const field = upload.elements[name];
    const message = field && upload.querySelector('#media-' + ({ alt_text: 'alt', file: 'file', caption: 'caption' })[name] + '-error');
    if (message) {
      message.textContent = text;
      field.setAttribute('aria-invalid', String(Boolean(text)));
    } else {
      uploadFeedback.textContent = text;
    }
  }

  function showResults(data) {
    tiles.replaceChildren();
    for (const image of data.images) {
      const card = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      const photo = document.createElement('img');
      photo.src = image.thumb;
      photo.alt = '';
      photo.loading = 'lazy';
      const label = document.createElement('strong');
      label.textContent = image.alt || image.caption || 'Foto ohne Alternativtext';
      button.append(photo, label);
      if (image.caption && image.alt) {
        const caption = document.createElement('span');
        caption.textContent = image.caption;
        button.append(caption);
      }
      button.addEventListener('click', () => choose(image));
      card.append(button);
      tiles.append(card);
    }
    currentPage = data.page;
    pagination.hidden = data.pages <= 1;
    previous.disabled = data.page <= 1;
    next.disabled = data.page >= data.pages;
    pagination.querySelector('span').textContent = 'Seite ' + data.page + ' von ' + data.pages;
    libraryFeedback.textContent = data.images.length ? '' : (search.value ? 'Keine passenden Fotos gefunden.' : 'Die Mediathek enthält noch keine Fotos.');
  }

  async function loadLibrary(page = 1) {
    searchRequest?.abort();
    searchRequest = new AbortController();
    const url = new URL(config.dataset.library, location.href);
    url.searchParams.set('page', page);
    url.searchParams.set('q', search.value.trim());
    pagination.hidden = true;
    tiles.replaceChildren();
    libraryFeedback.textContent = 'Fotos werden geladen …';
    try {
      const response = await fetch(url, { signal: searchRequest.signal });
      if (!response.ok) throw new Error('media library unavailable');
      showResults(await response.json());
    } catch (error) {
      if (error.name !== 'AbortError') libraryFeedback.textContent = 'Die Mediathek konnte nicht geladen werden. Bitte versuche es erneut.';
    }
  }

  function showMode(isUpload) {
    upload.hidden = !isUpload;
    library.hidden = isUpload;
    uploadMode.setAttribute('aria-pressed', String(isUpload));
    libraryMode.setAttribute('aria-pressed', String(!isUpload));
    if (!isUpload) loadLibrary();
  }

  uploadMode.addEventListener('click', () => showMode(true));
  libraryMode.addEventListener('click', () => showMode(false));
  searchForm.addEventListener('submit', event => { event.preventDefault(); loadLibrary(); });
  previous.addEventListener('click', () => loadLibrary(currentPage - 1));
  next.addEventListener('click', () => loadLibrary(currentPage + 1));
  file.addEventListener('change', () => { uploadError('file', ''); setFilePreview(); });
  drop.addEventListener('dragover', event => {
    event.preventDefault();
    drop.classList.add('is-dragging');
  });
  drop.addEventListener('dragleave', () => drop.classList.remove('is-dragging'));
  drop.addEventListener('drop', event => {
    event.preventDefault();
    drop.classList.remove('is-dragging');
    if (event.dataTransfer.files.length !== 1) {
      uploadError('file', 'Bitte genau ein Foto ablegen.');
      return;
    }
    file.files = event.dataTransfer.files;
    file.dispatchEvent(new Event('change'));
  });
  upload.addEventListener('submit', event => {
    event.preventDefault();
    if (uploadRequest) return;
    for (const name of ['file', 'alt_text', 'caption']) uploadError(name, '');
    if (file.files[0].size > maximum) {
      uploadError('file', 'Das Foto ist zu groß. Wähle eine kleinere Datei.');
      file.focus();
      return;
    }
    const data = new FormData(upload);
    data.append('csrfmiddlewaretoken', form.elements.csrfmiddlewaretoken.value);
    const request = new XMLHttpRequest();
    uploadRequest = request;
    uploadMode.disabled = libraryMode.disabled = startUpload.disabled = true;
    uploadFeedback.textContent = 'Foto wird hochgeladen …';
    progress.hidden = false;
    progress.removeAttribute('value');
    request.upload.addEventListener('progress', event => {
      if (event.lengthComputable) progress.value = 100 * event.loaded / event.total;
    });
    request.upload.addEventListener('load', () => {
      progress.removeAttribute('value');
      uploadFeedback.textContent = 'Foto wird verarbeitet …';
    });
    const finish = () => {
      uploadRequest = undefined;
      uploadMode.disabled = libraryMode.disabled = startUpload.disabled = false;
      progress.hidden = true;
    };
    request.addEventListener('load', () => {
      finish();
      if (request.status === 201 && request.response?.id) {
        choose(request.response);
      } else if (request.response?.errors) {
        uploadFeedback.textContent = 'Bitte prüfe die markierten Felder.';
        for (const [name, errors] of Object.entries(request.response.errors)) uploadError(name, errors.join(' '));
        upload.querySelector('[aria-invalid="true"]')?.focus();
      } else {
        uploadFeedback.textContent = request.status === 413 ? 'Das Foto ist zu groß.'
          : 'Der Upload war nicht möglich. Prüfe deine Anmeldung und versuche es erneut.';
      }
    });
    request.addEventListener('error', () => {
      finish();
      uploadFeedback.textContent = 'Die Verbindung wurde unterbrochen. Bitte versuche es erneut.';
    });
    request.addEventListener('abort', finish);
    request.open('POST', config.dataset.library);
    request.responseType = 'json';
    request.send(data);
  });
  dialog.querySelector('[data-media-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    uploadRequest?.abort();
    searchRequest?.abort();
    upload.reset();
    setFilePreview();
    for (const name of ['file', 'alt_text', 'caption']) uploadError(name, '');
    uploadFeedback.textContent = '';
    searchForm.reset();
    if (!confirmed) focusTarget?.focus();
  });

  return {
    editCrop,
    info,
    pick(title, callback) {
      onChoose = callback;
      focusTarget = document.activeElement;
      confirmed = false;
      dialog.querySelector('h2').textContent = title;
      showMode(uploadAllowed);
      dialog.showModal();
      (uploadAllowed ? file : search).focus();
    },
  };
}

export function mountCoverPicker(form, select, media) {
  const row = select.closest('.form-row');
  row.id = 'artikel-titelbild';
  const x = form.elements.hero_focus_x;
  const y = form.elements.hero_focus_y;
  const zoom = form.elements.hero_zoom;
  const selectedImage = form.elements.hero_focus_image;
  const controls = document.createElement('div');
  controls.className = 'cover-media';
  controls.innerHTML = `
    <figure hidden><div class="cover-thumb-frame"><img alt=""></div><figcaption></figcaption></figure>
    <div class="cover-media-actions">
      <button type="button" class="editorial-action-button" data-select>Titelbild hinzufügen</button>
      <button type="button" class="editorial-action-button" data-crop hidden>Ausschnitt</button>
      <button type="button" class="editorial-action-button" data-remove hidden>Entfernen</button>
    </div>
  `;
  const image = controls.querySelector('img');
  const figure = controls.querySelector('figure');
  const pick = controls.querySelector('[data-select]');
  const crop = controls.querySelector('[data-crop]');
  const remove = controls.querySelector('[data-remove]');
  const currentCrop = () => ({
    ratio: 'original',
    x: Number(x.value || 50),
    y: Number(y.value || 50),
    zoom: Number(zoom.value || 100),
  });

  function refresh() {
    const id = select.value;
    crop.hidden = remove.hidden = figure.hidden = !id;
    pick.textContent = id ? 'Bild wechseln' : 'Titelbild hinzufügen';
    if (id) {
      const item = media.info(id);
      const settings = currentCrop();
      image.src = item.thumb;
      image.alt = item.alt;
      image.style.objectPosition = settings.x + '% ' + settings.y + '%';
      image.style.transformOrigin = image.style.objectPosition;
      image.style.transform = 'scale(' + settings.zoom / 100 + ')';
      controls.querySelector('figcaption').textContent = item.caption || item.alt;
    } else {
      image.removeAttribute('src');
    }
  }

  function selectImage(id) {
    if (select.value !== id) {
      select.value = selectedImage.value = id;
      x.value = y.value = 50;
      zoom.value = 100;
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
    refresh();
    pick.focus();
  }

  pick.addEventListener('click', () => media.pick('Titelbild auswählen', item => selectImage(item.id)));
  remove.addEventListener('click', () => selectImage(''));
  crop.addEventListener('click', () => media.editCrop(media.info(select.value), currentCrop(), true, result => {
    x.value = result.x;
    y.value = result.y;
    zoom.value = result.zoom;
    selectedImage.value = select.value;
    select.dispatchEvent(new Event('change', { bubbles: true }));
    refresh();
  }));
  select.closest('.related-widget-wrapper')?.setAttribute('hidden', '');
  if (!select.closest('.related-widget-wrapper')) select.hidden = true;
  for (const field of [x, y, zoom]) {
    const container = field.closest('.form-row');
    if (!container.querySelector('.errorlist')) container.hidden = true;
  }
  row.querySelector('.flex-container').append(controls);
  refresh();
}
