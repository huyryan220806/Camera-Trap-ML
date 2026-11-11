"""Verify R6 delivery against TV3 hashes and TV2 acceptance; preserve older intakes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ZIP_SHA='fcb6118cd89c1a825d02e6d1c0a7bd19b983bac7bebaf863b959c0dd8854144e'
CHECKPOINT_SHA='24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    receipt=json.loads(args.receipt.read_text(encoding='utf-8-sig'))
    assert sha(args.zip)==receipt['zip_sha256']==ZIP_SHA
    assert args.zip.stat().st_size==receipt['bytes']==267959559
    assert receipt['checkpoint_sha256']==CHECKPOINT_SHA
    args.output.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(args.zip) as archive:
        seen=set();total=0
        for entry in archive.infolist():
            name=entry.filename;path=Path(name)
            assert not ('\\' in name or ':' in name or path.is_absolute() or '..' in path.parts)
            assert (entry.external_attr>>16)&0o170000!=0o120000 and not entry.flag_bits&1
            normalized=path.as_posix().casefold();assert normalized not in seen;seen.add(normalized)
            assert (args.output/path).resolve().is_relative_to(args.output.resolve())
            total+=entry.file_size;assert total<1024**3 and len(seen)<100
        assert archive.testzip() is None
        archive.extractall(args.output)
    folder=args.output/'R6_attempt01'
    for name,spec in receipt['files'].items():
        path=(folder/name).resolve();assert path.is_relative_to(folder.resolve())
        assert path.stat().st_size==spec['bytes'] and sha(path)==spec['sha256'],name
    assert sha(folder/'package_index.json')=='d2f149a5041049d0eee7ef460a3c8a5e479fb7cb37904358ed20e7c845b0f071'
    assert sha(folder/'registry.delivery.json')==sha(folder/'registry.result.json')
    h=json.loads((folder/'handoff.json').read_text())
    report={'status':'PASS','run_id':'R6','zip_sha256':ZIP_SHA,'zip_bytes':args.zip.stat().st_size,
        'payload_files':len(receipt['files']),'checkpoint_sha256':CHECKPOINT_SHA,'checkpoint_bytes':86851190,
        'config_sha256':h['config_sha256'],'source_sha':h['source_sha'],'feature_dim':h['feature_dim'],
        'pooling':h['pooling'],'dataset_version':h['train_dataset'],
        'native_module':'dino_w6_r6','native_source_sha256':receipt['files']['src/training/dino_w6.py']['sha256'],
        'source_index_sha256':sha(folder/'source_index.json'),'handoff_sha256':sha(folder/'handoff.json'),
        'config_raw_sha256':sha(folder/'config.json'),'preprocessing_sha256':sha(folder/'preprocessing.json'),
        'class_map_sha256':sha(folder/'class_map.json'),'tv2_acceptance_commit':'96d202563c63b47d4d3d6773c3d4b5a2a29c3c7a'}
    (args.output/'intake.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
