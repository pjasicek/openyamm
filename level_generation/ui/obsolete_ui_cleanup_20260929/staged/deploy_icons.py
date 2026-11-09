"""Verify or redeploy the current accepted icon workspace revision.

The accepted_icons.json index is authoritative. This command never regenerates or
accepts artwork and cannot silently replay an older dated installation snapshot.
"""
import argparse
import fcntl
import hashlib
import json
import os
import shutil
from pathlib import Path

from PIL import Image

from queue import Queue,save

HUD=Path(__file__).resolve().parent
ROOT=HUD.parents[2]
INDEX=HUD/'accepted_icons.json'
RETIREMENTS=HUD/'runtime_retirements.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())



def runtime_records(records):
    """Keep accepted artwork intact while explicitly retiring selected runtime exports."""
    if not RETIREMENTS.exists():
        return records, {}
    manifest = read(RETIREMENTS)
    assert manifest['schema'] == 'openyamm-runtime-icon-retirements-v1'
    retired = manifest['records']
    assert manifest['count'] == len(retired)
    assert retired.keys() <= records.keys(), 'Unknown retired accepted target'
    for target, retirement in retired.items():
        record = records[target]
        assert retirement['runtime_output_path'] == record['runtime_output_path'], target
        assert retirement['sha256'] == record['sha256'], f'Review changed retirement: {target}'
        assert sha(record['artifact']) == record['sha256'], f'Missing retired source art: {target}'
        assert not (ROOT / record['runtime_output_path']).exists(), f'Retired icon is still mounted: {target}'
    return {target: record for target, record in records.items() if target not in retired}, retired


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install',action='store_true',help='Deploy verified current accepted images')
    parser.add_argument('--check',action='store_true',help='Require runtime and workspace hashes to match')
    args=parser.parse_args()
    with (HUD/'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        q=Queue();manifest=read(INDEX);records=manifest['records']
        assert q.state['accepted_icon_index']['sha256']==sha(INDEX),'Current index/ledger mismatch'
        assert manifest['count']==len(records)
        records,retired=runtime_records(records)
        pending=[];destinations=set();checked_cells=set()
        for target,record in records.items():
            source=Path(record['artifact']);destination=ROOT/record['runtime_output_path']
            assert destination not in destinations,record['runtime_output_path'];destinations.add(destination)
            assert destination.name==destination.name.lower(),target
            assert destination.parent.name=='icons_x2' and 'mm9' not in destination.parts,target
            assert source.is_relative_to(HUD) or source.is_relative_to(ROOT/'level_generation'),source
            assert sha(source)==record['sha256'],target
            assert q.state['staged_targets'][target]['sha256']==record['sha256'],target
            with Image.open(source) as image:
                assert image.format=='PNG' and list(image.size)==record['x2_size'],target
            frozen_size=q.targets[target]['x2_size']
            migration=record.get('canvas_migration')
            if record['x2_size']!=frozen_size:
                assert migration and migration['target']==target,f'Missing export canvas migration: {target}'
                assert migration['previous_export_size']==frozen_size,target
                assert migration['approved_export_size']==record['x2_size'],target
                assert migration['source_native_size']==q.targets[target]['native_size'],target
                assert q.state['staged_targets'][target].get('canvas_migration')==migration,target
            else:
                assert not migration,f'Unnecessary export canvas migration: {target}'
            for cell in q.target_cells[target]:
                if cell not in checked_cells:
                    assert q.accepted(cell),cell;checked_cells.add(cell)
            current=sha(destination) if destination.exists() else None
            if current!=record['sha256']:
                assert current in (None,record.get('previous_sha256')),f'Unexpected runtime revision: {target}'
                pending.append((target,source,destination))
            elif destination.stat().st_mode&0o777!=0o644:
                pending.append((target,source,destination))
        if args.check:assert not pending,f'{len(pending)} icons have not been deployed'
        if args.install:
            for target,source,destination in pending:
                destination.parent.mkdir(parents=True,exist_ok=True)
                temporary=destination.with_name(destination.name+'.deploy-tmp')
                shutil.copyfile(source,temporary);temporary.chmod(0o644)
                assert sha(temporary)==records[target]['sha256'],target
                os.replace(temporary,destination)
            for target in retired:
                q.state['staged_targets'][target]['status']='accepted_runtime_retired'
            installed=[]
            for target,record in records.items():
                destination=ROOT/record['runtime_output_path'];assert sha(destination)==record['sha256'],target
                installed.append(dict(target=target,path=record['runtime_output_path'],sha256=record['sha256']))
                q.state['staged_targets'][target]['status']='accepted_installed'
            revision=ROOT/manifest['latest_revision'];receipt=revision.parent/'installed.json'
            save(receipt,dict(schema='openyamm-icon-deployment-v1',count=len(installed),records=installed,
                accepted_index=str(INDEX.relative_to(ROOT)),accepted_index_sha256=sha(INDEX)))
            q.state['runtime_icon_installation'].update(manifest=str(receipt.relative_to(ROOT)),
                sha256=sha(receipt),targets=len(installed),accepted_index=str(INDEX.relative_to(ROOT)))
            save(q.state_path,q.state)
            save(q.storage_root()/'exports/manifest.json',dict(targets=list(q.state['staged_targets'].values())))
        print(json.dumps(dict(result='PASS',accepted=manifest['count'],active=len(records),retired=len(retired),checked_cells=len(checked_cells),
            pending_before=len(pending),installed_this_run=len(pending) if args.install else 0,
            accepted_index_sha256=sha(INDEX)),indent=2))


if __name__=='__main__':main()
