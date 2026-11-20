"""Carry reviewed masks through the same whole-pose mapping used by verified hair crowns."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent / 'redo_2x'
old = json.loads((OUT / 'review/archer_calibration_before_verified_crowns.json').read_text())
records = json.loads((OUT / 'registration.json').read_text())
manifest = json.loads((OUT / 'review/manifest_before_verified_crowns.json').read_text())
archive = OUT / 'review/hair_authoring_before_verified_crowns.json'
if not archive.exists():
    archive.write_text((OUT / 'hair_authoring.json').read_text())
hair = json.loads(archive.read_text())
changed = []
for name, record in records.items():
    clean = Image.open(record['clean_path']).convert('RGBA')
    anatomy = old['anatomical_sheet_calibration'][record['batch']]
    first, second = [anatomy['landmarks'][label] for label in anatomy['scale_pair']]
    axes = anatomy['axes']
    factor = 2 / (np.linalg.norm((np.array(second['clean']) - first['clean'])[axes]) /
                  np.linalg.norm((np.array(second['native']) - first['native'])[axes]))
    old_size = np.array([round(v * factor) for v in clean.size])
    old_effective = old_size / clean.size
    position = old['frame_translation_calibration'][name]
    old_translate = np.round(np.array(position['native']) * 2 -
                             np.array(position['clean']) * old_effective).astype(int)
    old_scaled = clean.convert('RGBa').resize(tuple(old_size), Image.Resampling.LANCZOS).convert('RGBA')
    bounds = old_scaled.getbbox()
    old_origin = np.minimum([0, 0], old_translate + np.array(bounds[:2]) - 4)
    old_crop = [*(old_translate - old_origin + np.array(bounds[:2]) - 4),
                *(old_translate - old_origin + np.array(bounds[2:]) + 4)]
    assert old_crop == manifest['frames'][name]['crop_in_aligned_px'], name
    new_effective = np.array([round(v * record['scale']) for v in clean.size]) / clean.size
    new_translate = np.array(record['translate'])
    new_origin = np.array(record['canvas_origin_px'])
    if (np.array_equal(old_translate, new_translate) and np.array_equal(old_effective, new_effective)
            and np.array_equal(old_origin, new_origin)):
        continue

    def mapped(points):
        return np.round((np.array(points) + old_origin - old_translate) / old_effective * new_effective +
                        new_translate - new_origin).astype(int).tolist()

    box = hair['regions'][name]
    hair['regions'][name] = sum(mapped([box[:2], box[2:]]), [])
    for key in ('feather_exclusions', 'hair_inclusions', 'cloth_exclusions'):
        if name in hair['corrections'].get(key, {}):
            hair['corrections'][key][name] = mapped(hair['corrections'][key][name])
    changed.append(name)
hair['method'] += (' Reviewed hair and feather selections carried through the same whole-pose uniform '
                   'scale and translation after verified scalp correspondences.')
(OUT / 'hair_authoring.json').write_text(json.dumps(hair, indent=2) + '\n')
(OUT / 'review/hair_coordinate_reprojection.json').write_text(json.dumps(dict(
    frames=changed, old_mapping_verified_against_previous_manifest_crop=True,
    method='Same clean-source affine mapping as the registered complete pose; every recovered old alpha crop '
           'and its four-pixel atlas padding exactly match the previous manifest.'), indent=2) + '\n')
print('Remapped', len(changed), 'reviewed selections.')
