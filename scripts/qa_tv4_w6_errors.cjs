/* Separate QA server with an intentionally invalid candidate package, never real weights. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
 const out=path.resolve(process.env.QA_ERROR_OUTPUT||path.resolve(__dirname,'../outputs/tv4/w6/browser_errors01'));fs.mkdirSync(out,{recursive:false});
 const modelId=process.env.QA_ERROR_MODEL||'DINO_W6_R2';
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(process.env.FAILURE_DEMO_URL||'http://127.0.0.1:8767');
  await page.waitForFunction(()=>document.getElementById('classifier').options.length>=9);
  await page.locator('#classifier').selectOption(modelId);
  await page.locator('#sample').selectOption('0');await page.locator('#run').click();
  await page.waitForFunction(()=>!document.getElementById('run').disabled,null,{timeout:180000});
  const session=JSON.parse(await page.locator('#json').textContent());
  assert.equal(session.original.result.status,'error');assert.equal(session.original.result.error.stage,'classify');
  assert.equal(session.original.result.pipeline.classifier_id,modelId);
  assert.equal(session.original.provenance.classifier,null);assert.equal(session.original.result.detections.length,0);
  assert.equal(await page.locator('#status').getAttribute('class'),'error');
  assert.equal(await page.locator('.box').count(),0);assert.deepEqual(errors,[]);
  await page.screenshot({path:path.join(out,'invalid-checkpoint.png'),fullPage:true});
  fs.writeFileSync(path.join(out,'session.json'),JSON.stringify(session,null,2));
  fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({status:'PASS',errors,verified:['actual invalid-size checkpoint','classify error','no partial boxes','no silent fallback']},null,2));
  console.log('W6 actual model-error UI PASS');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
