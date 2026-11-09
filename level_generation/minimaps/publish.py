"""Accept an authorized, reviewed light-noise minimap revision; deploy with deploy_icons.py afterward."""
import argparse
from collections import defaultdict
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
DEFAULT_HERE = HERE
ROOT = HERE.parents[1]
HUD = ROOT/'level_generation/ui/hud_inventory'
CURRENT = HUD/'accepted_icons.json'
sys.path.insert(0,str(HUD))
from queue import accepted_cell, save


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable(path, record):
    if path.exists():
        assert read(path)==record, 'Receipt changed: '+str(path)
    else:
        save(path,record)


def copy_verified(source,destination,expected):
    assert sha(source)==expected
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        assert sha(destination)==expected
    else:
        shutil.copyfile(source,destination)
    destination.chmod(0o644)


def main():
    global HERE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--workspace',type=Path,default=DEFAULT_HERE,help='Reviewed revision directory')
    args=parser.parse_args()
    HERE=args.workspace.resolve()
    with (HUD/'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        # Publication uses frozen acceptance evidence, as deploy_icons.py does.
        # Live HUD layout inputs belong to the generation queue; this revision's
        # current ODM geometry and textures are checked by validate.py instead.
        state_path=HUD/'checkpoint/state.json';state=read(state_path)
        prepared=read(HUD/'jobs.json');catalog=read(HUD/'expected_targets.json')
        assert state['jobs_sha256']==sha(HUD/'jobs.json'), 'Prepared jobs changed'
        assert prepared['source_manifest_sha256']==sha(HUD/'expected_targets.json'), 'Frozen catalog changed'
        targets={target['id']:target for target in catalog['targets']}
        target_cells=defaultdict(list)
        for job in prepared['jobs']:
            for member in job['members']:
                target_cells[member['target']].append(member['id'])
        layout_cells=set();layout_revision=state.get('layout_revision')
        if layout_revision:
            assert sha(layout_revision['path'])==layout_revision['sha256'], 'Accepted layout revision changed'
            layout=read(layout_revision['path'])
            layout_cells={cell for target in layout['targets'] for cell in target_cells[target]}
        def layout_hash(cell):
            return layout_revision['sha256'] if cell in layout_cells else None
        storage_root=Path(layout_revision['path']).parent if layout_revision else state_path.parent
        previous=read(CURRENT)
        assert state['accepted_icon_index']['sha256']==sha(CURRENT)
        if (HERE/'accepted.json').exists():
            for target,record in read(HERE/'accepted.json')['records'].items():
                assert previous['records'][target]==record, 'Revision superseded; deploy the current index'
                assert all(accepted_cell(state['cells'],c,layout_hash) for c in target_cells[target])
            print('Already accepted; use deploy_icons.py --check or --install.')
            return
        exports=read(HERE/'exports.json')
        scope=read(HERE/'scope.json')
        count=scope['count']
        assert exports['count']==exports['expected']==count==len(scope['records'])
        assert {row['target'] for row in exports['records']}=={row['target'] for row in scope['records']}
        audit=read(HERE/'validation.json')
        assert audit['result']=='PASS' and audit['count']==count
        assert audit['exports_sha256']==sha(HERE/'exports.json')
        visual=read(HERE/'visual_review.json')
        assert visual['result']=='PASS' and visual['count']==count
        assert visual['exports_sha256']==sha(HERE/'exports.json')
        request=read(HERE/'request.json') if HERE!=DEFAULT_HERE else dict(
            instruction='yes light noise is the winner here. accept this approach, regen all minimaps and deploy them to icons_x2')
        authority=dict(schema='openyamm-minimap-approach-approval-v1',
            instruction=request['instruction'],
            scope=dict(**scope['worlds'],total=count),
            approval='User selected the light-noise New Sorpigal approach and authorized batch regeneration, acceptance and deployment.',
            review='User selected the recipe; this revision was checked by the assistant under the regeneration request.',
            noise=read(HERE/'approved_noise.json'),recipe=read(HERE/'approved_recipe.json'),
            evidence={str(p.relative_to(ROOT)):sha(p) for p in [HERE/'exports.json',HERE/'validation.json',HERE/'visual_review.json']})
        immutable(HERE/'authority.json',authority)
        records={};cells={}
        for export in exports['records']:
            target=export['target'];out=HERE/export['directory'];prior=previous['records'][target]
            assert len(target_cells[target])==1
            cell=target_cells[target][0];assert accepted_cell(state['cells'],cell,layout_hash)
            assert state['staged_targets'][target]['sha256']==prior['sha256']
            assert sha(prior['artifact'])==prior['sha256']==sha(ROOT/prior['runtime_output_path'])
            assert read(out/'sources.json')['previous']==prior, 'Accepted source changed during generation'
            with Image.open(out/'x2.png') as image:
                assert image.format=='PNG' and list(image.size)==targets[target]['x2_size']==export['x2_size']
            destination=HERE/'accepted'/Path(prior['runtime_output_path']).relative_to('assets_dev')
            copy_verified(out/'x2.png',destination,export['outputs']['x2.png'])
            record=dict(target=target,artifact=str(destination),sha256=sha(destination),
                source=prior['source'],source_sha256=prior['source_sha256'],x2_size=export['x2_size'],
                runtime_output_path=prior['runtime_output_path'],previous_artifact=prior['artifact'],previous_sha256=prior['sha256'],
                master_artifact=str(out/'master.png'),master_sha256=export['outputs']['master.png'],
                layered_artifact=str(out/'layers.ora'),capture=str(out/'capture.json'),
                authority=str(HERE/'authority.json'),acceptance='explicit_user_approved_light_noise_batch',
                reviewed_artifact=str(out/'x2.png'),recipe=str(HERE/'approved_recipe.json'),noise_recipe=str(HERE/'approved_noise.json'),
                placement_changes=False,world_bounds=[-32768,32768,-32768,32768],method='registered_cycles_layers_light_terrain_noise')
            receipt=HERE/'receipts'/(target+'.json');immutable(receipt,record)
            records[target]=record;cells[cell]=dict(record=record,receipt=receipt)
        if not args.apply:
            print(json.dumps(dict(prepared=True,targets=len(records))))
            return
        copy_verified(CURRENT,HERE/'previous_accepted_index.json',sha(CURRENT))
        copy_verified(state_path,HERE/'checkpoint.before.json',sha(state_path))
        old_cells=copy.deepcopy(state['cells'])
        for cell,new in cells.items():
            record,receipt=new['record'],new['receipt']
            evidence={str(receipt):sha(receipt),str(HERE/'authority.json'):sha(HERE/'authority.json')}
            state['cells'][cell]=dict(status='accepted',artifact=record['artifact'],sha256=record['sha256'],
                acceptance_method='user_approved_minimap_light_noise_batch',layout_sha256=layout_hash(cell),
                dependency_cells={},evidence_hashes=evidence,
                review=dict(authority=str(HERE/'authority.json'),decision=str(receipt)))
            target=record['target'];contract=targets[target];cell_hashes={cell:record['sha256']}
            state['staged_targets'][target]=dict(target=target,source_path=contract['source_path'],
                source_sha256=record['source_sha256'],artifact=record['artifact'],sha256=record['sha256'],
                native_size=contract['native_size'],x2_size=record['x2_size'],runtime_output_path=record['runtime_output_path'],
                cells=cell_hashes,status='accepted_staged',evidence_hashes=evidence,
                review=dict(authority=str(HERE/'authority.json'),decision=str(receipt)))
            state['reconstructed_targets'][target]=dict(target=target,path=record['artifact'],sha256=record['sha256'],
                size=record['x2_size'],cells=cell_hashes,status='accepted_full_canvas')
            if target in state.get('restoration_inventory',{}):
                state['restoration_inventory'][target].update(status='accepted',canonical_artifact=record['artifact'],
                    canonical_sha256=record['sha256'],acceptance_receipt=str(receipt))
        # Preserve historical references to prior minimaps rather than invalidating unrelated accepted art.
        frozen=[]
        for cell,record in state['cells'].items():
            if cell in cells:
                continue
            for dependency,expected in list(record.get('dependency_cells',{}).items()):
                if dependency not in cells:
                    continue
                old=old_cells[dependency];assert sha(old['artifact'])==expected==old['sha256']
                record.setdefault('evidence_hashes',{})[old['artifact']]=expected
                record.setdefault('reference_revision_history',[]).append(dict(cell=dependency,sha256=expected,artifact=old['artifact']))
                del record['dependency_cells'][dependency]
                frozen.append(cell)
        assert all(accepted_cell(state['cells'],cell,layout_hash) for cell in list(cells)+frozen)
        current=copy.deepcopy(previous);current['records'].update(records)
        current['latest_revision']=str((HERE/'accepted.json').relative_to(ROOT))
        current['updated_at']=datetime.now(timezone.utc).isoformat()
        assert current['count']==len(current['records'])==previous['count']
        assert all(current['records'][target]==record for target,record in previous['records'].items() if target not in records)
        save(CURRENT,current)
        state['accepted_icon_index']=dict(path=str(CURRENT.relative_to(ROOT)),sha256=sha(CURRENT),targets=current['count'])
        save(state_path,state)
        save(storage_root/'exports/manifest.json',dict(targets=list(state['staged_targets'].values())))
        save(HERE/'accepted.json',dict(schema='openyamm-minimap-accepted-replacement-v1',count=len(records),records=records,
            authority=str(HERE/'authority.json'),canonical_index_sha256=sha(CURRENT),ledger_sha256=sha(state_path),
            published_at=current['updated_at'],frozen_reference_cells=frozen))
        print(json.dumps(dict(accepted=True,replacements=len(records),total=current['count'],unrelated_records_unchanged=True)))


if __name__=='__main__':
    main()
