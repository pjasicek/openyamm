"""Stage MM5's explicit environment-only common-script policy without rebuilding geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
RUNTIME = PROJECT/'implementation/runtime/worlds/mm5'
SOURCE = PROJECT/'implementation/world_policy'
SCRIPT = Path('events/common/cross_continents_common.lua')


def stage_policy(stage):
    owner = json.loads((stage/'mm5-stage.json').read_text())
    assert owner['project'] == 'mm5_castleview_kalindra'
    source = SOURCE/SCRIPT
    targets = [RUNTIME/SCRIPT, stage/'assets_dev/worlds/mm5'/SCRIPT]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    for target in targets:
        assert not target.is_symlink(), target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
    base = ROOT/'assets_dev/engine'/SCRIPT
    report = {
        'world': 'mm5', 'policy': 'environment-only; no inherited cross-continent hooks',
        'source': str(source.relative_to(PROJECT)), 'virtualPath': str(SCRIPT), 'sha256': digest,
        'baseSource': str(base.relative_to(ROOT)),
        'baseSha256': hashlib.sha256(base.read_bytes()).hexdigest(),
        'targets': [str(target) for target in targets],
        'limits': 'Staging provenance only. Fresh runtime and saved timer/population checks are separate.'}
    review = PROJECT/'review/script_policy_v1'
    review.mkdir(exist_ok=True)
    (review/'staging.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, default=Path('/tmp/openyamm-mm5-castleview'))
    args = parser.parse_args()
    print(json.dumps(stage_policy(args.stage), indent=2))
