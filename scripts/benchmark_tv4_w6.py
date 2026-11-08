"""Fresh-process CPU benchmark: W5/R1-R4, identical frozen24 train images, two warm rounds."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
MODELS=('DINOv3_LP_run01','DINO_W6_R2','DINO_W6_R1','DINO_W6_R3','DINO_W6_R4')


def summary(values):
    ordered=sorted(values)
    # Nearest-rank p95, explicitly only48 repeated requests /24 unique images.
    return {'n':len(values),'mean_ms':statistics.mean(values),'p50_ms':statistics.median(values),
            'p95_ms':ordered[math.ceil(.95*len(ordered))-1],'p95_method':'nearest_rank'}


def worker(kind,out):
    import torch
    import psutil
    from PIL import Image
    from src.demo.classifier import ClassifierCache,crop_coordinates
    from src.demo.dino import DinoCache
    from src.demo.dino_w6 import W6Cache
    from src.demo.detector import MegaDetectorAdapter,digest,MODEL_PATH,PACKAGE_VERSION
    from src.demo.inference import analyze_classified
    from src.demo.review import runtime_info
    torch.set_num_threads(4); torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
    fixture=ROOT/'outputs/tv4/w6/benchmark_fixture/images.json'
    rows=json.loads(fixture.read_text())['images']
    vendor=ROOT/'outputs/tv4/w5/dinov3_architecture'
    w5=DinoCache(ClassifierCache(),ROOT/'outputs/tv4/w5/intake_20261102/DINOv3_LP_run01',vendor)
    cache=W6Cache(w5,vendor)
    first=rows[0]
    with Image.open(ROOT/first['quality']['local_path']) as im:
        rgb=im.convert('RGB')
        crop=rgb.crop(crop_coordinates(first['boxes'][0]['bbox_xywh'],rgb.size))
    start=time.perf_counter()
    if kind=='DINOv3_LP_run01': w5.logits([crop])
    else: cache.logits([crop],kind)
    cold_load_ms=(time.perf_counter()-start)*1000
    actual_detector=MegaDetectorAdapter()

    class Detector:
        elapsed=0
        def __getattr__(self,name): return getattr(actual_detector,name)
        def predict(self,*args):
            started=time.perf_counter()
            try: return actual_detector.predict(*args)
            finally: self.elapsed=(time.perf_counter()-started)*1000
    class Cache:
        elapsed=0
        def predict(self,*args):
            started=time.perf_counter()
            try: return cache.predict(*args)
            finally: self.elapsed=(time.perf_counter()-started)*1000
    detector=Detector(); timed_cache=Cache()
    def analyze(row):
        data=(ROOT/row['quality']['local_path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['quality']['sha256']
        detector.elapsed=timed_cache.elapsed=0
        started=time.perf_counter()
        envelope=analyze_classified(data,row['file_name'],classifier=kind,cache=timed_cache,
            mode='megadetector',threshold=.2,review_threshold=.7,adapter=detector)
        elapsed=(time.perf_counter()-started)*1000
        result=envelope['result']
        return {'model_id':kind,'image_id':row['image_id'],'image_sha256':row['quality']['sha256'],
            'status':result['status'],'boxes':len(result['detections']),'error':result['error'],
            'detector_ms':detector.elapsed,'classifier_ms':timed_cache.elapsed,'pipeline_ms':elapsed,
            'envelope':envelope}
    cold_pipeline=analyze(first)
    records=[]
    with (out/f'{kind}.jsonl').open('x',encoding='utf-8') as log:
        for repeat in range(2):
            for index,row in enumerate(rows):
                record=analyze(row); record.update(round=repeat+1,index=index+1)
                records.append(record); log.write(json.dumps(record,ensure_ascii=False)+'\n'); log.flush()
                if (index+1)%6==0:
                    print(f'{kind} round{repeat+1}: {index+1}/24',flush=True)
    statuses={state:sum(r['status']==state for r in records) for state in sorted({r['status'] for r in records})}
    report={'model_id':kind,'unique_images':24,'requests':48,'warm_rounds':2,'runtime':runtime_info(),
        'device':'cpu','precision':'FP32','amp':False,'tf32':False,'cold_classifier_load_and_one_crop_ms':cold_load_ms,
        'cold_pipeline_classifier_already_loaded':cold_pipeline,'fixture_sha256':digest(fixture),
        'detector_sha256':digest(MODEL_PATH),'detector_version':'MDv5a.0.1','megadetector_package':PACKAGE_VERSION,
        'threshold':.2,'review_threshold':.7,'image_batch':1,'crop_microbatch':8,
        'detector_resolution':1280,'classifier_resolution':256,'status_counts':statuses,
        'total_boxes':sum(r['boxes'] for r in records),
        'timing':{key:summary([r[key] for r in records]) for key in ('pipeline_ms','detector_ms','classifier_ms')},
        'process_memory_bytes':psutil.Process().memory_info()._asdict(),
        'timing_scope':'Pipeline includes decode, detector, classifier, checksums/cache, schema validation; excludes disk read/hash gate, HTTP/upload, preview, journal, browser, human review',
        'cold_scope':'Fresh Python per model; classifier weights load + gates + one train crop. Separate cold detector request with classifier already loaded.',
        'test_opened':False,'records_path':f'{kind}.jsonl'}
    (out/f'{kind}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(kind,'COMPLETE',json.dumps(report['timing']['pipeline_ms']),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--worker',choices=MODELS)
    args=parser.parse_args()
    if args.worker:
        worker(args.worker,args.output); return
    args.output.mkdir(parents=True,exist_ok=False)
    reports=[]
    for model in MODELS:
        result=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--output',str(args.output),'--worker',model],cwd=ROOT)
        if result.returncode:
            raise RuntimeError(f'{model} worker failed; preserve output and diagnose')
        reports.append(json.loads((args.output/f'{model}.json').read_text()))
    (args.output/'benchmark.json').write_text(json.dumps({'status':'COMPLETE','models':reports,
        'scope':'24 unique train images, two repeated warm rounds per model, fresh CPU process per model; no GPU/Test'},indent=2),encoding='utf-8')


if __name__=='__main__': main()
