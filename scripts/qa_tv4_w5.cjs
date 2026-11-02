/* Run against an explicitly configured candidate server; creates QA-only reviews. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {batchCsv} = require('../app/batch.js');
const root = path.resolve(__dirname, '..');
const out = path.resolve(process.env.QA_OUTPUT || path.join(root, 'outputs/tv4/w5/browser_attempt01'));
const url = process.env.DEMO_URL || 'http://127.0.0.1:8766';
fs.mkdirSync(out, {recursive: false});
const fixture = {name: 'qa-landscape.png', mimeType: 'image/png',
  buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=', 'base64')};
// CSV quoting, Unicode and formula neutralization are independent of the browser.
const csvProbe = batchCsv([{id:'qa', name:'=SUM(1,2)', status:'request_error', error:'Tiếng Việt,"quoted"\nnew line'}]);
assert.ok(csvProbe.startsWith('\uFEFF'));
assert.ok(csvProbe.includes('"\'=SUM(1,2)"'));
assert.ok(csvProbe.includes('"Tiếng Việt,""quoted""\nnew line"'));

(async () => {
  const browser = await chromium.launch({headless:true, channel:'msedge'});
  const page = await browser.newPage({viewport:{width:1440,height:1100},acceptDownloads:true});
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  const current = async () => JSON.parse(await page.locator('#json').textContent());
  async function run() {
    await page.locator('#run').click();
    await page.waitForFunction(() => !document.getElementById('run').disabled, null, {timeout:180000});
    return current();
  }
  async function screenshot(name,width,height) {
    await page.setViewportSize({width,height});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert.equal(await page.getByRole('button',{name:'Xuất JSON phiên đã lưu',exact:true}).count(),1);
    const image = await page.locator('#preview').boundingBox();
    if (image) for (const box of await page.locator('.box').all()) {
      const b = await box.boundingBox();
      assert.ok(b.x >= image.x-1 && b.y >= image.y-1 && b.x+b.width <= image.x+image.width+1 && b.y+b.height <= image.y+image.height+1);
    }
    await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});
  }
  try {
    await page.goto(url);
    await page.waitForFunction(() => document.getElementById('classifier').options[3].disabled === false);
    assert.equal(await page.locator('#classifier').inputValue(),'B2');
    const config = await (await page.request.get(url+'/api/config')).json();
    assert.ok(config.samples.length, 'Install a hash-verified original train image first');
    await page.locator('#sample').selectOption(config.samples[0].id);
    await page.locator('#classifier').selectOption('DINOv3_LP_run01');
    const timings = [];
    let real;
    for (let i=0;i<4;i++) {
      const started = Date.now(); real = await run();
      assert.notEqual(real.original.result.status,'error');
      assert.equal(real.original.provenance.classifier.classifier_id,'DINOv3_LP_run01');
      assert.equal(real.original.provenance.classifier.checkpoint_sha256,'acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3');
      timings.push({phase:i?'warm':'cold',client_click_to_enabled_ms:Date.now()-started,
        inference_wall_ms:real.inference_wall_ms, crop_count:real.original.result.detections.length,
        cache_hit:real.original.provenance.classifier.cache_hit});
    }
    const original = structuredClone(real.original);
    await page.locator('#reviewer').fill('TV4 QA');
    const old = original.result.detections[0].top_k[0].label;
    await page.locator('#review-label').selectOption(old === 'sambar' ? 'masked_palm_civet' : 'sambar');
    await page.locator('#review-note').fill('QA only: "Unicode tiếng Việt",\nnot expert labels');
    await page.locator('#save-review').click();
    await page.waitForFunction(() => document.getElementById('review-revision').textContent === 'Bản 1');
    real = await current(); assert.deepEqual(real.original, original);
    await page.locator('#reload-review').click();
    await page.waitForFunction(() => document.getElementById('review-status').textContent === 'Đã lưu trên máy');
    const stale = await page.request.post(url+'/api/review',{data:{request_id:real.request_id,...real.review,revision:0}});
    assert.equal(stale.status(),409);
    const downloaded = page.waitForEvent('download');
    await page.locator('#export').click();
    await (await downloaded).saveAs(path.join(out,'real-review.json'));
    assert.deepEqual(JSON.parse(fs.readFileSync(path.join(out,'real-review.json'),'utf8')),real);
    await screenshot('dino-desktop',1440,1100);
    await screenshot('dino-mobile',390,844);
    await screenshot('dino-narrow',320,740);

    // Queue: duplicate names remain distinct, corrupt file does not stop next image.
    await page.setViewportSize({width:1440,height:1100});
    await page.locator('[data-mode="mock"]').click();
    await page.locator('#scenario').selectOption('multiple');
    const train = JSON.parse(fs.readFileSync(path.join(root,'data/processed/comparison_v1/train.jsonl'),'utf8').split('\n')[0]);
    const good = {name:'same.jpg',mimeType:'image/jpeg',buffer:fs.readFileSync(path.join(root,train.quality.local_path))};
    await page.locator('#batch-files').setInputFiles([good,{name:'bad.jpg',mimeType:'image/jpeg',buffer:Buffer.from('bad')},good]);
    await page.locator('#batch-run').click();
    await page.waitForFunction(() => document.getElementById('batch-status').textContent.startsWith('3/3'),null,{timeout:180000});
    assert.equal(await page.locator('#batch-queue button').count(),3);
    await page.locator('#batch-queue button').nth(1).click();
    assert.equal((await current()).original.result.status,'error');
    assert.equal(await page.locator('#image-frame').isVisible(),false);
    await page.locator('#batch-queue button').nth(0).click();
    const first = await current();
    assert.equal(first.original.result.detections.length,2);
    await page.locator('#reviewer').fill('TV4 QA');
    await page.locator('#review-label').selectOption('unresolved');
    await page.locator('#review-note').fill('=SUM(1,2)\n"chưa lưu"');
    await page.locator('#batch-queue button').nth(2).click();
    assert.notEqual((await current()).request_id, first.request_id);
    await page.locator('#batch-queue button').nth(0).click();
    assert.equal(await page.locator('#review-note').inputValue(),'=SUM(1,2)\n"chưa lưu"');
    assert.equal(await page.locator('#review-label').inputValue(),'unresolved');
    assert.match(await page.locator('#review-status').innerText(), /chưa lưu/);
    let promise = page.waitForEvent('download'); await page.locator('#batch-csv').click();
    await (await promise).saveAs(path.join(out,'before-save.csv'));
    assert.ok(!fs.readFileSync(path.join(out,'before-save.csv'),'utf8').includes('SUM(1,2)'));
    await page.locator('#save-review').click();
    await page.waitForFunction(() => document.getElementById('review-revision').textContent === 'Bản 1');
    promise = page.waitForEvent('download'); await page.locator('#batch-csv').click();
    await (await promise).saveAs(path.join(out,'after-save.csv'));
    assert.ok(fs.readFileSync(path.join(out,'after-save.csv'),'utf8').includes("'=SUM(1,2)"));
    promise = page.waitForEvent('download'); await page.locator('#batch-json').click();
    await (await promise).saveAs(path.join(out,'batch.json'));
    const batch = JSON.parse(fs.readFileSync(path.join(out,'batch.json'),'utf8'));
    assert.equal(batch.items[0].session.review.revision,1);
    assert.equal(batch.items[0].session.review.box_reviews.length,2);
    assert.deepEqual(batch.items[0].session.original,first.original);
    await screenshot('batch-desktop',1440,1100);
    await screenshot('batch-mobile',390,844);
    await screenshot('batch-narrow',320,740);
    // Over-limit selection preserves current results; pause/resume leaves waiting files intact.
    await page.locator('#batch-files').setInputFiles(Array.from({length:11},()=>good));
    assert.match(await page.locator('#batch-status').innerText(), /Tối đa 10/);
    assert.equal(await page.locator('#batch-queue button').count(),3);
    page.once('dialog', dialog=>dialog.accept());
    await page.locator('#batch-files').setInputFiles([good,good,good]);
    await page.route('**/api/analyze', async route => {
      await new Promise(resolve=>setTimeout(resolve,250));
      await route.continue();
    });
    await page.locator('#batch-run').click();
    await page.locator('#batch-stop').click();
    await page.waitForFunction(() => !document.getElementById('batch-run').disabled);
    assert.match(await page.locator('#batch-status').innerText(), /1\/3/);
    await page.unroute('**/api/analyze');
    await page.locator('#batch-run').click();
    await page.waitForFunction(() => document.getElementById('batch-status').textContent.startsWith('3/3'));
    // Explicit empty and detector error scenarios preserve distinct states.
    await page.locator('#scenario').selectOption('empty'); await page.locator('#sample').selectOption(config.samples[0].id);
    assert.equal((await run()).original.result.status,'no_detection');
    await page.locator('#scenario').selectOption('error');
    assert.equal((await run()).original.result.error.stage,'detect');
    if (process.env.FAILURE_DEMO_URL) {
      await page.goto(process.env.FAILURE_DEMO_URL);
      await page.waitForFunction(() => !document.getElementById('classifier').options[3].disabled);
      await page.locator('#classifier').selectOption('DINOv3_LP_run01');
      const failed = await run();
      assert.equal(failed.original.result.status,'error');
      assert.equal(failed.original.result.error.stage,'classify');
      assert.equal(failed.original.result.pipeline.classifier_id,'DINOv3_LP_run01');
      assert.equal(failed.original.result.detections.length,0);
      assert.equal(await page.locator('#status').getAttribute('class'),'error');
      await page.screenshot({path:path.join(out,'dino-model-error.png'),fullPage:true});
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({status:'PASS',errors,timings,runtime:real.runtime,
      verified:['B2 default','explicit real MD+DINO','saved correction/reload/export','409 rejects stale revision',
      'mobile accessible export name','per-box mock multiple','mixed batch continues','duplicate names','draft preserved',
      'CSV saved-only/formula/quoting/UTF8','batch JSON original immutable','10-file cap','stop/resume',
      'empty/detector error','3 viewports',...(process.env.FAILURE_DEMO_URL ? ['invalid real checkpoint UI error/no fallback'] : [])],
      real_request_id:real.request_id},null,2));
    console.log('W5 browser QA PASS');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
