const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const base = process.env.ADMIN_BROWSER_BASE || 'http://127.0.0.1:8769';
const username = process.env.ADMIN_BROWSER_USER;
const password = process.env.ADMIN_BROWSER_PASSWORD;

async function login(page) {
  await page.goto(base + '/admin/');
  await page.locator('#id_username').fill(username);
  await page.locator('#id_password').fill(password);
  await page.locator('#login-form input[type="submit"]').click();
  await page.getByRole('heading', { name: 'Redaktionsübersicht' }).waitFor();
}

async function checkWidth(page) {
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'Page must not scroll horizontally');
}

async function fixturePhoto(page) {
  const data = await page.evaluate(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 600;
    const context = canvas.getContext('2d');
    context.fillStyle = '#d9b386';
    context.fillRect(0, 0, 800, 600);
    context.fillStyle = '#226361';
    context.fillRect(120, 160, 240, 320);
    context.fillStyle = '#773560';
    context.fillRect(520, 120, 120, 260);
    return canvas.toDataURL().split(',')[1];
  });
  return Buffer.from(data, 'base64');
}

async function upload(page, alt, buffer) {
  const dialog = page.getByRole('dialog');
  await dialog.locator('input[type="file"]').setInputFiles({ name: 'testfoto.png', mimeType: 'image/png', buffer });
  await dialog.getByRole('textbox', { name: 'Alternativtext' }).fill(alt);
  await dialog.getByRole('button', { name: 'Hochladen und einfügen' }).click();
  await dialog.waitFor({ state: 'hidden' });
}

async function touchCrop(page, context) {
  const cdp = await context.newCDPSession(page);
  const box = await page.locator('.crop-stage').boundingBox();
  const x = Math.round(box.x + box.width / 2);
  const y = Math.round(box.y + box.height / 2);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ id: 1, x: x - 30, y }, { id: 2, x: x + 30, y }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ id: 1, x: x - 65, y }, { id: 2, x: x + 65, y }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  assert.ok(Number(await page.locator('#crop-zoom').inputValue()) > 140, 'Pinch should increase zoom');
  const initial = await page.locator('.crop-stage img').evaluate(image => image.style.left);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ id: 1, x, y }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ id: 1, x: x + 24, y }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  assert.notEqual(await page.locator('.crop-stage img').evaluate(image => image.style.left), initial);
}

