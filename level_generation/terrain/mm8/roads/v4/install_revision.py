"""Explicit, hash-guarded migration from the accepted v3 pack to the reviewed v4 road edges."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import *
from install import assets_snapshot
import json
import shutil


def main():
    manifest_path = P / 'complete_runtime_x2/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    old = json.loads((HERE / 'previous_delivery/complete_runtime_x2/manifest.json').read_text())
    previous = {n:r['sha256'] for n,r in old['files'].items()}
    expected = {n:r['sha256'] for n,r in manifest['files'].items()}
    review = json.loads((HERE / 'visual_review.json').read_text())
    assert review['status'] == 'visually_reviewed_for_road_edge_update'
    for relative,digest in review['evidence'].items(): assert sha(P / relative)==digest,relative
    assert {n for n in expected if expected[n]!=previous[n]} == set(review['changed'])
    validation = json.loads((P / 'reports/complete_validation.json').read_text())
    assert validation['manifest_sha256']==sha(manifest_path) and not validation['failures']
    assert validation['check_count']==24428
    source=P/'complete_runtime_x2/worlds/mm8/terrain_x2'
    assert {f.name:sha(f) for f in source.glob('*.png')}==expected
    destination=ROOT/'assets_dev/worlds/mm8/terrain_x2'
    installed={f.name:sha(f) for f in destination.glob('*.png')}
    assert installed in (previous,expected), 'Installed pack has independent edits; refusing replacement'
    acceptance=json.loads((HERE/'previous_delivery/reports/acceptance.json').read_text())
    acceptance['manifest_sha256']=sha(manifest_path)
    acceptance['evidence']['reports/complete_validation.json']=sha(P/'reports/complete_validation.json')
    acceptance['evidence']['roads/v4/visual_review.json']=sha(HERE/'visual_review.json')
    acceptance['evidence']['roads/v4/validation.json']=sha(HERE/'validation.json')
    acceptance['road_edge_revision']='v4: local NS donor repaint propagated to30 connected cobble tiles; prior v3 road reviews remain historical and are superseded for these changed edges by roads/v4/visual_review.json.'
    for relative,digest in acceptance['evidence'].items(): assert sha(P/relative)==digest,relative
    # The migration preserves all nonterrain assets and every original texture.
    before=assets_snapshot(destination)
    integration=json.loads((HERE/'previous_delivery/reports/integration.json').read_text())
    baseline_path=P/'reports/protected_baseline.json'
    baseline=json.loads(baseline_path.read_text())
    # Settings are user-owned and can change between deliveries. Preserve the
    # current settings, while still requiring every protected asset to match.
    settings_before=sha(ROOT/'settings.ini')
    previous_baseline=HERE/'previous_delivery/reports/protected_baseline.json'
    if not previous_baseline.exists(): shutil.copy2(baseline_path,previous_baseline)
    baseline['settings.ini']=settings_before
    for relative,digest in {**integration['preserved_original_terrain'],**baseline}.items():
        assert sha(ROOT/relative)==digest,relative
    for name in review['changed']:
        shutil.copy2(source/name,destination/name)
        (destination/name).chmod(0o644)
    assert {f.name:sha(f) for f in destination.glob('*.png')}==expected
    assert assets_snapshot(destination)==before
    assert sha(ROOT/'settings.ini')==settings_before
    baseline_path.write_text(json.dumps(baseline,indent=2)+'\n')
    acceptance_path=P/'reports/acceptance.json'
    acceptance_path.write_text(json.dumps(acceptance,indent=2)+'\n')
    integration.update(files=expected,acceptance_sha256=sha(acceptance_path),manifest_sha256=sha(manifest_path),
                       preserved_asset_entries=len(before), migration_script='roads/v4/install_revision.py',
                       migration_script_sha256=sha(HERE/'install_revision.py'), changed_files=review['changed'],
                       protected_baseline_sha256=sha(baseline_path), preserved_current_settings_sha256=settings_before,
                       previous_manifest_sha256=sha(HERE/'previous_delivery/complete_runtime_x2/manifest.json'))
    (P/'reports/integration.json').write_text(json.dumps(integration,indent=2)+'\n')
    print('Installed30 repaired cobble tiles;209 remaining textures and',len(before),'other asset entries preserved')


if __name__=='__main__': main()
