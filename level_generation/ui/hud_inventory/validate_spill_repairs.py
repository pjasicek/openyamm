"""Validate staged PNGs against the accepted fitted images and audit manifest."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

import repair_spill as repair
import scan_spill as scan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, default=repair.OUT)
    args = parser.parse_args()
    manifest = scan.read(args.review / 'manifest.json')
    accepted = scan.read(scan.HERE / 'runtime_install_20260926/accepted.json')['records']
    contracts = {row['id']:row for row in scan.read(scan.HERE / 'expected_targets.json')['targets']}
    report = scan.read(scan.HERE / 'spill_audit_20260926/report.json')
    expected = {row['target'] for row in report['records']
                if row['scope'] == 'accepted_x2' and row['metrics']['status'] == 'likely_spill'}
    assert {row['target'] for row in manifest['records']} == expected
    assert len(manifest['records']) == len(expected)
    assert manifest['recipe_sha256'] == repair.digest(Path(repair.__file__))
    assert manifest['scan_sha256'] == repair.digest(scan.HERE / 'spill_audit_20260926/report.json')
    for path, digest in manifest['guards'].items():
        assert repair.digest(scan.ROOT / path) == digest, path
    aliases = defaultdict(list)
    candidates = set()
    total_changed = 0
    masters = {}
    for row in manifest['records']:
        target = row['target']
        assert repair.digest(scan.ROOT / row['before']) == row['before_sha256'], target
        assert repair.digest(scan.ROOT / accepted[target]['runtime_output_path']) == row['before_sha256'], target
        with Image.open(scan.ROOT / row['before']) as image:
            before = np.asarray(image.convert('RGBA'))
        result_hash = row['before_sha256']
        if 'candidate' in row:
            path = scan.ROOT / row['candidate']
            candidates.add(path.resolve())
            assert repair.digest(path) == row['sha256'], target
            assert path.stat().st_mode & 0o777 == 0o644, target
            with Image.open(path) as image:
                assert image.format == 'PNG', target
                after = np.asarray(image.convert('RGBA'))
            assert before.shape == after.shape, target
            assert np.array_equal(before[:,:,3],after[:,:,3]), target
            changed = np.any(before != after,axis=2)
            with Image.open(scan.ROOT / row['mask']) as image:
                mask = np.asarray(image.convert('L')) > 0
            assert np.array_equal(changed,mask), target
            assert int(changed.sum()) == row['operation']['changed_pixels'], target
            total_changed += int(changed.sum())
            result_hash = row['sha256']
        aliases[(row['before_sha256'], contracts[target]['native_rgba_sha256'], row['treatment'])].append((target,result_hash))
        for master in row['master_backgrounds']:
            masters[master['path']] = master
        assert (scan.ROOT / row['native_reference']).is_file(), target
    for path, master in masters.items():
        if 'sha256' in master:
            assert repair.digest(scan.ROOT / path) == master['sha256'], path
    files = {path.resolve() for path in (args.review / 'candidates').rglob('*') if path.is_file()}
    assert files == candidates, 'Unregistered or missing candidate files'
    conflicts = [rows for rows in aliases.values() if len({value for _,value in rows}) > 1]
    result = dict(schema='openyamm-spill-repair-validation-v1',targets=len(expected),
        candidates=len(candidates),changed_rgb_pixels=total_changed,alpha_changes=0,canvas_changes=0,
        active_asset_changes=0,placement_changes=0,ledger_changes=0,master_changes=0,
        checked_master_files=len(masters),alias_conflicts=conflicts,
        passed=not conflicts,manifest_sha256=repair.digest(args.review/'manifest.json'))
    repair.save(args.review/'validation.json',result)
    print(json.dumps(result,indent=2))
    assert not conflicts, 'Identical accepted/native assets acquired different repairs'


if __name__ == '__main__':
    main()
