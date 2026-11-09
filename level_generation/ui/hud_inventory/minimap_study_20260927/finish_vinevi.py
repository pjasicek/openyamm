"""Deterministic approximation of vinevi's layered Krita processing, with fixed object alpha."""
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
OUT = HERE / 'new_sorpigal'
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


import sys
sys.path.insert(0, str(ROOT))
from level_generation.minimaps.processing import rgba, grade, random_pick, composite, openraster


def main():
    recipe = json.loads((HERE/'vinevi_recipe.json').read_text())
    capture = json.loads((OUT/'vinevi_capture.json').read_text())
    assert capture['recipe']['sun'] == recipe['sun'], 'Rerender after changing lights'
    assert capture['recipe']['world'] == recipe['world'], 'Rerender after changing fill'
    assert capture['recipe']['render'] == recipe['render'], 'Rerender after changing render settings'
    assert capture['recipe']['terrain_flat_normal_blend'] == recipe['terrain_flat_normal_blend'], \
        'Rerender after changing terrain normals'
    size, export = recipe['render']['size'], recipe['export_size']
    terrain = np.asarray(Image.open(OUT/'vinevi_terrain_master.png').convert('RGBA'), dtype=np.float32)/255
    objects = np.asarray(Image.open(OUT/'vinevi_objects_master.png').convert('RGBA'), dtype=np.float32)/255
    assert terrain.shape == objects.shape == (size, size, 4)
    assert objects[:, :, 3].max() == 1 and np.count_nonzero(objects[:, :, 3]) > 100
    raw = composite(terrain, objects)
    levels = recipe['object_levels']
    corrected = objects.copy()
    corrected[:, :, :3] = np.clip((objects[:, :, :3]-levels['black']) /
                                 (levels['white']-levels['black']), 0, 1)**(1/levels['gamma'])
    corrected = grade(corrected, recipe)
    assert np.array_equal(corrected[:, :, 3], objects[:, :, 3])
    clean_terrain = grade(terrain, recipe)
    picked_terrain = grade(random_pick(terrain, recipe['terrain_random_pick']), recipe)
    clean_terrain[:, :, 3] = picked_terrain[:, :, 3] = 1
    clean = composite(clean_terrain, corrected)
    finished = composite(picked_terrain, corrected)
    outputs = {}
    for name, image in [('vinevi_raw', raw), ('vinevi_no_pick', clean), ('vinevi', finished)]:
        image.save(OUT/(name+'_master.png'))
        path = OUT/(name+'_x2.png')
        image.resize((export, export), Image.Resampling.LANCZOS).save(path)
        outputs[name+'_x2'] = dict(file=path.name, sha256=sha(path))
    previous = OUT/'vinevi_v1/vinevi_x2.png'
    outputs['vinevi_previous_x2'] = dict(file=str(previous.relative_to(OUT)), sha256=sha(previous))
    rgba(corrected).save(OUT/'vinevi_objects_processed_master.png')
    rgba(picked_terrain).save(OUT/'vinevi_terrain_processed_master.png')
    openraster(OUT/'new_sorpigal_vinevi.ora', picked_terrain, corrected, finished)
    original = np.array(Image.open(OUT/'original.png').convert('RGB'), dtype=float)/255
    mask = ((original[:, :, 1] > 1.18*original[:, :, 0]) &
            (original[:, :, 1] > 1.5*original[:, :, 2]) & (original[:, :, 1] > .25))
    metrics = {}
    for name in ['original', 'blender_styled_x2', 'vinevi_raw_x2', 'vinevi_no_pick_x2', 'vinevi_x2']:
        rgb = np.array(Image.open(OUT/(name+'.png')).convert('RGB').resize((512, 512)), dtype=float)/255
        luma = rgb @ np.array([.2126, .7152, .0722])
        saturation = (rgb.max(-1)-rgb.min(-1))/np.maximum(rgb.max(-1), 1e-6)
        metrics[name] = dict(grass_luma_percentiles=np.percentile(luma[mask]*255, [10, 50, 90]).tolist(),
                             grass_median_saturation=float(np.median(saturation[mask])))
    source = json.loads((OUT/'sources.json').read_text())
    assert all(sha(ROOT/path) == expected for path, expected in source['sources'].items())
    target = 'worlds-mm6--icons--oute3.bmp'
    expected = source['sources']['assets_dev/worlds/mm6/icons_x2/oute3.bmp']
    assert json.loads((HERE.parent/'accepted_icons.json').read_text())['records'][target]['sha256'] == expected
    assert json.loads((HERE.parent/'checkpoint/state.json').read_text())['staged_targets'][target]['sha256'] == expected
    report = dict(status='comparison_only_not_accepted', recipe=recipe, outputs=outputs, capture=capture,
                  grass_metrics=metrics, processed_object_alpha_exactly_preserved=True,
                  terrain_neighbor_radius_x2_pixels=recipe['terrain_random_pick']['radius_master_pixels']*export/size,
                  object_xy_warp=False, runtime_and_target_acceptance_unchanged=True,
                  implementation='Independent Python approximation of the described Krita operations; not its exact filter code.',
                  raw_layers={name: sha(OUT/name) for name in ['vinevi_terrain_master.png', 'vinevi_objects_master.png']})
    (OUT/'vinevi_comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    comparison = json.loads((OUT/'comparison.json').read_text())
    comparison['outputs'].update(outputs)
    comparison['vinevi_process'] = report
    (OUT/'comparison.json').write_text(json.dumps(comparison, indent=2)+'\n')
    (OUT/'data.js').write_text('window.MINIMAP_STUDY = '+json.dumps(comparison)+';\n')
    print(json.dumps(dict(outputs=list(outputs), metrics=metrics, unchanged_object_alpha=True), indent=2))


if __name__ == '__main__':
    main()
