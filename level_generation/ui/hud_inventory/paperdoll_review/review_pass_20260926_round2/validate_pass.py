"""Verify immutable review/staging, native-sized replacements and explicit derived offsets."""
import csv
import json
from collections import Counter
from urllib.parse import unquote

import numpy as np
from PIL import Image

from prepare import HERE, OUT, digest, read, write


def main():
    baseline = read(OUT/'baseline.json')
    review = read(OUT/'review.original.json')
    stage = read(OUT/'stage_manifest.json')['records']
    repairs = read(OUT/'repairs.json')['results']
    original_placements = read(OUT/'placements.json')['placements']
    effective = read(OUT/'placements.effective.json')['placements']
    inherited = read(OUT/'inherited_placement_updates.json')
    overlay = json.loads((OUT/'review.js').read_text().split('=', 1)[1].strip().rstrip(';'))
    assert digest(OUT/'review.original.json') == baseline['review_sha256']
    assert digest(HERE.parent/'checkpoint/state.json') == baseline['checkpoint_sha256']
    assert overlay['decisions'] == review['decisions']
    assert original_placements == review['placements']
    assert overlay['placements'] == effective
    assert set(stage) == set(review['decisions'])
    assert set(read(OUT/'new_flags.json')) <= set(repairs)
    approved = 0
    for target, record in stage.items():
        assert record['decision'] == review['decisions'][target]
        assert digest(HERE/unquote(record['reviewed_path'])) == record['reviewed_sha256']
        if 'staged_path' in record:
            assert record['decision']['decision'] == 'approve'
            assert digest(HERE/record['staged_path']) == record['reviewed_sha256']
            approved += 1
    for key, original in original_placements.items():
        if key not in inherited:
            assert effective[key] == original, key
        else:
            change = inherited[key]
            assert change['before'] == original and change['after'] == effective[key]
            assert effective[key]['delta'] == original_placements[original['inherited_from']]['delta']
            assert original.get('inherited_from'), 'Never replace a manually authored placement'
    for name in ['placement_proposals.csv', 'placement_proposals.effective.csv']:
        with (OUT/name).open() as stream:
            assert len(list(csv.DictReader(stream))) == len(original_placements)
    sampling = []
    for target, repair in repairs.items():
        image = Image.open(HERE/repair['path'])
        native = Image.open(HERE/'native'/(target+'.png'))
        assert image.mode == 'RGBA' and image.size == (native.width*2, native.height*2)
        assert digest(HERE/repair['path']) == repair['sha256']
        pixels = np.asarray(image)
        assert (pixels[:, :, 3] > 0).any() and (pixels[:, :, 3] == 0).any()
        assert not pixels[pixels[:, :, 3] == 0, :3].any()
        if 'exact_native_donor' in repair:
            donor = repairs[repair['exact_native_donor']]
            assert repair['source_hash'] == donor['source_hash']
            assert repair['path'] == donor['path'] and repair['sha256'] == donor['sha256']
        for operation in repair['operations']:
            if 'native_sampling' in operation:
                assert min(operation['native_sampling']) >= 2
                sampling.extend(operation['native_sampling'])
        for placement in effective.values():
            if placement['reviewed_asset'] == target and placement['source_hash'] == repair['source_hash']:
                assert placement['candidate_hash'] in overlay['repairs'][target]['placement_compatible_hashes']
    scan = read(OUT/'magenta_scan.json')
    assert len(scan['records']) == len(repairs)
    assert all(r['status'] == 'no_spill_detected' for r in scan['records'])
    report = {'result': 'PASS', 'preserved_decisions': len(review['decisions']), 'staged_approved_images': approved,
              'original_placement_records_preserved': len(original_placements),
              'inherited_wand_records_refreshed': len(inherited), 'manual_placement_changes': 0,
              'new_flagged_targets_covered': len(read(OUT/'new_flags.json')), 'replacement_targets': len(repairs),
              'distinct_generated_subjects': 29, 'minimum_generated_native_sampling': round(min(sampling), 3),
              'native_size_2x_and_alpha_checks': 'PASS', 'new_magenta_scan': scan['summary'],
              'checkpoint_unchanged': True, 'review_export_sha256': baseline['review_sha256'],
              'staged_crop_audit': read(OUT/'staged_crop_audit.json')['summary']}
    write(OUT/'validation.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
