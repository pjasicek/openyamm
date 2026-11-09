"""Record the explicitly authorized spill review revision in the canonical icon ledger.

Default prepares hash-checked workspace artifacts and receipts. --apply updates the
ledger and current accepted index; deployment is a separate deploy_icons.py command.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
HUD=OUT.parent
ROOT=HUD.parents[2]
sys.path.insert(0,str(HUD))
from queue import Queue,save

METHOD='user_approved_spill_revision_20260927'
CURRENT=HUD/'accepted_icons.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def immutable(path,value):
    if path.exists():assert read(path)==value,f'Immutable receipt differs: {path}'
    else:save(path,value)


def copy_verified(source,destination,expected):
    assert sha(source)==expected,str(source)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():assert sha(destination)==expected,str(destination)
    else:shutil.copy2(source,destination)
    destination.chmod(0o644)


def prepare(q):
    review_path=HUD/'spill_repairs_20260927/review/manifest.json'
    review=read(review_path)
    previous_path=CURRENT if CURRENT.exists() else HUD/'runtime_install_20260926/accepted.json'
    previous=read(previous_path)['records']
    resolutions={r['target']:r for r in read(OUT/'resolutions.json')['records']}
    assert len(review['records'])==1722 and len(resolutions)==12
    capture=read(OUT/'browser_state.original.json')
    decisions=json.loads(capture['storage']['openyamm-icon-spill-repairs-v1'])['decisions']
    decisions={r['target']:r for r in decisions.values()}
    authority=dict(schema='openyamm-icon-revision-authority-v1',method=METHOD,
        instruction='Accept all of these as new accepted, deploy them, retain the new accepted workspace assets, and only resolve recent web comments.',
        scope='All 1722 entries in the current spill repair review; 12 captured commented targets repaired.',
        browser_capture_sha256=sha(OUT/'browser_state.original.json'),
        review_manifest_sha256=sha(review_path),resolutions_sha256=sha(OUT/'resolutions.json'),
        generation='Three built-in imagegen restorations, agent visually checked under user repair authorization; not represented as earlier browser approvals.',
        placement_policy='Existing alpha masks, dimensions and item placement tables retained.')
    immutable(OUT/'authority.json',authority)
    records={};cells={}
    for row in review['records']:
        target=row['target'];prior=previous[target];contract=q.targets[target]
        assert prior['sha256']==row['before_sha256'],target
        assert q.state['staged_targets'][target]['sha256']==prior['sha256'],target
        assert sha(ROOT/prior['runtime_output_path'])==prior['sha256'],target
        selected=ROOT/row.get('candidate',row['before']);expected=row.get('sha256',row['before_sha256'])
        resolution=resolutions.get(target)
        if resolution:
            assert resolution['sha256']==expected,target
            selected=ROOT/resolution['artifact'];expected=resolution['resolved_sha256']
        with Image.open(ROOT/row['before']) as image:before=np.asarray(image.convert('RGBA'))
        with Image.open(selected) as image:
            after=np.asarray(image.convert('RGBA'))
            assert list(image.size)==contract['x2_size'],target
        assert before.shape==after.shape and np.array_equal(before[:,:,3],after[:,:,3]),target
        destination=OUT/'accepted'/Path(prior['runtime_output_path']).relative_to('assets_dev')
        copy_verified(selected,destination,expected)
        record=dict(target=target,artifact=str(destination),sha256=expected,
            source=prior['source'],source_sha256=prior['source_sha256'],x2_size=contract['x2_size'],
            runtime_output_path=prior['runtime_output_path'],previous_artifact=prior['artifact'],
            previous_sha256=prior['sha256'],reviewed_artifact=str(selected),
            authority=str(OUT/'authority.json'),review_manifest=str(review_path),
            browser_decision=decisions.get(target),resolution=resolution,
            acceptance='explicit_user_authorized_comment_repair' if resolution else 'explicit_user_all_review_entries_approval',
            alpha_identical=True,dimensions_identical=True,placement_changes=False)
        receipt=OUT/'receipts'/(target+'.json');immutable(receipt,record)
        records[target]=record
        target_cells=q.target_cells[target]
        if len(target_cells)==1:
            cells[target_cells[0]]=dict(artifact=str(destination),sha256=expected,receipt=str(receipt))
        else:
            assert target=='engine--icons--sprites.pcx'
            # Update precisely the atlas cells containing changed pixels; do not
            # replace the entire atlas's cell ownership with a made-up singleton.
            for cell in target_cells:
                x,y,w,h=q.members[cell][1]['export_region']
                changed=np.any(before[y:y+h,x:x+w]!=after[y:y+h,x:x+w],axis=2)
                if not changed.any():continue
                old=q.state['cells'][cell]
                with Image.open(old['artifact']) as image:cell_pixels=np.asarray(image.convert('RGBA')).copy()
                assert np.array_equal(cell_pixels[:,:,:3],before[y:y+h,x:x+w,:3]),cell
                cell_pixels[:,:,:3][changed]=after[y:y+h,x:x+w,:3][changed]
                cell_path=OUT/'accepted/cells'/(cell+'.png');cell_path.parent.mkdir(parents=True,exist_ok=True)
                Image.fromarray(cell_pixels).save(cell_path);cell_path.chmod(0o644)
                cells[cell]=dict(artifact=str(cell_path),sha256=sha(cell_path),receipt=str(receipt))
    summary=dict(targets=len(records),changed_images=sum(r['sha256']!=r['previous_sha256'] for r in records.values()),
        comment_resolutions=len(resolutions),accepted_cells_updated=len(cells),alpha_changes=0,dimension_changes=0,
        previous_index=str(previous_path),previous_index_sha256=sha(previous_path))
    return records,cells,previous,summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    with (HUD/'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);q=Queue()
        if (OUT/'accepted.json').exists():
            accepted=read(OUT/'accepted.json')
            for target,record in accepted['records'].items():
                assert q.state['staged_targets'][target]['sha256']==record['sha256'],target
                assert all(q.accepted(c) for c in q.target_cells[target]),target
            print('This revision is already accepted; use deploy_icons.py for verified redeployment.');return
        records,cells,previous,summary=prepare(q)
        save(OUT/'prepared.json',dict(records=records,cells=cells,summary=summary))
        if not args.apply:print(json.dumps(dict(prepared=True,**summary),indent=2));return
        if (OUT/'checkpoint.before.json').exists():
            assert sha(q.state_path)==sha(OUT/'checkpoint.before.json'),'Inspect interrupted ledger publication'
        else:shutil.copy2(q.state_path,OUT/'checkpoint.before.json')
        immutable(OUT/'previous_accepted_index.json',dict(records=previous))
        placement_paths=[ROOT/'assets_dev/engine/data_tables/item_visuals.txt',HUD/'finalization_20260926/placements.json']
        placements={str(p.relative_to(ROOT)):sha(p) for p in placement_paths}
        old_cells=copy.deepcopy(q.state['cells'])
        for cell,new in cells.items():
            receipt=Path(new['receipt'])
            q.state['cells'][cell]=dict(status='accepted',artifact=new['artifact'],sha256=new['sha256'],
                acceptance_method=METHOD,layout_sha256=q.layout_hash(cell),dependency_cells={},
                evidence_hashes={str(receipt):sha(receipt),str(OUT/'authority.json'):sha(OUT/'authority.json')},
                review=dict(authority=str(OUT/'authority.json'),decision=str(receipt),
                    notes='Explicit blanket approval plus requested, inspected comment corrections. Prior ledger is archived.'))
        frozen=[]
        # These completed images were generated against a particular historical
        # reference revision. Keep that immutable reference, rather than making
        # a later RGB cleanup invalidate their existing approval.
        for cell,record in q.state['cells'].items():
            if cell in cells:continue
            for dependency,expected in list(record.get('dependency_cells',{}).items()):
                if dependency not in cells or cells[dependency]['sha256']==expected:continue
                old=old_cells[dependency];assert old['sha256']==expected and sha(old['artifact'])==expected
                snapshot=dict(cell=dependency,sha256=expected,artifact=old['artifact'],
                    reason='Freeze the exact previously reviewed reference revision during spill publication')
                record.setdefault('reference_revision_history',[]).append(snapshot)
                record.setdefault('evidence_hashes',{})[old['artifact']]=expected
                del record['dependency_cells'][dependency]
                frozen.append(dict(dependent=cell,**snapshot))
        for target,record in records.items():
            contract=q.targets[target];receipt=OUT/'receipts'/(target+'.json')
            target_cells={c:q.state['cells'][c]['sha256'] for c in q.target_cells[target]}
            evidence={str(receipt):sha(receipt),str(OUT/'authority.json'):sha(OUT/'authority.json')}
            q.state['staged_targets'][target]=dict(target=target,source_path=contract['source_path'],
                source_sha256=record['source_sha256'],artifact=record['artifact'],sha256=record['sha256'],
                native_size=contract['native_size'],x2_size=record['x2_size'],runtime_output_path=record['runtime_output_path'],
                cells=target_cells,evidence_hashes=evidence,status='accepted_staged',
                review=dict(authority=str(OUT/'authority.json'),decision=str(receipt)))
            q.state['reconstructed_targets'][target]=dict(target=target,path=record['artifact'],sha256=record['sha256'],
                size=record['x2_size'],cells=target_cells,status='accepted_full_canvas')
            if target in q.state.get('restoration_inventory',{}):
                q.state['restoration_inventory'][target].update(status='accepted',canonical_artifact=record['artifact'],
                    canonical_sha256=record['sha256'],acceptance_receipt=str(receipt))
        assert all(q.accepted(c) for t in records for c in q.target_cells[t])
        assert all(q.accepted(r['dependent']) for r in frozen)
        current=copy.deepcopy(previous);current.update(records)
        publication=dict(schema='openyamm-current-accepted-icons-v1',count=len(current),records=current,
            latest_revision=str((OUT/'accepted.json').relative_to(ROOT)),updated_at=datetime.now(timezone.utc).isoformat())
        save(CURRENT,publication)
        q.state['accepted_icon_index']=dict(path=str(CURRENT.relative_to(ROOT)),sha256=sha(CURRENT),targets=len(current))
        save(q.state_path,q.state)
        save(q.storage_root()/'exports/manifest.json',dict(targets=list(q.state['staged_targets'].values())))
        assert all(sha(ROOT/p)==value for p,value in placements.items())
        result=dict(schema='openyamm-accepted-spill-revision-v1',records=records,summary=summary,
            authority=str(OUT/'authority.json'),published_at=publication['updated_at'],placements=placements,
            reference_revision_migrations=frozen,canonical_index_sha256=sha(CURRENT),ledger_sha256=sha(q.state_path))
        save(OUT/'accepted.json',result)
        print(json.dumps(dict(accepted=True,reference_revisions_frozen=len(frozen),**summary),indent=2))


if __name__=='__main__':main()
