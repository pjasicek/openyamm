"""Expose the installed accepted revision without overwriting browser feedback."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
HUD=OUT.parent
ROOT=HUD.parents[2]
sys.path.insert(0,str(HUD))
import scan_spill as scan


def main():
    accepted=scan.read(OUT/'accepted.json');installed=scan.read(OUT/'installed.json')
    confirmation_path=OUT/'final_12_user_approval.json'
    confirmation=scan.read(confirmation_path) if confirmation_path.exists() else None
    if confirmation:
        assert confirmation['accepted_revision_sha256']==scan.sha(OUT/'accepted.json')
        assert set(confirmation['records'])=={t for t,r in accepted['records'].items() if r['resolution']}
    runtime={r['target']:r for r in installed['records']}
    contracts={c['id']:c for c in scan.read(HUD/'expected_targets.json')['targets']}
    rows={}
    for target,record in accepted['records'].items():
        assert runtime[target]['sha256']==record['sha256'],target
        result=dict(artifact=str(Path(record['artifact']).relative_to(ROOT)),sha256=record['sha256'],
                    resolution=record['resolution'])
        if confirmation and target in confirmation['records']:
            assert confirmation['records'][target]['sha256']==record['sha256'],target
            result['confirmed_at']=confirmation['accepted_at']
            result['confirmation']=str(confirmation_path.relative_to(ROOT))
        if record['resolution']:
            with Image.open(record['artifact']) as im:after=im.convert('RGBA')
            native,_=scan.native_reference(contracts[target]);metrics,_=scan.measure(after,native)
            with Image.open(record['previous_artifact']) as im:before=np.asarray(im.convert('RGBA'))
            result['after_scan']=metrics['status']
            result['overall_changed_pixels']=int(np.any(np.asarray(after)!=before,axis=2).sum())
        rows[target]=result
    publication=dict(schema='openyamm-spill-review-publication-v1',published_at=accepted['published_at'],
        authority=str((OUT/'accepted.json').relative_to(ROOT)),records=rows)
    review=HUD/'spill_repairs_20260927/review'
    (review/'publication.js').write_text('window.SPILL_PUBLICATION = '+json.dumps(publication)+';\n')
    for src,dest in [('spill_repair_review.html','index.html'),('spill_repair_review.js','review.js')]:
        (review/dest).write_bytes((HUD/src).read_bytes())
    print(json.dumps(dict(published=len(rows),comments_resolved=sum(bool(r['resolution']) for r in rows.values()))))


if __name__=='__main__':main()
