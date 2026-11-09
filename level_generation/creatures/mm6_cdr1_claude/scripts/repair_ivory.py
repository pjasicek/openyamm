"""Correct horn/claw colour inside reviewed, mirrored 3D hulls; keep the accepted UVs and mesh."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import ConvexHull, cKDTree
P = Path(__file__).resolve().parents[1]
T = P / 'textures'
OLD = P / 'work/before_ivory_v3/textures'
seeds = np.load(P / 'work/ivory_seeds_v3.npz')
points, labels = seeds['points'], seeds['labels']
# Colour seed components reviewed in rest coordinates, shared across all three atlases.
selected = [0, 1, 2, 4, 5, 8, 9, 11, 17, 18, 21, 28, 29, 31, 33, 35, 42, 44, 45, 46, 47, 48]
hulls = []
for k in selected:
    q = points[labels == k].copy()
    # Two claws have fully red tips; include their measured mesh endpoints.
    if k == 21:
        q = np.vstack([q, [.2195, -1.0093, .2585], [.228, -1.02, .270]])
    if k == 28:
        q = np.vstack([q, [.2582, -.1701, .0304], [.2539, -.1733, .0433]])
    hulls.append(ConvexHull(q).equations)
mesh = json.loads((P/'work/mouth_mesh.json').read_text())
claw = np.array(mesh['vertices']); claw[:, 0] = abs(claw[:, 0])
claw = claw[(claw[:,0]>.14)&(claw[:,0]<.185)&(claw[:,1]>-.21)&(claw[:,1]<-.16)&(claw[:,2]<.086)]
hulls.append(ConvexHull(claw).equations)
(P/'work/ivory_hulls_v3.json').write_text(json.dumps([h.tolist() for h in hulls]))
report = {}
for label in ['body', 'head', 'wings']:
    data = np.load(P / 'work' / f'uvraster_ivory_{label}.npz')
    cov, pos = data['piece'] >= 0, data['pos']
    pos[..., 0] = abs(pos[..., 0])
    target = np.zeros(cov.shape, bool)
    for equations in hulls:
        # Expanded by 6 mm to cover UV interpolation and the original jagged colour boundary.
        ids = np.flatnonzero(cov)
        for eq in equations:
            ids = ids[(pos.reshape(-1, 3)[ids] @ eq[:3] + eq[3]) <= .006]
            if not len(ids):
                break
        target.flat[ids] = True
    base = np.array(Image.open(OLD / f'cdr1_{label}_basecolor_2k.png').convert('RGB'))
    hsv = np.array(Image.fromarray(base).convert('HSV')) / 255
    clean = target & (hsv[..., 1] < .25) & (hsv[..., 2] > .53)
    assert clean.sum() > 100
    # Sample clean bone by physical location, so atlas seams share their shading.
    tree = cKDTree(pos[clean])
    _, nearest = tree.query(pos[target], workers=2)
    sampled = base[clean][nearest].astype(float)
    value = sampled.max(1) / 255
    ivory = np.array([1., .955, .835]) * value[:, None]
    # Retain subtle local mottling without carrying the red stain's large luminance change.
    high = hsv[..., 2] - ndimage.gaussian_filter(hsv[..., 2], 2)
    ivory *= 1 + np.clip(high[target], -.12, .12)[:, None] * .18
    corrected = base.copy()
    corrected[target] = np.uint8(np.clip(ivory, 0, 1) * 255 + .5)
    # Pad only into unused atlas space, never onto neighbouring skin or the tooth swatch.
    near = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    padding = ~cov & ndimage.binary_dilation(target, iterations=6)
    if label == 'head':
        tile = json.loads((P / 'work/teeth_tile.json').read_text())
        x, y, w, h = [tile[k] for k in ['x', 'y', 'width', 'height']]
        padding[y:y+h, x:x+w] = False
    corrected[padding] = corrected[tuple(near[:, padding])]
    allowed = target | padding
    assert np.array_equal(base[~allowed], corrected[~allowed])
    Image.fromarray(corrected).save(T / f'cdr1_{label}_basecolor_2k.png')
    for suffix, mode in [('region_mask', 'RGBA'), ('material_classes', 'L'), ('metal_rough_2k', 'RGB')]:
        a = np.array(Image.open(OLD / f'cdr1_{label}_{suffix}.png').convert(mode))
        if suffix == 'region_mask':
            a[target] = 0
        elif suffix == 'material_classes':
            a[target] = 4
        else:
            a[target, 0] = 89
            a[target, 1] = 122
            a[target, 2] = 0
        a[padding] = a[tuple(near[:, padding])]
        assert np.array_equal(np.array(Image.open(OLD / f'cdr1_{label}_{suffix}.png').convert(mode))[~allowed], a[~allowed])
        Image.fromarray(a).save(T / f'cdr1_{label}_{suffix}.png')
    Image.fromarray(np.uint8(target)*255).save(P / 'review/ivory_v3' / f'{label}_mask.png')
    report[label] = {'corrected_texels': int(target.sum()), 'padded_texels': int(padding.sum()), 'outside_selection_unchanged': True}
    print(label, report[label], flush=True)
(P / 'review/ivory_v3/texture.json').write_text(json.dumps(report, indent=2)+'\n')
