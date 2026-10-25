const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'outputs/tv4/w4/browser');
fs.mkdirSync(out, {recursive:true});
const url = process.env.DEMO_URL || 'http://127.0.0.1:8765';
(async () => {
  const browser = await chromium.launch({headless:true, channel:'msedge'});
  const page = await browser.newPage({viewport:{width:1440,height:1100}, acceptDownloads:true});
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  const current = async () => JSON.parse(await page.locator('#json').textContent());
  async function run() {
    await page.locator('#run').click();
    await page.waitForFunction(() => !document.getElementById('run').disabled, null, {timeout:180000});
    return current();
  }
  async function save(revision) {
    await page.locator('#save-review').click();
    await page.waitForFunction(r => document.getElementById('review-revision').textContent === `Bản ${r}`, revision);
    return current();
  }
  async function screenshot(name,width,height) {
    await page.setViewportSize({width,height});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const invalid = await page.locator('.review-grid input:not([type=checkbox]),.review-grid select,#review-note').evaluateAll(nodes => nodes.some(n => {
      const r=n.getBoundingClientRect(); return r.width < 40 || r.right > innerWidth + 1 || r.left < 0;
    }));
    assert.equal(invalid,false);
    const image = await page.locator('#preview').boundingBox();
    assert.ok(image.width > 100 && image.height > 40);
    for (const box of await page.locator('.box').all()) {
      const b=await box.boundingBox();
      assert.ok(b.x >= image.x-1 && b.y >= image.y-1 && b.x+b.width <= image.x+image.width+1 && b.y+b.height <= image.y+image.height+1);
    }
    await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});
  }
  try {
    await page.goto(url);
    await page.waitForFunction(() => document.getElementById('sample').options.length > 1);
    assert.equal(await page.locator('#classifier').inputValue(),'B2');
    let real = await run();
    assert.equal(real.schema_version,'review-session-1.0');
    assert.equal(real.original.provenance.classifier.classifier_id,'B2');
    assert.ok(real.original.result.detections.length > 0);
    assert.equal(real.runtime.classifier_max_crop_batch_size,8);
    const original = structuredClone(real.original);
    await page.locator('#reviewer').fill('TV1 - QA');
    const old = original.result.detections[0].top_k[0].label;
    const corrected = old === 'sambar' ? 'masked_palm_civet' : 'sambar';
    await page.locator('#review-label').selectOption(corrected);
    await page.locator('#review-note').fill('QA correction only; not a ground-truth adjudication.');
    real=await save(1);
    assert.deepEqual(real.original,original);
    assert.equal(real.review.box_reviews[0].decision,'corrected');
    const reloaded=await (await page.request.get(url+'/api/review/'+real.request_id)).json();
    assert.deepEqual(reloaded,real);
    await screenshot('desktop-real-reviewed',1440,1100);
    await screenshot('mobile-real-reviewed',390,844);
    await screenshot('mobile-narrow-reviewed',320,740);
    const downloadPromise=page.waitForEvent('download');
    await page.locator('#export').click();
    await (await downloadPromise).saveAs(path.join(out,'review-export.json'));
    assert.deepEqual(JSON.parse(fs.readFileSync(path.join(out,'review-export.json'),'utf8')),real);
    await page.setViewportSize({width:1440,height:1100});
    await page.locator('[data-mode="mock"]').click();
    assert.equal(await page.locator('#review-panel').isVisible(),false);
    await page.locator('#scenario').selectOption('multiple');
    let multiple=await run();
    assert.equal(multiple.original.result.status,'needs_review');
    await page.locator('#review-only').check();
    assert.equal(await page.locator('#review-box option').count(),2);
    await page.locator('#review-label').selectOption('unresolved');
    await page.locator('#image-outcome').selectOption('unresolved');
    multiple=await save(1);
    assert.equal(multiple.review.box_reviews[0].label,null);
    assert.equal(multiple.review.box_reviews[0].decision,'unresolved');
    await page.locator('#scenario').selectOption('empty');
    let empty=await run();
    assert.equal(empty.original.result.status,'no_detection');
    assert.equal(empty.review.image_outcome,'pending');
    assert.equal(await page.locator('#review-label').isDisabled(),true);
    await page.locator('#image-outcome').selectOption('detector_miss');
    await page.locator('#review-note').fill('Synthetic missing-box UI test: animal at left edge.');
    empty=await save(1);
    assert.equal(empty.review.image_outcome,'detector_miss');
    assert.equal(empty.original.result.status,'no_detection');
    await page.locator('#file').setInputFiles({name:'bad.jpg',mimeType:'image/jpeg',buffer:Buffer.from('invalid')});
    const bad=await run();
    assert.equal(bad.original.result.error.stage,'read');
    await page.locator('#sample').selectOption('0');
    await page.locator('#scenario').selectOption('multiple');
    await run();
    await screenshot('desktop-multiple',1440,1100);
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({status:'PASS',url,errors,
      verified:['real MD+B2','per-box human correction','original immutable','GET persistence','JSON export',
        'low-score review','unresolved is not novel species','mock detector miss','corrupt image',
        'desktop/mobile/narrow layout','runtime and batch sizes'],real_request_id:real.request_id},null,2));
    console.log('TV4 W4 browser QA PASS');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
