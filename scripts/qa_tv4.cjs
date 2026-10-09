// Optional browser acceptance test. Requires Playwright with Chromium installed.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'outputs/tv4/browser');
fs.mkdirSync(out, { recursive: true });
const url = process.env.DEMO_URL || 'http://127.0.0.1:8765';
(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHANNEL ? {channel: process.env.PLAYWRIGHT_CHANNEL} : {}) });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, acceptDownloads: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  async function run() {
    await page.locator('#run').click();
    await page.locator('#export').waitFor({ state: 'visible' });
    await page.waitForFunction(() => !document.getElementById('run').disabled, null, { timeout: 180000 });
    assert.equal(await page.locator('#export').isEnabled(), true);
    return JSON.parse(await page.locator('#json').textContent());
  }
  try {
    await page.goto(url);
    await page.waitForFunction(() => document.getElementById('sample').options.length > 1);
    await page.locator('#preview').waitFor({ state: 'visible' });
    await page.waitForFunction(() => document.getElementById('preview').naturalWidth > 0);
    let result = await run();
    assert.equal(result.pipeline.mode, 'mock'); assert.equal(result.status, 'detected');
    assert.equal(await page.locator('.box').count(), 1);
    const bounds = await page.locator('.box').boundingBox();
    const imageBounds = await page.locator('#preview').boundingBox();
    assert.ok(Math.abs(bounds.x - imageBounds.x - imageBounds.width * .25) < 2);
    assert.ok(Math.abs(bounds.width - imageBounds.width * .4) < 2);
    await page.screenshot({ path: path.join(out, 'desktop-mock.png'), fullPage: true });
    await page.locator('#show-boxes').uncheck();
    assert.equal(await page.locator('#boxes').isVisible(), false);
    await page.locator('#show-boxes').check();
    const downloadPromise = page.waitForEvent('download'); await page.locator('#export').click();
    const download = await downloadPromise; await download.saveAs(path.join(out, 'export.json'));
    assert.equal(JSON.parse(fs.readFileSync(path.join(out, 'export.json'))).request_id, result.request_id);
    await page.locator('#scenario').selectOption('empty'); result = await run();
    assert.equal(result.status, 'no_detection'); assert.equal(await page.locator('.box').count(), 0);
    await page.locator('#scenario').selectOption('error'); result = await run(); assert.equal(result.error.stage, 'detect');
    await page.locator('#file').setInputFiles({ name: 'broken.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('broken image') });
    result = await run(); assert.equal(result.error.stage, 'read');
    const sampleRow = JSON.parse(fs.readFileSync(path.join(root, 'data/processed/v2/train.jsonl'), 'utf8').trim().split('\n')[0]);
    await page.locator('#scenario').selectOption('animal');
    await page.locator('#file').setInputFiles(path.join(root, sampleRow.quality.local_path));
    await page.waitForFunction(() => !document.getElementById('run').disabled);
    result = await run(); assert.equal(result.status, 'detected');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(out, 'mobile-mock.png'), fullPage: true });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    const mobileBox = await page.locator('.box').boundingBox();
    const mobileImage = await page.locator('#preview').boundingBox();
    assert.ok(mobileBox.x >= mobileImage.x && mobileBox.x + mobileBox.width <= mobileImage.x + mobileImage.width + 1);
    await page.setViewportSize({ width: 1440, height: 1100 });
    await page.locator('#sample').selectOption('0');
    await page.locator('[data-mode="megadetector"]').click();
    result = await run();
    assert.equal(result.pipeline.mode, 'megadetector'); assert.notEqual(result.status, 'error');
    assert.match(result.pipeline.weights_sha256, /^[a-f0-9]{64}$/);
    await page.screenshot({ path: path.join(out, 'desktop-real.png'), fullPage: true });
    assert.equal(errors.length, 0, errors.join('\n'));
    const report = { passed: true, checked_utc: new Date().toISOString(), url,
      desktop: '1440x1100', mobile: '390x844', browser_errors: errors,
      verified: ['sample preview', 'mock/real separation', 'box geometry', 'upload', 'empty/error', 'toggle', 'JSON export', 'mobile no overflow', 'real detector'],
      real_status: result.status, real_detection_count: result.detections.length };
    fs.writeFileSync(path.join(root, 'reports/tv4_w2/browser_verification.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
