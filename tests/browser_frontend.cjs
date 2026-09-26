// Requests are fulfilled from actual Django-rendered fixtures and shipped assets.
// This is layout/navigation verification, not a substitute for PostgreSQL tests.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const errors = [], external = [];
  const fixtures = '.qa/frontend';
  const names = fs.readdirSync(fixtures).filter(name => name.endsWith('.html'));
  const captures = new Set(['home','article','submission-disabled','long-title','search','submission-error']);
  try {
    for (const width of [360, 768, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 } });
      await context.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.host !== 'fixture.test') { external.push(url.href); return route.abort(); }
        if (url.pathname.startsWith('/static/news/')) {
          const file = path.join('news/static/news', url.pathname.slice('/static/news/'.length));
          const type = file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'text/javascript' : file.endsWith('.ttf') ? 'font/ttf' : 'image/jpeg';
          return route.fulfill({ body: fs.readFileSync(file), contentType: type });
        }
        if (/^\/(redaktion\/)?medien\//.test(url.pathname)) {
          return route.fulfill({ contentType:'image/svg+xml', body:'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="600"><rect width="1200" height="600" fill="#e5ded3"/><path d="M0 440H1200M400 0V600M800 0V600" stroke="#b9afa0" stroke-width="2"/><text x="600" y="300" text-anchor="middle" font-family="Arial" font-size="40" fill="#5e5953">TESTGRAFIK · KEIN SCHULFOTO</text></svg>' });
        }
        const name = url.pathname.slice(1) || 'home.html';
        return route.fulfill({body:fs.readFileSync(path.join(fixtures, name)), contentType:'text/html'});
      });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      for (const name of names) {
        await page.goto(`http://fixture.test/${name}`);
        await page.evaluate(() => document.fonts.ready);
        // Lazy images outside the viewport legitimately wait until scrolling.
        // Decode all of them before full-page capture and asset assertions.
        await page.locator('img').evaluateAll(images => Promise.all(images.map(async img => {
          img.loading = 'eager';
          await img.decode();
        })));
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${name}: overflow at ${width}`);
        assert.equal(await page.locator('h1').count(), 1, `${name}: one h1`);
        assert.equal(await page.evaluate(() => document.fonts.check('18px "Source Serif 4"') && document.fonts.check('16px "Source Sans 3"')), true);
        assert.equal(await page.locator('img').evaluateAll(images => images.every(img => img.complete && img.naturalWidth > 0)), true, `${name}: image load`);
        if (captures.has(name.replace('.html',''))) await page.screenshot({path:`${fixtures}/${name.replace('.html','')}-${width}.png`,fullPage:true});
      }
      await page.goto('http://fixture.test/home.html');
      await page.keyboard.press('Tab');
      assert.equal(await page.locator('.skip-link').evaluate(el => el === document.activeElement), true);
      assert.equal(await page.locator('.skip-link').evaluate(el => getComputedStyle(el).outlineWidth), '3px');
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('main').evaluate(el => el === document.activeElement), true);
      if (width < 1024) {
        await page.locator('.menu-toggle').click();
        assert.equal(await page.locator('.menu-toggle').getAttribute('aria-expanded'), 'true');
        assert.equal(await page.locator('.menu-close').evaluate(el => el === document.activeElement), true);
        await page.keyboard.press('Shift+Tab');
        assert.equal(await page.locator('.submit-link').evaluate(el => el === document.activeElement), true);
        await page.keyboard.press('Tab');
        assert.equal(await page.locator('.menu-close').evaluate(el => el === document.activeElement), true);
        assert.equal(await page.locator('main').evaluate(el => el.inert), true);
        await page.keyboard.press('Escape');
        assert.equal(await page.locator('.menu-toggle').evaluate(el => el === document.activeElement), true);
        assert.equal(await page.locator('main').evaluate(el => el.inert), false);
      }
      await page.goto('http://fixture.test/submission-disabled.html');
      assert.equal(await page.locator('button[type=submit]').isDisabled(), true);
      await page.goto('http://fixture.test/submission-error.html');
      assert.equal(await page.locator('#id_name').inputValue(), 'Erhaltene Eingabe');
      await context.close();
      console.log(`${width}px: ${names.length} pages, fonts, images, no overflow, keyboard and state checks passed.`);
    }
    const nojs = await browser.newContext({javaScriptEnabled:false,viewport:{width:360,height:900}});
    await nojs.route('**/*', route => {
      const url = new URL(route.request().url());
      const file = url.pathname.startsWith('/static/') ? path.join('news/static/news', path.basename(url.pathname)) : '.qa/frontend/empty-home.html';
      if (url.pathname.includes('/fonts/')) return route.fulfill({body:fs.readFileSync(path.join('news/static/news/fonts',path.basename(url.pathname))),contentType:'font/ttf'});
      return route.fulfill({body:fs.readFileSync(file),contentType:file.endsWith('.css')?'text/css':file.endsWith('.jpg')?'image/jpeg':'text/html'});
    });
    const page = await nojs.newPage();
    await page.goto('http://fixture.test/empty-home.html');
    assert.equal(await page.locator('#main-nav').isVisible(), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    console.log('No-JavaScript navigation passed. No JS errors or external requests.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