(async () => {
  assert.ok(username && password, 'Set ADMIN_BROWSER_USER and ADMIN_BROWSER_PASSWORD for a disposable publication account. The test creates a draft, uploads two photos, and briefly publishes the article.');
  assert.ok(['127.0.0.1', 'localhost', '[::1]'].includes(new URL(base).hostname), 'Use a local test instance.');
  const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_EXECUTABLE });
  const errors = [];
  const title = 'Bildworkflow Test ' + Date.now();
  fs.mkdirSync('.qa/images', { recursive: true });
  try {
    let articleUrl;
    for (const width of [1440, 768, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, hasTouch: width === 390 });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      page.on('dialog', dialog => dialog.accept());
      await login(page);
      await checkWidth(page);
      await page.screenshot({ path: '.qa/images/admin-overview-' + width + '.png' });
      if (width < 861) {
        await page.getByRole('button', { name: 'Menü' }).click();
        await page.getByRole('navigation', { name: 'Redaktionsmenü' }).waitFor();
        await page.keyboard.press('Escape');
        assert.equal(await page.getByRole('button', { name: 'Menü' }).getAttribute('aria-expanded'), 'false');
      }
      if (articleUrl) {
        await page.goto(articleUrl);
      } else {
        await page.getByRole('link', { name: 'Neuen Artikel schreiben' }).click();
        await page.locator('#id_title').fill(title);
        const category = page.locator('#id_category option').nth(1);
        await page.locator('#id_category').selectOption(await category.getAttribute('value'));
        await page.locator('#id_authors input').first().check();
        await page.locator('.tiptap').fill('Der erste Absatz.');
        const buffer = await fixturePhoto(page);
        const addCover = page.getByRole('button', { name: 'Titelbild hinzufügen' });
        await addCover.click();
        await page.screenshot({ path: '.qa/images/admin-upload-' + width + '.png' });
        const dialog = page.getByRole('dialog');
        await dialog.locator('input[type="file"]').setInputFiles({ name: 'ungueltig.png', mimeType: 'image/png', buffer: Buffer.from('test') });
        await dialog.getByRole('textbox', { name: 'Alternativtext' }).fill('Ungültiger Upload');
        await dialog.getByRole('button', { name: 'Hochladen und einfügen' }).click();
        await dialog.getByText('Das Bild ist beschädigt oder kann nicht sicher geöffnet werden.').waitFor();
        await upload(page, 'Titelbild der Testausgabe', buffer);
        assert.equal(await page.locator('#id_title').inputValue(), title);

        await page.getByRole('button', { name: 'Ausschnitt', exact: true }).click();
        await page.locator('.crop-stage').waitFor();
        await page.getByRole('combobox', { name: 'Vorschauformat' }).selectOption('lead');
        await page.getByRole('button', { name: 'Vergrößern' }).click();
        const bounds = await page.locator('.crop-stage').boundingBox();
        await page.mouse.move(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
        await page.mouse.down();
        await page.mouse.move(bounds.x + bounds.width / 2 + 36, bounds.y + bounds.height / 2, { steps: 5 });
        await page.mouse.up();
        await page.getByRole('button', { name: 'Übernehmen' }).click();
        assert.equal(await page.locator('#id_hero_zoom').inputValue(), '110');
        assert.notEqual(await page.locator('#id_hero_focus_x').inputValue(), '50');

        await page.locator('.tiptap').press('End');
        await page.getByRole('button', { name: 'Bild einfügen' }).click();
        await upload(page, 'Foto im Artikeltext', buffer);
        assert.deepEqual(await page.locator('.tiptap > *').evaluateAll(nodes => nodes.slice(0, 2).map(node => node.classList.contains('editor-text-image') ? 'IMG' : node.tagName)), ['P', 'IMG']);
        await page.locator('.tiptap img').click();
        await page.getByRole('button', { name: 'Bildausschnitt', exact: true }).click();
        await page.locator('.crop-stage').waitFor();
        await page.getByRole('combobox', { name: 'Bildformat' }).selectOption('1-1');
        await page.getByRole('button', { name: 'Vergrößern' }).click();
        await page.getByRole('button', { name: 'Übernehmen' }).click();
        assert.match(await page.locator('#id_body').inputValue(), /data-crop="1-1\/50\/50\/110"/);

        const previewTab = page.waitForEvent('popup');
        await page.getByRole('button', { name: 'Vorschau', exact: true }).click();
        const preview = await previewTab;
        await preview.locator('.hero-image .title-crop').waitFor();
        assert.equal(await preview.locator('.article-body .text-crop').count(), 1);
        await preview.locator('.article-body .text-crop img').scrollIntoViewIfNeeded();
        await preview.waitForFunction(() => {
          const image = document.querySelector('.article-body .text-crop img');
          return image?.complete && image.naturalWidth > 0;
        });
        await preview.close();

        await page.getByRole('button', { name: 'Entwurf speichern' }).click();
        await page.waitForURL(/\/admin\/news\/article\/\d+\/change\//);
        articleUrl = page.url();
        assert.equal(await page.locator('#id_hero_zoom').inputValue(), '110');
        assert.match(await page.locator('#id_body').inputValue(), /data-crop="1-1\/50\/50\/110"/);
        await page.getByRole('button', { name: 'Speichern und veröffentlichen' }).click();
        await page.getByText('Der Artikel wurde veröffentlicht.').waitFor();
        const slug = await page.locator('#id_slug').inputValue();
        const publicPage = await context.newPage();
        await publicPage.goto(base + '/artikel/' + slug);
        await publicPage.locator('.hero-image .title-crop').waitFor();
        assert.equal(await publicPage.locator('.article-body .text-crop').count(), 1);
        await publicPage.close();
        await page.getByRole('button', { name: 'Zurückziehen', exact: true }).click();
        await page.getByRole('button', { name: 'Entwurf speichern' }).waitFor();
      }
      await checkWidth(page);
      await page.screenshot({ path: '.qa/images/admin-editor-' + width + '.png' });
      await page.getByRole('button', { name: 'Ausschnitt', exact: true }).click();
      await page.locator('.crop-stage').waitFor();
      await page.getByRole('combobox', { name: 'Vorschauformat' }).selectOption('lead');
      if (width === 390) await touchCrop(page, context);
      if (width === 768) {
        const stage = page.locator('.crop-stage');
        const top = await stage.locator('img').evaluate(img => img.style.top);
        await stage.press('ArrowUp');
        assert.notEqual(await stage.locator('img').evaluate(img => img.style.top), top);
      }
      await page.screenshot({ path: '.qa/images/admin-crop-' + width + '.png' });
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#id_hero_zoom').inputValue(), '110');
      await page.getByRole('button', { name: 'Bild wechseln' }).click();
      await page.getByRole('button', { name: 'Aus Mediathek wählen' }).click();
      await page.getByRole('searchbox', { name: 'Bilder suchen' }).fill('Foto im Artikeltext');
      await page.getByRole('button', { name: 'Suchen', exact: true }).click();
      await page.getByRole('button', { name: 'Foto im Artikeltext', exact: true }).first().waitFor();
      await page.screenshot({ path: '.qa/images/admin-library-' + width + '.png' });
      await page.keyboard.press('Escape');
      await page.goto(base + '/admin/news/article/');
      await page.getByRole('link', { name: title }).waitFor();
      await checkWidth(page);
      if (width === 390) assert.ok((await page.locator('th.field-title').first().boundingBox()).width > 150);
      await page.screenshot({ path: '.qa/images/admin-articles-' + width + '.png' });
      await context.close();
    }
    assert.deepEqual(errors, []);
    console.log('Admin upload, crop, publication and responsive browser checks passed.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
