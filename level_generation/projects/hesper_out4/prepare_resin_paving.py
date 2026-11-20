"""Prepare the Crown's `resin_paving` terrain material (THE_CROWN.md section 8) from its CC0 photoscan.

    python3 level_generation/projects/hesper_out4/prepare_resin_paving.py

Source: Poly Haven `slate_floor` (CC0, 2.29 m; assets_source/engine/terrain_materials/sources.yml), polished dark
slate slabs with visible grout. tools/terrain_materials.py's prepare packs it into albedo_height.png and
normal_ao_rough.png as for every library material, but into a scratch library (the runtime library is assets_dev's,
which Hesper never touches). Then the slabs are turned to violet-black resin and the joints, the height map's low band,
painted violet in the albedo: the engine reads a terrain emissive only as {color, threshold} on "albedo red minus
blue", which cannot pick out violet joints, so the paving does not glow (R3 review, P3.md "Remaining fixes" 4).
Prints the library entry for level_generation/projects/hesper_stage/terrain_library.yml.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import terrain_materials  # noqa: E402

MATERIAL = 'resin_paving'
SLAB = np.array([30, 26, 38]) / 255.0          # the swatch's polished black resin (crown_terrain.MATERIALS paving)
JOINT = np.array([140, 92, 242]) / 255.0       # the joints' violet (THE_CROWN.md section 8)
JOINT_STRENGTH = 0.4

with tempfile.TemporaryDirectory() as scratch:
    terrain_materials.LIBRARY = Path(scratch) / 'library.yml'
    terrain_materials.prepare([MATERIAL])
    entry = yaml.safe_load(terrain_materials.LIBRARY.read_text())['materials'][MATERIAL]

directory = ROOT / 'assets_source/engine/terrain_materials' / MATERIAL
path = directory / 'albedo_height.png'
pixels = np.asarray(Image.open(path).convert('RGBA'), dtype=np.float64) / 255.0
colour, height = pixels[..., :3], pixels[..., 3]
# The slabs: the photo's own light and dark detail (luminance about its mean) on the resin's violet-black, so the
# slate's brown goes and the stone's grain stays.
luminance = colour @ np.array([0.2126, 0.7152, 0.0722])
detail = np.clip(luminance / max(luminance.mean(), 1e-4), 0.35, 2.2) ** 0.8
resin = np.clip(SLAB[None, None, :] * 2.4 * detail[..., None], 0.0, 1.0)
# The joints: the grout lies in the height map's lowest band; a soft mask so they stay thin lines.
# Pits inside a slab lie as low as its grout, but only the grout is one network: keep the low band's large connected
# parts (the joints) and drop the small ones (pits and scratches).
low = np.percentile(height, 9.0)
joints = np.clip((low + 0.05 - height) / 0.08, 0.0, 1.0)
labels, count = ndimage.label(joints > 0.5)
sizes = ndimage.sum(np.ones_like(joints), labels, range(1, count + 1))
network = np.isin(labels, 1 + np.flatnonzero(sizes >= 4000))
joints = ndimage.gaussian_filter(np.where(ndimage.binary_dilation(network, iterations=1), joints, 0.0), 1.0,
                                 mode='wrap')
resin = resin * (1.0 - JOINT_STRENGTH * joints[..., None]) + JOINT * JOINT_STRENGTH * joints[..., None]
Image.fromarray(np.clip(np.dstack([resin, height]) * 255.0 + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(path)
entry['mean_color'] = [round(float(value), 4) for value in resin.reshape(-1, 3).mean(axis=0)]
print(yaml.safe_dump({MATERIAL: entry}, sort_keys=False))
print(f'joints cover {float((joints > 0.5).mean()) * 100:.1f} % of the texture')
