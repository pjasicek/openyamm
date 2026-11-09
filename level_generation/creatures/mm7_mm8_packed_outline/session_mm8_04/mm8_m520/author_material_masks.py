"""Author Cyclops leather coverage from delivered enhanced RGB, preserving skin.

Native ACT colours supply tone samples only, never a resized spatial mask.
The green eye supplies an enhanced-image face exclusion landmark.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

root = Path(__file__).resolve().parent
repo = root.parents[4]
sys.path.insert(0, str(repo / 'level_generation/creatures/mm8_remaining'))
import native_materials
import native_package

parser = argparse.ArgumentParser()
parser.add_argument('--sample', action='store_true')
args = parser.parse_args()
sources = json.loads((root / 'sources.json').read_text())
reg = json.loads((root / 'registration.json').read_text())
config = json.loads((root / 'material_settings.json').read_text())
palettes = {key: np.frombuffer((repo / item['path']).read_bytes()[:768], np.uint8).reshape(256, 3)
            .astype(float) for key, item in sources['palette_sources'].items()}
luma_weights = np.array([.2126, .7152, .0722])
indices = np.arange(55, 86)
base_luma = palettes['521'][indices] @ luma_weights
tones = {key: np.median(value[indices] / np.maximum(base_luma[:, None], 1), axis=0)
         for key, value in palettes.items()}
records = {}
for name, record in reg.items():
    if args.sample and name != 'm520sa0':
        continue
    master = Image.open(root / 'aligned_2x' / f'{name}.png').convert('RGBA')
    pixels = np.asarray(master)
    rgb = pixels[:, :, :3].astype(float)
    r, g, b = np.moveaxis(rgb, -1, 0)
    leather = np.minimum((r - 1.55 * g) / 8, (r - b - 18) / 8).clip(0, 1)
    leather *= ((g - 1.12 * b) / 6).clip(0, 1)
    leather[pixels[:, :, 3] == 0] = 0
    eye = (pixels[:, :, 3] > 240) & (g > r * 1.18) & (g > b * 1.25) & (g > 30)
    labels, count = ndimage.label(eye)
    eyes = []
    for label in range(1, count + 1):
        y, x = np.where(labels == label)
        if 1 <= len(x) <= 60:
            eyes.append((len(x), float(x.mean()), float(y.mean())))
    exclusion = np.ones(leather.shape)
    if eyes:
        _, ex, ey = max(eyes)
        y, x = np.indices(leather.shape)
        exclusion[((x - ex) / 26) ** 2 + ((y - ey - 4) / 34) ** 2 < 1] = 0
        # When the crown bends toward the chest, pendant disks can overlap the
        # face ellipse. Their copper chroma remains a separate material.
        copper = (r > 1.72 * g) & (g > 1.6 * b) & (r > 40)
        exclusion[copper] = 1
    # A colour coverage gate removes native-neighbour leakage onto exposed skin.
    coverage = native_materials.masks(master, config).astype(float) / 255
    brown = ((r - 1.33 * g) / 9).clip(0, 1) * ((g - b) / 8).clip(0, 1)
    coverage *= brown * exclusion
    # Native brown leather can be restored with mauve reflected bands. Include
    # their enhanced colour samples so the blue/red ACT changes cover them too.
    mauve = ((r - 1.35 * g) / 8).clip(0, 1) * ((b - g - 8) / 8).clip(0, 1)
    mauve[pixels[:, :, 3] == 0] = 0
    leather = np.maximum(leather, mauve) * exclusion
    leather = ndimage.gaussian_filter(leather, .35)
    leather[pixels[:, :, 3] == 0] = 0
    coverage = np.maximum(coverage, leather)
    coverage[pixels[:, :, 3] == 0] = 0
    mask = Image.fromarray(np.round(coverage * 255).astype(np.uint8))
    mask.save(root / 'masks_2x' / f'{name}.png')
    for key in palettes:
        if key == '521':
            preview = master.copy()
        else:
            ordinary = np.asarray(native_materials.recolor(master, mask, int(key), config))[:, :, :3].astype(float)
            target = (rgb @ luma_weights)[:, :, None] * tones[key]
            out = ordinary * (1 - leather[:, :, None]) + target * leather[:, :, None]
            preview_pixels = np.array(master)
            preview_pixels[:, :, :3] = np.round(out).clip(0, 255).astype(np.uint8)
            preview = Image.fromarray(preview_pixels)
        preview.save(root / 'previews' / f'{name}_{key}.png')
        assert np.array_equal(np.asarray(preview)[:, :, 3], pixels[:, :, 3])
    records[name] = dict(face_landmark=eyes, mask_pixels=int((coverage > .5).sum()))
if not args.sample:
    processing = json.loads((root / 'processing.json').read_text())
    processing['materials'].update(regions=['ACT-varying leather pendants, straps, wrist bands, belt and warm fur/wrap samples'],
        protected=['Skin, green eye, pale teeth and neutral rock; true alpha'],
        native_palette_review='All native ACT 521/522/523 inspected; blue and red pendant/band interiors require enhanced RGB leather coverage.')
    processing['materials']['local_authorship'] = dict(script=Path(__file__).name,
        method='Enhanced warm chroma coverage plus native ACT tone samples; green eye face exclusion; no spatial native mask transfer.',
        tone_palette_indices=indices.tolist(), tone_rgb_per_base_luma={k: v.tolist() for k, v in tones.items()}, frames=records)
    (root / 'processing.json').write_text(json.dumps(processing, indent=2) + '\n')
    config['local_semantic_mask_author'] = processing['materials']['local_authorship']
    (root / 'material_settings.json').write_text(json.dumps(config, indent=2) + '\n')
    native_package.ROOT = root
    native_package.run()
    draft = json.loads((root / 'draft_manifest.json').read_text())
    draft.update(logical_canvas=sources['logical_canvas'], logical_pivot=sources['logical_pivot'],
                 placement_registration='registration.json', generated_sampling_min=min(min(x['effective_sampling_xy']) for x in reg.values()),
                 native_palette_exports=sources['staged_native_palettes'], review_evidence='review/acceptance.json')
    draft.pop('viewer', None)
    (root / 'draft_manifest.json').write_text(json.dumps(draft, indent=2) + '\n')
print('Authored enhanced masks:', len(records))
