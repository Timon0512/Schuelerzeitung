const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  const id = '12345678-1234-1234-1234-123456789abc';
  const other = '23456789-1234-1234-1234-123456789abc';
  const script = fs.readFileSync('news/static/news/image-focus.js', 'utf8');
  const css = fs.readFileSync('news/static/news/image-focus.css', 'utf8');
  fs.mkdirSync('.qa/images', { recursive: true });
  try {
    for (const width of [1280, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, hasTouch: true });
      const requests = [];
      await context.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.pathname.startsWith('/redaktion/medien/')) {
          if (url.pathname.includes(other)) return route.fulfill({ status: 403, contentType: "text/plain", body: "Forbidden" });
          return route.fulfill({ contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800"><rect width="1200" height="800" fill="#ead9c3"/><rect x="800" y="100" width="120" height="500" fill="#943916"/><text x="30" y="400" font-size="65">Testbild: Motiv rechts</text></svg>' });
        }
        if (url.pathname.startsWith('/medien/')) {
          requests.push(url.pathname);
          const w = url.pathname.endsWith('/small') ? 640 : 1920;
          return route.fulfill({ contentType: 'image/svg+xml', body: `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${w / 2}"><rect width="100%" height="100%" fill="#ead9c3"/></svg>` });
        }
        if (url.pathname.startsWith('/static/news/')) {
          const file = 'news/static/news/' + url.pathname.slice('/static/news/'.length);
          return route.fulfill({ body: fs.readFileSync(file), contentType: file.endsWith('.css') ? 'text/css' : file.endsWith('.ttf') ? 'font/ttf' : 'image/jpeg' });
        }
        if (url.pathname === '/article') return route.fulfill({ body: fs.readFileSync('.qa/frontend/article.html'), contentType: 'text/html' });
        return route.fulfill({ contentType: 'text/html', body: `<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>body{font:16px Arial;margin:16px}input,select{font:inherit;max-width:100%;box-sizing:border-box}.form-row{padding:12px 0}label{display:block} ${css}</style><h1>Artikel bearbeiten</h1><form>
          <label for="id_hero_image">Titelbild</label><select id="id_hero_image"><option value="">Kein Titelbild</option><option value="${id}" selected>Motiv rechts</option><option value="${other}">Nicht verfügbar</option></select>
          <div class="form-row"><label for="id_hero_focus_x">Bildfokus horizontal (%)</label><input id="id_hero_focus_x" type="number" min="0" max="100" value="25"></div>
          <div class="form-row"><label for="id_hero_focus_y">Bildfokus vertikal (%)</label><input id="id_hero_focus_y" type="number" min="0" max="100" value="60"></div>
          <input id="id_hero_focus_image" type="hidden" value="${id}"></form><script>${script}</script></html>` });
      });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      await page.goto('http://fixture.test/focus');
      await page.locator('.focus-content').waitFor({ state: 'visible' });
      assert.equal(await page.locator('.focus-previews img').first().evaluate(img => img.style.objectPosition), '25% 60%');
      const point = page.locator('.focus-point');
      await point.focus();
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.locator('#id_hero_focus_x').inputValue(), '26');
      await page.keyboard.press('Shift+ArrowDown');
      assert.equal(await page.locator('#id_hero_focus_y').inputValue(), '70');
      const source = page.locator('.focus-source');
      const rect = await source.boundingBox();
      await page.touchscreen.tap(rect.x + rect.width * .75, rect.y + rect.height * .25);
      assert.equal(await page.locator('#id_hero_focus_x').inputValue(), '75');
      assert.equal(await page.locator('#id_hero_focus_y').inputValue(), '25');
      await page.mouse.move(rect.x + rect.width * .75, rect.y + rect.height * .25);
      await page.mouse.down();
      await page.mouse.move(rect.x + rect.width * .8, rect.y + rect.height * .4);
      await page.mouse.up();
      assert.equal(await page.locator('#id_hero_focus_x').inputValue(), '80');
      await page.locator('#id_hero_focus_x').fill('90');
      assert.equal(await page.locator('.focus-previews img').first().evaluate(img => img.style.objectPosition), '90% 40%');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `.qa/images/focus-${width}.png`, fullPage: true });
      await page.getByRole('button', { name: 'Bildmitte verwenden' }).click();
      assert.equal(await page.locator('#id_hero_focus_x').inputValue(), '50');
      await page.locator('#id_hero_image').selectOption('');
      assert.match(await page.locator('.focus-status').innerText(), /zuerst ein Titelbild/);
      await page.locator('#id_hero_image').selectOption(other);
      await page.waitForFunction(() => document.querySelector('.focus-status').textContent.includes('nicht verfügbar'));
      await page.goto('http://fixture.test/article');
      await page.locator('.hero-image img').evaluate(img => img.decode());
      const selected = await page.locator('.hero-image img').evaluate(img => img.currentSrc);
      assert.ok(selected.endsWith(width === 390 ? '/small' : '/large'), selected);
      assert.equal(requests.some(url => !url.endsWith('/small') && !url.endsWith('/large')), false);
      console.log(`${width}px: focus mouse/touch/keyboard and responsive source ${selected.split('/').pop()} passed`);
      await context.close();
    }
    assert.deepEqual(errors, []);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
