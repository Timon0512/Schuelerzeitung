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
  fs.mkdirSync('.qa', { recursive: true });
  for (const width of [1280, 390]) {
    const page = await browser.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.setViewportSize({ width, height: 950 });
    await page.setContent(`<!doctype html><html lang="de"><head><meta charset="utf-8"><style>body{margin:16px;font:16px Arial}select{max-width:100%} ${css}</style></head><body>
      <h1>Artikel bearbeiten</h1><form><label for="id_text_images">Textbilder</label>
      <select id="id_text_images" multiple><option selected value="${id}">Ein Testbild</option></select>
      <p><label for="id_body">Artikeltext</label></p><textarea id="id_body" name="body" class="kaktus-editor">&lt;p&gt;Redaktioneller Testtext&lt;/p&gt;</textarea>
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
    // All generated image nodes must use private local routes.
    await page.getByRole('combobox', { name: 'Ausgewähltes Textbild einfügen' }).selectOption(id);
    await page.getByRole('button', { name: 'Bild einfügen', exact: true }).click();
    assert.match(await page.locator('#id_body').inputValue(), new RegExp(`/redaktion/medien/${id}`));
    await page.locator('form').evaluate(form => form.addEventListener('submit', event => event.preventDefault()));
    await page.getByRole('button', { name: 'Speichern', exact: true }).click();
    assert.match(await page.locator('#id_body').inputValue(), /data-media-id/);
    await page.close();
  }
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('Editor browser checks passed at 1280px and 390px; screenshots in .qa/.');
})().catch(error => { console.error(error); process.exit(1); });
