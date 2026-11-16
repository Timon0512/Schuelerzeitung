// Isolated browser test of the shipped editor bundle; no database or account required.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  const bundle = fs.readFileSync('news/static/news/editor.js', 'utf8');
  const css = fs.readFileSync('news/static/news/editor.css', 'utf8');
  const id = '12345678-1234-1234-1234-123456789abc';
  const secondId = '12345678-1234-1234-1234-123456789def';
  fs.mkdirSync('.qa', { recursive: true });
  for (const width of [1280, 390]) {
    const page = await browser.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.setViewportSize({ width, height: 950 });
    await page.setContent(`<!doctype html><html lang="de"><head><meta charset="utf-8"><style>body{margin:16px;font:16px Arial}select{max-width:100%} ${css}</style></head><body>
      <h1>Artikel bearbeiten</h1><form><label for="id_hero_image">Titelbild</label>
      <select id="id_hero_image" name="hero_image"><option value="" selected>---------</option><option value="${id}">Ein Testbild</option><option value="${secondId}">Zweites Testbild</option></select>
      <p><label for="id_body">Artikeltext</label></p><textarea id="id_body" name="body" class="kaktus-editor">&lt;p&gt;Redaktioneller Testtext&lt;/p&gt;&lt;p&gt;Zweiter Absatz&lt;/p&gt;</textarea>
      <p><button type="submit">Speichern</button></p></form><script>${bundle}</script></body></html>`);
    await page.locator('.tiptap').waitFor();
    await page.getByRole('button', { name: 'Zwischenüberschrift', exact: true }).click();
    assert.match(await page.locator('#id_body').inputValue(), /<h2>/);
    await page.getByRole('button', { name: 'Fett', exact: true }).click();
    await page.waitForFunction(() => document.activeElement.classList.contains('tiptap'));
    await page.keyboard.type(' Ergänzung');
    assert.match(await page.locator('#id_body').inputValue(), /<strong>/);
    await page.getByRole('button', { name: 'Liste', exact: true }).click();
    assert.match(await page.locator('#id_body').inputValue(), /<ul>/);
    await page.getByRole('button', { name: 'Liste', exact: true }).click();
    await page.getByRole('button', { name: 'Absatz', exact: true }).click();
    await page.getByRole('button', { name: 'Fett', exact: true }).focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle), 'solid');
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    assert.equal(overflow, false, `Horizontal overflow at ${width}`);
    await page.screenshot({ path: path.join('.qa', `editor-${width}.png`), fullPage: true });
    const insert = page.getByRole('button', { name: 'Bild einfügen', exact: true });
    const firstChoice = page.getByRole('button', { name: 'Ein Testbild', exact: true });
    await page.locator('.tiptap p').first().click();
    await page.keyboard.press('End');
    await insert.click();
    await page.waitForFunction(() => document.activeElement.textContent === 'Ein Testbild');
    await page.keyboard.press('Escape');
    assert.equal(await insert.getAttribute('aria-expanded'), 'false');
    assert.equal(await insert.evaluate(button => button === document.activeElement), true);
    await insert.press('Enter');
    await page.screenshot({ path: path.join('.qa', `editor-image-picker-${width}.png`), fullPage: true });
    await firstChoice.press('Enter');
    assert.equal(await insert.getAttribute('aria-expanded'), 'false');
    assert.equal(await page.locator('#id_hero_image').inputValue(), '');
    assert.match(await page.locator('#id_body').inputValue(), new RegExp(`/redaktion/medien/${id}`));
    assert.deepEqual(await page.locator('.tiptap > *').evaluateAll(nodes => nodes.slice(0, 3).map(node => node.tagName)), ['P', 'IMG', 'P']);
    await page.waitForFunction(() => document.activeElement.classList.contains('tiptap'));
    await page.locator('form').evaluate(form => form.addEventListener('submit', event => event.preventDefault()));
    await page.getByRole('button', { name: 'Speichern', exact: true }).click();
    assert.match(await page.locator('#id_body').inputValue(), /data-media-id/);
    await page.locator('#id_hero_image option:not([value=""])').evaluateAll(options => options.forEach(option => option.remove()));
    await insert.click();
    assert.equal(await page.getByText('Noch keine Bilder verfügbar.', { exact: false }).isVisible(), true);
    await page.setContent(`<!doctype html><form>
      <select name="hero_image"><option value="">---------</option><option value="${id}">Ein Testbild</option></select>
      <textarea id="id_body" name="body" class="kaktus-editor">&lt;img data-media-id="${id}" src="/medien/${id}"&gt;</textarea>
      </form><script>${bundle}</script>`);
    const savedImage = page.locator('.tiptap img');
    await savedImage.waitFor({ state: 'attached' });
    assert.equal(await savedImage.getAttribute('src'), `/redaktion/medien/${id}`);
    await page.close();
  }
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('Editor browser checks passed at 1280px and 390px; screenshots in .qa/.');
})().catch(error => { console.error(error); process.exit(1); });
