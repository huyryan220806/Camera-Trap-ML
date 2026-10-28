"""Independent API review of an exact TV4 snapshot; browser checks remain separate.

Requires a loopback review server launched from the recorded PR snapshot. Uses
train samples and explicitly labelled synthetic scenarios, never Test rasters.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import requests


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8766')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path,help='Launch isolated snapshot server in the same network context')
    parser.add_argument('--commit',default='fef2511b571b23be3d4e2cf6c1ccedd659097b6f')
    args=parser.parse_args()
    assert args.url.startswith('http://127.0.0.1:'), 'Local isolated server only'
    args.output.mkdir(parents=True,exist_ok=False)
    server=None
    if args.snapshot:
        root=Path(__file__).resolve().parents[1]
        snapshot=args.snapshot.resolve()
        assert snapshot.is_relative_to(root/'outputs')
        pinned={}
        for name in ('app/index.html','app/app.js','app/review.js','app/style.css','scripts/run_demo.py',
                     'src/demo/inference.py','src/demo/classifier.py','src/demo/detector.py','src/demo/review.py',
                     'configs/demo_classifiers.json'):
            expected=subprocess.check_output(['git','show',f'{args.commit}:{name}'],cwd=root)
            actual=(snapshot/name).read_bytes()
            assert actual.replace(b'\r\n',b'\n')==expected.replace(b'\r\n',b'\n'), 'Snapshot code mismatch: '+name
            pinned[name]=dict(git_content_sha256=hashlib.sha256(expected).hexdigest(),
                              archive_sha256=hashlib.sha256(actual).hexdigest(),
                              exact_bytes=actual==expected,only_crlf_conversion=actual!=expected)
        log=(args.output/'server.log').open('x',encoding='utf-8')
        server=subprocess.Popen([sys.executable,'-u','-X','utf8',str(snapshot/'scripts/run_demo.py'),
                                '--port',args.url.rsplit(':',1)[1]],cwd=snapshot,stdout=log,stderr=subprocess.STDOUT)
        with (args.output/'snapshot.json').open('x',encoding='utf-8') as f:json.dump(dict(commit=args.commit,sha256=pinned),f,indent=2)
        import atexit
        def stop():
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=10)
            log.close()
        atexit.register(stop)
    checks=[]
    def save(name,data):
        with (args.output/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
    def check(name,condition,actual=None):
        row=dict(test_case=name,status='PASS' if condition else 'FAIL',actual=actual)
        checks.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
        save('checks_in_progress_'+str(len(checks)),checks)
        assert condition, name
    http=requests.Session(); http.trust_env=False
    if server:
        deadline=time.monotonic()+30
        while True:
            assert server.poll() is None,'Review server exited; see server.log'
            try:
                config=http.get(args.url+'/api/config',timeout=2)
                break
            except requests.ConnectionError:
                if time.monotonic()>deadline:raise
                time.sleep(.2)
    else:config=http.get(args.url+'/api/config',timeout=30)
    config.raise_for_status(); config=config.json();save('config',config)
    check('API-01 B2 weights and train samples',config['classifiers']['B2']['checkpoint_present'] and len(config['samples'])==8)
    real=[]
    for phase in ('cold','warm'):
        clock=time.perf_counter()
        response=http.post(args.url+'/api/analyze',json=dict(sample_id=config['samples'][0]['id'],mode='megadetector',
                           classifier='B2',threshold=.2,review_threshold=.7),timeout=180)
        response.raise_for_status(); data=response.json();save('real_'+phase,{k:v for k,v in data.items() if k!='preview'})
        session=data['review_session']; original=session['original']; result=original['result']
        check('API-02 '+phase+' real B2 no fallback',result['status'] in ('ok','needs_review') and
              original['provenance']['classifier']['classifier_id']=='B2' and result['pipeline']['mode']=='inference',
              dict(status=result['status'],detections=len(result['detections'])))
        check('API-03 '+phase+' top3 and detection IDs',bool(result['detections']) and
              all(len(d['top_k'])==3 and len({p['class_id'] for p in d['top_k']})==3 for d in result['detections']) and
              {d['detection_id'] for d in result['detections']}=={d['detection_id'] for d in session['review']['box_reviews']})
        check('API-04 '+phase+' calibrated score wording',original['provenance']['scores_calibrated'] is False and
              original['provenance']['training_overlap_swg'] is True)
        real.append(dict(phase=phase,request_id=session['request_id'],http_wall_seconds=time.perf_counter()-clock,
                         inference_wall_ms=session['inference_wall_ms'],runtime=session['runtime'],
                         classifier_cache_hit=original['provenance']['classifier']['cache_hit'],
                         timing_scope=session['timing_scope']))
    session=data['review_session']; original=copy.deepcopy(session['original'])
    payload=copy.deepcopy(session['review']); payload.update(request_id=session['request_id'],operator='TV2 independent API QA',
              note='Synthetic human correction for software QA only; not expert ground truth.',image_outcome='unresolved')
    for box in payload['box_reviews']:
        box.update(decision='corrected',label='sambar' if original['result']['detections'][0]['top_k'][0]['label']!='sambar' else 'masked_palm_civet')
    response=http.post(args.url+'/api/review',json=payload,timeout=30);response.raise_for_status();reviewed=response.json();save('reviewed_session',reviewed)
    loaded=http.get(args.url+'/api/review/'+session['request_id'],timeout=30).json();save('reloaded_session',loaded)
    check('API-05 revision persisted; original immutable',reviewed==loaded and loaded['original']==original and loaded['review']['revision']==1)
    stale=http.post(args.url+'/api/review',json=payload,timeout=30)
    check('API-06 stale revision rejected',stale.status_code==409,stale.status_code)
    for scenario in ('multiple','empty','error'):
        response=http.post(args.url+'/api/analyze',json=dict(sample_id=config['samples'][0]['id'],mode='mock',classifier='B2',
                      scenario=scenario,threshold=.2,review_threshold=.7),timeout=30)
        response.raise_for_status();data=response.json();save('synthetic_'+scenario,{k:v for k,v in data.items() if k!='preview'})
        result=data['result'];session=data['review_session']
        expected={'multiple':'needs_review','empty':'no_detection','error':'error'}[scenario]
        check('API-07 labelled synthetic '+scenario,result['status']==expected and result['pipeline']['mode']=='mock',
              dict(status=result['status'],detections=len(result['detections'])))
        if scenario=='multiple':
            check('API-08 multiple detection IDs preserved',len(result['detections'])==2 and
                  len({d['detection_id'] for d in result['detections']})==2)
        if scenario=='empty':
            body=dict(request_id=session['request_id'],revision=0,operator='TV2 synthetic QA',
                      note='Synthetic fixture: detector miss at left edge; no expert adjudication.',
                      image_outcome='detector_miss',box_reviews=[])
            reviewed=http.post(args.url+'/api/review',json=body,timeout=30).json();save('synthetic_detector_miss',reviewed)
            check('API-09 synthetic detector miss separate revision',reviewed['original']['result']['status']=='no_detection'
                  and reviewed['review']['image_outcome']=='detector_miss')
    response=http.post(args.url+'/api/analyze',json=dict(file_name='synthetic_corrupt.jpg',image_base64='aW52YWxpZA==',
                       mode='megadetector',classifier='B2',threshold=.2,review_threshold=.7),timeout=30)
    response.raise_for_status();data=response.json();save('synthetic_corrupt',{k:v for k,v in data.items() if k!='preview'})
    check('API-10 corrupt image visible read error',data['result']['status']=='error' and data['result']['error']['stage']=='read')
    save('runtime_measurements',real)
    save('review_summary',dict(status='API_PASS_BROWSER_BLOCKED',review_commit=args.commit,
         url=args.url,checks=checks,browser=dict(status='BLOCKED',reason='IAB localhost timeout; native Edge app approval timed out'),
         screenshots=[],browser_export='BLOCKED (API reload verified; browser download not exercised)',
         responsive_1440_390_320='BLOCKED',batch_csv='NOT_IMPLEMENTED_IN_PR8',test_inference_performed=False))


if __name__=='__main__': main()
