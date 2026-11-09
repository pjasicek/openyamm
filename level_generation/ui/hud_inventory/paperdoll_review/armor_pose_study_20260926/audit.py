"""Read-only armor-pair feasibility audit and isolated compositing probes; no approvals or installation."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
HERE = OUT.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools/mm9_import_discovery'))
import audit_mm9_armor_pose_pairs as pair_tools

SNAPSHOT = HERE / 'acceptance_snapshot_20260926_1322'
PROBES = {'7item066v1', '7item076v1', '7item078v1', '7item078v2', '7item078v3', '7item078v4',
          '7item078v5', '7item299v5', '6chain3v1'}


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().rstrip(';'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_pixels(image):
    pixels = np.asarray(image.convert('RGBA')).copy()
    pixels[pixels[:, :, 3] == 0] = 0
    return pixels


def main():
    catalog = js(HERE / 'catalog.js')
    snapshot = js(SNAPSHOT / 'review.js')
    scope = json.loads((SNAPSHOT / 'completion_audit.json').read_text())
    states = {r['name']: r['status'] for r in scope['all_equipment']}
    checkpoint_before = digest(HERE.parent / 'checkpoint/state.json')
    overlay_before = digest(SNAPSHOT / 'review.js')
    rows = []
    for empty in (r for r in scope['all_equipment'] if 'Armor, empty hands' in r['groups']):
        empty_name = empty['name']
        assert empty_name.endswith('a')
        held_name = empty_name[:-1]
        a, b = catalog['assets'][empty_name], catalog['assets'][held_name]
        base_record = snapshot['staged'][a['id']]
        assert base_record['decision']['decision'] == 'approve'
        base_path = HERE / base_record['staged_path']
        assert digest(base_path) == base_record['reviewed_sha256']
        donor_record = snapshot['staged'].get(b['id'])
        donor_path = HERE / (donor_record['staged_path'] if donor_record and donor_record.get('staged_path') else
                            snapshot['repairs'][b['id']]['path'] if b['id'] in snapshot['repairs'] else b['candidate'])
        native_empty = Image.open(HERE / a['native']).convert('RGBA')
        native_held = Image.open(HERE / b['native']).convert('RGBA')
        base = Image.open(base_path).convert('RGBA')
        donor = Image.open(donor_path).convert('RGBA')
        assert native_empty.size == native_held.size
        assert base.size == donor.size == (native_empty.width * 2, native_empty.height * 2)
        native_diff = np.any(visible_pixels(native_empty) != visible_pixels(native_held), axis=2)
        allowed_native = pair_tools.derive_validated_pose_change_mask(
            native_held, native_empty, native_held, native_empty)
        allowed = np.repeat(np.repeat(allowed_native, 2, axis=0), 2, axis=1)
        # The common-region replacement in the MM9 tool also reapplies native alpha. Do not use it here:
        # the accepted restored RGBA, including its soft contour, is the immutable base instead.
        p = np.asarray(base).copy()
        q = np.asarray(donor)
        old_diff = np.any(p != q, axis=2)
        alpha_diff = p[:, :, 3] != q[:, :, 3]
        probe = p.copy()
        probe[allowed] = q[allowed]
        assert np.array_equal(probe[~allowed], p[~allowed])
        rows.append({'empty': empty_name, 'held': held_name, 'doll_type': empty['uses'][0]['doll_type'],
            'uses': empty['uses'], 'native_size': list(native_empty.size), 'exact_2x_size': list(base.size),
            'native_pair_identical': not bool(native_diff.any()), 'native_changed_pixels': int(native_diff.sum()),
            'provisional_arm_mask_pixels_2x': int(allowed.sum()), 'held_status': states[held_name],
            'base_path': str(base_path.relative_to(HERE)), 'base_sha256': digest(base_path),
            'held_candidate_path': str(donor_path.relative_to(HERE)), 'held_candidate_sha256': digest(donor_path),
            'existing_held_rgba_differences_outside_arm': int((old_diff & ~allowed).sum()),
            'existing_held_alpha_differences_outside_arm': int((alpha_diff & ~allowed).sum()),
            'probe_differences_outside_arm': 0,
            'strategy': 'reuse_accepted_file' if not native_diff.any() else 'local_arm_transfer_needs_visual_review'})
        if held_name not in PROBES:
            continue
        proof = OUT / 'probes' / held_name
        proof.mkdir(parents=True, exist_ok=True)
        Image.fromarray(probe).save(proof / 'composite-probe.png')
        Image.fromarray(allowed.astype('uint8') * 255).save(proof / 'allowed-mask.png')
        marked = p.copy()
        marked[allowed] = (255, 115, 45, 255)
        images = [base, donor, Image.fromarray(probe), Image.fromarray(marked)]
        width, height = base.size
        sheet = Image.new('RGB', ((width + 12) * 4, height + 48), (43, 47, 53))
        draw = ImageDraw.Draw(sheet)
        for i, (label, im) in enumerate(zip(['Accepted empty', 'Existing held', 'Arm-only probe', 'Allowed edit area'], images)):
            x = i * (width + 12) + 6
            draw.text((x, 6), label, fill='white')
            sheet.paste(im, (x, 30), im)
        sheet.save(proof / 'comparison.png')
    summary = {'pairs': len(rows), 'body_types': 5, 'same_native_canvas_all': True,
        'identical_native_pairs': sum(r['native_pair_identical'] for r in rows),
        'different_native_pairs': sum(not r['native_pair_identical'] for r in rows),
        'pending_held_exact_reuse': sum(r['native_pair_identical'] and r['held_status'] == 'unreviewed' for r in rows),
        'pending_held_arm_edit': sum(not r['native_pair_identical'] and r['held_status'] == 'unreviewed' for r in rows),
        'existing_held_with_changes_outside_arm': sum(r['existing_held_rgba_differences_outside_arm'] > 0 for r in rows),
        'existing_held_with_alpha_changes_outside_arm': sum(r['existing_held_alpha_differences_outside_arm'] > 0 for r in rows),
        'all_compositing_probes_exact_outside_arm': True, 'imagegen_calls': 0,
        'active_browser_changed': False, 'approvals_changed': False, 'ledger_changed': False,
        'limitation': 'Native-derived arm masks are provisional; exact copying proves preservation but not donor-arm quality or seams.'}
    assert digest(HERE.parent / 'checkpoint/state.json') == checkpoint_before
    assert digest(SNAPSHOT / 'review.js') == overlay_before
    (OUT / 'audit.json').write_text(json.dumps({'summary': summary, 'pairs': rows}, indent=2) + '\n')
    with (OUT / 'pairs.csv').open('w', newline='') as stream:
        keys = ['empty', 'held', 'doll_type', 'native_pair_identical', 'held_status', 'strategy',
                'existing_held_rgba_differences_outside_arm', 'existing_held_alpha_differences_outside_arm']
        writer = csv.DictWriter(stream, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
