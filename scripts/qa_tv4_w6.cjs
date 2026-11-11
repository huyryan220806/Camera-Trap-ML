/* Real candidate UI/API smoke, plus existing saved-review/batch/CSV regressions. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const url=process.env.DEMO_URL||'http://127.0.0.1:8766';
const out=path.resolve(process.env.QA_OUTPUT||path.join(root,'outputs/tv4/w6/browser01'));
const runs=(process.env.QA_MODEL_RUNS||'R2,R1,R3,R4').split(',');
const activeRun=runs[0],activeModel='DINO_W6_'+activeRun;
const activeDataset=activeRun==='R6'?'train_expansion_w6_v1':'comparison_v1';
fs.mkdirSync(out,{recursive:false});
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1440,height:1100},acceptDownloads:true});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 const current=async()=>JSON.parse(await page.locator('#json').textContent());
 async function run(){await page.locator('#run').click();await page.waitForFunction(()=>!document.getElementById('run').disabled,null,{timeout:180000});return current();}
 async function save(){await page.locator('#save-review').click();await page.waitForFunction(()=>document.getElementById('review-revision').textContent==='Bản 1');return current();}
 try{
  await page.goto(url);await page.waitForFunction(()=>document.getElementById('classifier').options.length>=9);
  assert.equal(await page.locator('#classifier').inputValue(),'B2');
  assert.equal(await page.locator('#classifier option[value="DINO_W6_R5"]').count(),0);
  const config=await(await page.request.get(url+'/api/config')).json();assert.ok(config.samples.length);
  await page.locator('#sample').selectOption(config.samples[0].id);
  const sessions={};
  for(const runId of runs){
   const modelId='DINO_W6_'+runId;await page.locator('#classifier').selectOption(modelId);
   let session=await run();assert.notEqual(session.original.result.status,'error');
   assert.equal(session.original.result.pipeline.classifier_id,modelId);
   assert.equal(session.runtime.classifier_image_size,256);
   assert.match(await page.locator('#model-context').innerText(),new RegExp(runId==='R6'?'train_expansion_w6_v1':'comparison_v1'));
   assert.match(await page.locator('#model-context').innerText(),new RegExp(runId+'_attempt01'));
   assert.match(await page.locator('#model-context').innerText(),/CPU/);
   assert.ok(session.original.result.detections.every(d=>d.top_k.length===3));
   const original=structuredClone(session.original);
   await page.locator('#reviewer').fill('TV4 W6 QA');
   await page.locator('#review-label').selectOption('unresolved');
   await page.locator('#image-outcome').selectOption('unresolved');
   await page.locator('#review-note').fill('W6 QA only; not expert labels.');
   session=await save();assert.deepEqual(session.original,original);
   await page.locator('#reload-review').click();await page.waitForFunction(()=>document.getElementById('review-status').textContent==='Đã lưu trên máy');
   assert.deepEqual(await current(),session);
   const conflict=await page.request.post(url+'/api/review',{data:{request_id:session.request_id,...session.review,revision:0}});assert.equal(conflict.status(),409);
   const download=page.waitForEvent('download');await page.locator('#export').click();await(await download).saveAs(path.join(out,runId+'-review.json'));
   assert.deepEqual(JSON.parse(fs.readFileSync(path.join(out,runId+'-review.json'),'utf8')),session);
   sessions[runId]={request_id:session.request_id,model:session.original.provenance.classifier};
  }
  // Switching models evicts the capacity1 candidate, while B2 and W5 remain runnable.
  for(const modelId of ['B2','DINOv3_LP_run01',activeModel]){
   await page.locator('#classifier').selectOption(modelId);const s=await run();
   assert.notEqual(s.original.result.status,'error');assert.equal(s.original.result.pipeline.classifier_id,modelId);
  }
  for(const [width,height,name] of [[1440,1100,'desktop'],[390,844,'mobile'],[320,740,'narrow']]){
   await page.setViewportSize({width,height});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert.equal(await page.getByRole('button',{name:'Xuất JSON phiên đã lưu',exact:true}).count(),1);
   const image=await page.locator('#preview').boundingBox();
   for(const box of await page.locator('.box').all()){
    const b=await box.boundingBox();assert.ok(b.x>=image.x-1&&b.y>=image.y-1&&b.x+b.width<=image.x+image.width+1&&b.y+b.height<=image.y+image.height+1);
   }
   await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});
  }
  // One real W6 batch with duplicate image names and a corrupt image between.
  const train=JSON.parse(fs.readFileSync(path.join(root,'data/processed/comparison_v1/train.jsonl'),'utf8').split('\n')[0]);
  const good={name:'same.jpg',mimeType:'image/jpeg',buffer:fs.readFileSync(path.join(root,train.quality.local_path))};
  await page.locator('#batch-files').setInputFiles([good,{name:'bad.jpg',mimeType:'image/jpeg',buffer:Buffer.from('bad')},good]);
  await page.locator('#batch-run').click();await page.waitForFunction(()=>document.getElementById('batch-status').textContent.startsWith('3/3'),null,{timeout:180000});
  await page.locator('#batch-queue button').nth(1).click();assert.equal((await current()).original.result.status,'error');assert.equal(await page.locator('#image-frame').isVisible(),false);
  await page.locator('#batch-queue button').nth(0).click();const first=await current();
  await page.locator('#reviewer').fill('TV4 W6 QA');await page.locator('#review-label').selectOption('unresolved');
  await page.locator('#review-note').fill('=SUM(1,2)\n"Tiếng Việt"');
  await page.locator('#batch-queue button').nth(2).click();assert.notEqual((await current()).request_id,first.request_id);
  await page.locator('#batch-queue button').nth(0).click();assert.equal(await page.locator('#review-note').inputValue(),'=SUM(1,2)\n"Tiếng Việt"');
  let download=page.waitForEvent('download');await page.locator('#batch-csv').click();await(await download).saveAs(path.join(out,'draft-excluded.csv'));
  assert.ok(!fs.readFileSync(path.join(out,'draft-excluded.csv'),'utf8').includes('SUM(1,2)'));
  await save();download=page.waitForEvent('download');await page.locator('#batch-csv').click();await(await download).saveAs(path.join(out,'saved.csv'));
  const csv=fs.readFileSync(path.join(out,'saved.csv'),'utf8');assert.ok(csv.includes("'=SUM(1,2)"));assert.ok(csv.includes(activeRun+'_attempt01'));assert.ok(csv.includes(activeDataset));
  download=page.waitForEvent('download');await page.locator('#batch-json').click();await(await download).saveAs(path.join(out,'batch.json'));
  const batch=JSON.parse(fs.readFileSync(path.join(out,'batch.json'),'utf8'));assert.deepEqual(batch.items[0].session.original,first.original);
  await page.locator('[data-mode="mock"]').click();
  for(const scenario of ['multiple','empty','error']){
   await page.locator('#scenario').selectOption(scenario);await page.locator('#sample').selectOption(config.samples[0].id);
   const s=await run();assert.equal(s.original.result.status,scenario==='multiple'?'needs_review':scenario==='empty'?'no_detection':'error');
   if(scenario==='multiple')assert.equal(s.original.result.detections.length,2);
   if(scenario==='empty'){
    await page.locator('#reviewer').fill('TV4 W6 QA');await page.locator('#image-outcome').selectOption('detector_miss');
    await page.locator('#review-note').fill('QA synthetic missed animal at left');assert.equal((await save()).review.image_outcome,'detector_miss');
   }
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({status:'PASS',errors,sessions,
    verified:['real '+runs.join(','),'B2/W5 preserved','default B2','R5 excluded','per-box top3','save/reload/export/409',
     'model/dataset/version context','3viewport/boxes/a11y','real W6 mixed batch','saved-only CSV/formula/UTF8',
     'original immutable','mock multiple/empty/detector error/miss']},null,2));
  console.log('W6 browser QA PASS');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
