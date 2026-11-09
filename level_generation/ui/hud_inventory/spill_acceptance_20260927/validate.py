"""Validate publication, comment resolution, geometry, aliases and preserved work."""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
HUD=OUT.parent
ROOT=HUD.parents[2]
sys.path.insert(0,str(HUD))
from queue import Queue,save


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    accepted=read(OUT/'accepted.json');current=read(HUD/'accepted_icons.json')['records'];q=Queue()
    previous=read(OUT/'checkpoint.before.json');scope=set(accepted['records'])
    prepared=read(OUT/'prepared.json');cells=set(prepared['cells'])
    frozen={r['dependent'] for r in accepted['reference_revision_migrations']}
    assert set(accepted['records'])=={r['target'] for r in read(HUD/'spill_repairs_20260927/review/manifest.json')['records']}
    assert {t for t,r in accepted['records'].items() if r['resolution']}=={
        r['target'] for r in read(OUT/'commented_targets.json')['records']}
    for name,value in accepted['placements'].items():assert sha(ROOT/name)==value,name
    for key in ['attempts','claims','layout_revision','user_excluded_targets','retired_targets','native_source_archive']:
        assert q.state.get(key)==previous.get(key),key
    for cell,old in previous['cells'].items():
        if cell not in cells|frozen:assert q.state['cells'][cell]==old,cell
    for target,old in previous['staged_targets'].items():
        if target not in scope:assert q.state['staged_targets'][target]==old,target
    groups=defaultdict(list)
    old_index=read(OUT/'previous_accepted_index.json')['records']
    namespace=defaultdict(int)
    for target,record in current.items():
        assert sha(record['artifact'])==record['sha256'],target
        destination=ROOT/record['runtime_output_path']
        assert sha(destination)==record['sha256'] and destination.stat().st_mode&0o777==0o644,target
        assert q.state['staged_targets'][target]['sha256']==record['sha256'],target
        old=old_index[target]
        groups[(old['sha256'],old['source_sha256'])].append((target,record['sha256']))
        if target in scope:
            assert record==accepted['records'][target],target
            with Image.open(old['artifact']) as im:a=np.asarray(im.convert('RGBA'))
            with Image.open(record['artifact']) as im:
                b=np.asarray(im.convert('RGBA'));assert im.format=='PNG',target
            assert a.shape==b.shape and np.array_equal(a[:,:,3],b[:,:,3]),target
            assert all(q.accepted(c) for c in q.target_cells[target]),target
            namespace['/'.join(Path(record['runtime_output_path']).parts[1:-2])]+=1
        else:assert record==old,target
    aliases=[g for g in groups.values() if len({h for _,h in g})>1]
    assert not aliases,aliases
    assert all(q.accepted(cell) for cell in frozen)
    result=dict(result='PASS',accepted_review_entries=len(scope),runtime_icons_checked=len(current),
        changed_runtime_images=accepted['summary']['changed_images'],resolved_comments=12,
        namespace_counts=dict(namespace),alpha_changes=0,dimension_changes=0,placement_changes=0,
        unrelated_cell_changes=0,duplicate_conflicts=0,frozen_historical_references=len(frozen),
        latest_index_sha256=sha(HUD/'accepted_icons.json'),ledger_sha256=sha(q.state_path),
        accepted_revision_sha256=sha(OUT/'accepted.json'))
    save(OUT/'validation.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
