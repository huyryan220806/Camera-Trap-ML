// Real local API/UI acceptance for available, verified classifiers.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const out = path.resolve(root, process.env.QA_OUTPUT || 'outputs/tv4/w3/browser');
fs.mkdirSync(out, { recursive: true });
const url = process.env.DEMO_URL || 'http://127.0.0.1:8765';
(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, acceptDownloads: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  async function run() {
    await page.locator('#run').click();
    await page.waitForFunction(() => !document.getElementById('run').disabled, null, { timeout: 180000 });
    assert.equal(await page.locator('#export').isEnabled(), true);
    return JSON.parse(await page.locator('#json').textContent());
  }
  async function layout(width, height, name) {
    await page.setViewportSize({ width, height });
    await page.locator('#results').scrollIntoViewIfNeeded();
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const img = await page.locator('#preview').boundingBox();
    assert.ok(img.width > 100 && img.height > 40);
    for (const box of await page.locator('.box').all()) {
      const b = await box.boundingBox();
      assert.ok(b.x >= img.x - 1 && b.y >= img.y - 1 && b.x + b.width <= img.x + img.width + 1 && b.y + b.height <= img.y + img.height + 1);
    }
    const badText = await page.locator('.predictions li').evaluateAll(items => items.filter(item => {
      const [label, score] = item.children;
      const a = label.getBoundingClientRect(), b = score.getBoundingClientRect();
      return a.right > b.left || label.scrollWidth > label.clientWidth + 1;
    }).length);
    assert.equal(badText, 0);
    await page.screenshot({ path: path.join(out, name + '.png'), fullPage: true });
  }
  try {
    await page.goto(url);
    await page.waitForFunction(() => document.getElementById('sample').options.length > 1);
    await page.waitForFunction(() => document.getElementById('preview').naturalWidth > 0);
    assert.equal(await page.locator('#classifier').inputValue(), 'B0');
    const availability = (await (await page.request.get(url + '/api/config')).json()).classifiers;
    for (const model of ['B1', 'B2']) {
      if (process.env['REQUIRE_' + model] === '1') {
        assert.equal(availability[model].enabled && availability[model].checkpoint_present, true);
      }
      assert.equal(await page.locator(`#classifier option[value="${model}"]`).isDisabled(),
        !(availability[model].enabled && availability[model].checkpoint_present));
    }
    let cold = await run();
    assert.equal(cold.schema_version, 'classifier-demo-1.0');
    assert.equal(cold.result.pipeline.mode, 'inference');
    assert.equal(cold.provenance.classifier.classifier_id, 'B0');
    assert.equal(cold.provenance.scores_calibrated, false);
    assert.equal(cold.result.detections[0].top_k.length, 3);
    const warm = await run();
    assert.equal(warm.provenance.classifier.cache_hit, true);
    assert.equal(warm.provenance.classifier.model_load_count, cold.provenance.classifier.model_load_count);
    assert.deepEqual(cold.result.detections, warm.result.detections);
    await layout(1440, 1100, 'desktop-real');
    await layout(390, 844, 'mobile-real');
    await layout(320, 740, 'mobile-narrow');
    await page.setViewportSize({ width: 1440, height: 1100 });
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#export').click();
    const download = await downloadPromise;
    await download.saveAs(path.join(out, 'export.json'));
    assert.equal(JSON.parse(fs.readFileSync(path.join(out, 'export.json'))).provenance.scores_calibrated, false);
    const models = { B0: { sha256: cold.provenance.classifier.checkpoint_sha256, warm_cache: true } };
    for (const model of ['B1', 'B2']) {
      if (!(availability[model].enabled && availability[model].checkpoint_present)) continue;
      const prefix = model.toLowerCase();
      await page.locator('#classifier').selectOption(model);
      assert.equal(await page.locator('#export').isDisabled(), true);
      const b1 = await run(), b1Warm = await run();
      assert.equal(b1.provenance.classifier.classifier_id, model);
      assert.equal(b1.result.detections[0].top_k.length, 3);
      assert.equal(b1Warm.provenance.classifier.cache_hit, true);
      assert.equal(b1Warm.provenance.classifier.model_load_count, b1.provenance.classifier.model_load_count);
      assert.deepEqual(b1.result.detections, b1Warm.result.detections);
      if (model === 'B1') assert.ok(b1.provenance.warnings.some(text => text.includes('distribution shift')));
      await layout(1440, 1100, 'desktop-' + prefix);
      await layout(390, 844, 'mobile-' + prefix);
      await layout(320, 740, 'mobile-narrow-' + prefix);
      const b1DownloadPromise = page.waitForEvent('download');
      await page.locator('#export').click();
      await (await b1DownloadPromise).saveAs(path.join(out, prefix + '-export.json'));
      const exported = JSON.parse(fs.readFileSync(path.join(out, prefix + '-export.json')));
      assert.equal(exported.provenance.classifier.classifier_id, model);
      assert.equal(exported.provenance.scores_calibrated, false);
      assert.equal(exported.provenance.classifier.checkpoint_sha256, b1.provenance.classifier.checkpoint_sha256);
      models[model] = { sha256: b1.provenance.classifier.checkpoint_sha256, warm_cache: true };
      await page.setViewportSize({ width: 1440, height: 1100 });
    }
    await page.locator('[data-mode="mock"]').click();
    assert.equal(await page.locator('#export').isDisabled(), true);
    await page.locator('#scenario').selectOption('multiple');
    let result = await run();
    assert.equal(result.result.pipeline.classifier_id, 'mock-scores-v1');
    assert.equal(await page.locator('.box').count(), 2);
    assert.equal(await page.locator('.predictions li').count(), 6);
    await layout(1440, 1100, 'desktop-multiple');
    await layout(390, 844, 'mobile-multiple');
    await page.locator('#show-boxes').uncheck();
    assert.equal(await page.locator('#boxes').isVisible(), false);
    await page.locator('#show-boxes').check();
    await page.locator('#scenario').selectOption('empty');
    result = await run();
    assert.equal(result.result.status, 'no_detection');
    assert.equal(await page.locator('.predictions li').count(), 0);
    await page.locator('#scenario').selectOption('error');
    result = await run();
    assert.equal(result.result.error.stage, 'detect');
    await page.locator('#file').setInputFiles({ name: 'broken.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('bad image') });
    result = await run();
    assert.equal(result.result.error.stage, 'read');
    await page.locator('#sample').selectOption('0');
    await page.locator('#scenario').selectOption('animal');
    await page.locator('#classifier').selectOption('none');
    result = await run();
    assert.equal(result.schema_version, 'detector-demo-1.0');
    assert.equal(result.status, 'detected');
    assert.equal(errors.length, 0, errors.join('\n'));
    const report = { passed: true, checked_utc: new Date().toISOString(), url,
      viewport_sizes: ['1440x1100', '390x844', '320x740'], browser_errors: errors, models,
      real_box_count: cold.result.detections.length, classifier_load_count: warm.provenance.classifier.model_load_count,
      verified: ['real MD+B0', ...['B1', 'B2'].filter(model => models[model]).map(model => `real MD+${model} and JSON export`),
        'warm cache', 'top 3 per box', 'uncalibrated score disclosure',
        'explicit multiple-box mock', 'JSON provenance export', 'empty/read/detector errors',
        'legacy detector-only', 'model selection clears results', 'availability follows registry',
        'desktop/mobile no overflow', 'box alignment', 'no text-score overlap'] };
    fs.writeFileSync(path.join(out, 'verification.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
