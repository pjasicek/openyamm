"""Assemble the generated skin repair on the existing head UVs and match UV borders in surface space.

Run after export_head_repair_map.py. Geometry, UVs, weights and animation are untouched.
The AI return supplies skin colour; original hair, circlet and facial landmarks remain selected.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
import compose_textures_v2 as C

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review/head_repair_20261013'
SIZE = C.SIZE = 1024
data = np.load(ROOT / 'work/head_repair_uv3d.npz')
parts = [str(p) for p in data['parts']]
part, xyz = C.rasterise(data, tol=0)
skin = part == parts.index('Body')
original = np.asarray(Image.open(REVIEW / 'before_pfem_head_basecolor_graded.png').convert('RGB'), np.float32) / 255
generated = np.asarray(Image.open(REVIEW / 'head_atlas_imagegen_v1.png').convert('RGB').resize(
    (SIZE, SIZE), Image.Resampling.LANCZOS), np.float32) / 255
x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]

def ellipse(cx, cz, rx, rz):
    distance = np.sqrt(((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2)
    return np.clip((1.25 - distance) / 0.25, 0, 1) * (y < -0.035)

# Protect the original eyes/brows, nostrils and lips; mask boundaries are continuous in 3D.
features = np.maximum.reduce([ellipse(-0.030512, 1.46279, 0.023, 0.017),
                             ellipse(0.016218, 1.46255, 0.023, 0.017),
                             ellipse(-0.0075, 1.411, 0.029, 0.012),
                             ellipse(-0.0075, 1.434, 0.022, 0.012)])
h, s, v = C.hsv(generated)
clean = skin & (features < 0.05) & (v > 0.6) & (s < 0.55) & (h > 4) & (h < 42)
points = xyz[clean]
values = generated[clean]
assert len(points) > 1000
tree = cKDTree(points)
target_points = xyz[skin]
smooth = np.empty((len(target_points), 3), np.float32)
for start in range(0, len(target_points), 4096):
    distance, nearest = tree.query(target_points[start:start + 4096], k=96, workers=4)
    weight = np.exp(-0.5 * (distance / 0.010) ** 2) / np.maximum(distance, 0.004)
    # Very sparse hidden scalp triangles still receive the closest selected skin colour.
    total = weight.sum(1)
    empty = total < 1e-20
    weight[empty] = 0
    weight[empty, 0] = 1
    smooth[start:start + 4096] = (values[nearest] * weight[..., None]).sum(1) / weight.sum(1)[:, None]

# Reintroduce fine skin variation away from UV edges; never reintroduce the old island colour step.
known = clean.astype(np.float32)
denom = ndimage.gaussian_filter(known, 1.7)
low = np.stack([ndimage.gaussian_filter(generated[..., c] * known, 1.7) / np.maximum(denom, 1e-5)
                for c in range(3)], -1)
detail = np.clip(generated - low, -0.015, 0.015)
interior = ndimage.distance_transform_edt(clean)
detail *= np.clip((interior - 1) / 3, 0, 1)[..., None]
out = original.copy()
out[skin] = smooth + detail[skin]
# Hidden scalp retains the original hair-coloured backing beneath the hair shell.
keep_original = np.maximum.reduce([features, np.clip((1.395 - z) / 0.055, 0, 1),
                                   np.clip((z - 1.505) / 0.015, 0, 1)])
out[skin] = out[skin] * (1 - keep_original[skin, None]) + original[skin] * keep_original[skin, None]

# Guard hair/circlet and add a small skin-side gutter for bilinear/mip filtering.
distance, nearest = ndimage.distance_transform_edt(part == -1, return_indices=True)
padding = (part == -1) & (distance <= 6) & skin[nearest[0], nearest[1]]
out[padding] = out[nearest[0][padding], nearest[1][padding]]
unchanged = (part >= 0) & ~skin
assert np.array_equal(out[unchanged], original[unchanged])
assert np.isfinite(out).all()
target = ROOT / 'textures_v3/pfem_head_basecolor_repaired.png'
Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)).save(target)
report = {'source': 'head_atlas_imagegen_v1.png', 'skin_texels': int(skin.sum()),
          'sample_texels': int(clean.sum()), 'protected_other_material_texels': int(unchanged.sum()),
          'method': 'Surface-space skin continuity; original facial landmarks, hair, circlet and lower neck retained',
          'mesh_uvs_rig_clips_changed': False}
(REVIEW / 'compose_report.json').write_text(json.dumps(report, indent=2) + '\n')
print('HEAD_REPAIR_COMPOSE', report)
