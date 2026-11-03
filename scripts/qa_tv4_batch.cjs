const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async()=>{
  const root = path.resolve(__dirname,'..');
  const out = path.join(root,'outputs/tv4/w5/batch_final');
  fs.mkdirSync(out,{recursive:false});
  const browser = await chromium.launch({headless:true,channel:'msedge'});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844}});
    const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(process.env.DEMO_URL || 'http://127.0.0.1:8766');
    await page.waitForFunction(()=>document.getElementById('sample').options.length>1);
    await page.locator('[data-mode="mock"]').click();
    await page.locator('#scenario').selectOption('multiple');
    const row=JSON.parse(fs.readFileSync(path.join(root,'data/processed/comparison_v1/train.jsonl'),'utf8').split('\n')[0]);
    const good={name:'same.jpg',mimeType:'image/jpeg',buffer:fs.readFileSync(path.join(root,row.quality.local_path))};
    await page.locator('#batch-files').setInputFiles([good,{name:'bad.jpg',mimeType:'image/jpeg',buffer:Buffer.from('bad')},good]);
    await page.locator('#batch-run').click();
    await page.waitForFunction(()=>document.getElementById('batch-status').textContent.startsWith('3/3'));
    await page.locator('#batch-queue button').nth(0).click();
    await page.locator('#reviewer').fill('TV4 QA');
    await page.locator('#review-note').fill('Bản nháp giữ riêng');
    await page.locator('#review-label').selectOption('unresolved');
    await page.locator('#batch-queue button').nth(1).click();
    assert.equal(await page.locator('#image-frame').isVisible(),false);
    assert.equal(JSON.parse(await page.locator('#json').textContent()).original.result.error.stage,'read');
    await page.locator('#batch-queue button').nth(2).click();
    assert.equal(await page.locator('#image-frame').isVisible(),true);
    await page.locator('#batch-queue button').nth(0).click();
    assert.equal(await page.locator('#review-note').inputValue(),'Bản nháp giữ riêng');
    assert.equal(await page.locator('#review-label').inputValue(),'unresolved');
    await page.locator('[data-mode="megadetector"]').click();
    await page.locator('#batch-queue button').nth(0).click();
    assert.match(await page.locator('#mode-badge').innerText(),/GIẢ LẬP/);
    assert.equal(await page.locator('#review-note').inputValue(),'Bản nháp giữ riêng');
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    assert.deepEqual(errors,[]);
    await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
    fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({status:'PASS',errors,
      verified:['corrupt item hides stale preview','good item restores preview','draft isolation',
        'saved result restores correct mode badge','mobile overflow']},null,2));
    console.log('Final batch regression PASS');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
