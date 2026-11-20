#!/usr/bin/env python3
"""Wing outline and texture from the restored native spread-wing frame (wdmflyd0, 2x, image-left wing = the
creature's right wing). Wing pixels: sprite alpha, dark and low-saturation (membrane and finger bones), largest
component left of the shoulder, holes closed. Body/spike pixels inside the wing outline are inpainted from the
nearest membrane pixel. Writes work/wing_mesh.json (outline polygon, vertices and triangles in sprite px, image y down) and
textures/wing_<tier>_basecolor.png (1024² RGB; the mesh carries the outline) for palettes 684/685/683. The membrane mesh is the
traced outline plus an interior point grid, Delaunay-triangulated and clipped to the mask (work/wing_mesh.json)."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parents[1] / 'mm6_wdm'
FRAME = 'wdmflyd0'
ROOT_X = 300                      # sprite px: wing root column (behind the shoulder spikes)
GAIN = 1.7                        # sprites carry baked shading; the model is lit at runtime
im = np.asarray(Image.open(SRC / 'trimmed_2x' / f'{FRAME}.png').convert('RGBA')).astype(np.float32) / 255
rgb, alpha = im[..., :3], im[..., 3] > 0.5
mx, mn = rgb.max(2), rgb.min(2)
sat = (mx - mn) / np.maximum(mx, 1e-4)
hue = np.zeros(mx.shape, np.float32)
d = np.maximum(mx - mn, 1e-6)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
purple = (hue > 255) & (hue < 345) & (sat > 0.22) & (mx > 0.16)
spike = ndimage.binary_dilation((mx > 0.52) & (sat < 0.35), iterations=3)
region = alpha.copy(); region[:, ROOT_X:] = False; region[250:, :] = False
body = ndimage.binary_opening(purple, iterations=2) & region
lab, n = ndimage.label(region & ~ndimage.binary_dilation(body, iterations=2))
sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
wing = lab == (1 + int(np.argmax(sizes)))
wing = ndimage.binary_fill_holes(ndimage.binary_closing(wing, iterations=4)) & region
wing = ndimage.binary_opening(wing, iterations=1)
membrane = wing & ~spike & ~purple & (sat < 0.4)
from scipy.spatial import Delaunay


def trace(mask):
    """Moore-neighbour boundary trace of the single component; returns (x, y) pixel centres in order."""
    ys, xs = np.nonzero(mask)
    start = (ys.min(), xs[ys == ys.min()].min())
    dirs = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    pts, cur, d = [start], start, 6
    for _ in range(200000):
        for k in range(8):
            nd = (d + k) % 8
            ny, nx = cur[0] + dirs[nd][0], cur[1] + dirs[nd][1]
            if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx]:
                cur, d = (ny, nx), (nd + 6) % 8
                break
        if cur == start:
            break
        pts.append(cur)
    return np.array([(x, y) for y, x in pts], np.float64)


def rdp(points, eps):
    if len(points) < 3:
        return points
    a, b = points[0], points[-1]
    ab = b - a; L = np.linalg.norm(ab)
    dist = (np.abs(np.cross(ab, points - a)) / L) if L > 0 else np.linalg.norm(points - a, axis=1)
    i = int(np.argmax(dist))
    if dist[i] > eps:
        return np.vstack([rdp(points[:i + 1], eps)[:-1], rdp(points[i:], eps)])
    return np.vstack([a, b])


ring = trace(wing)
half = len(ring) // 2
poly = np.vstack([rdp(ring[:half + 1], 1.0)[:-1], rdp(np.vstack([ring[half:], ring[:1]]), 1.0)[:-1]])
# Interior points on a jittered-free grid, then Delaunay; keep triangles whose centroid lies in the mask.
dist_in = ndimage.distance_transform_edt(wing)
STEP = 14
gy, gx = np.mgrid[0:wing.shape[0]:STEP, 0:wing.shape[1]:STEP]
inner = dist_in[gy, gx] > STEP * 0.45
pts = np.vstack([poly, np.stack([gx[inner], gy[inner]], 1).astype(np.float64)])
tri = Delaunay(pts).simplices
cent = pts[tri].mean(1)
keep = wing[np.clip(cent[:, 1].round().astype(int), 0, wing.shape[0] - 1),
            np.clip(cent[:, 0].round().astype(int), 0, wing.shape[1] - 1)]
tri = tri[keep]
ys, xs = np.nonzero(wing)
print('wing px', int(wing.sum()), 'bbox x', xs.min(), xs.max(), 'y', ys.min(), ys.max(), 'polygon', len(poly))
# Texture: membrane colours, occluded pixels filled from the nearest membrane pixel.
good = membrane
_, (iy, ix) = ndimage.distance_transform_edt(~good, return_indices=True)
x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
meta = {'frame': FRAME, 'root_x': ROOT_X, 'bbox': [int(x0), int(y0), int(x1), int(y1)],
        'polygon': [[float(x), float(y)] for x, y in poly], 'image_size': [int(im.shape[1]), int(im.shape[0])],
        'vertices': pts.tolist(), 'triangles': tri.tolist()}
(HERE / 'work').mkdir(exist_ok=True); (HERE / 'textures').mkdir(exist_ok=True)
json.dump(meta, open(HERE / 'work' / 'wing_mesh.json', 'w'))
print('mesh verts', len(pts), 'tris', len(tri))
grow = ndimage.binary_dilation(wing, iterations=3)
for tier, palette in (('a', None), ('b', '685'), ('c', '683')):
    if palette is None:
        src = rgb
    else:
        def wing_median(pal):
            v = np.asarray(Image.open(SRC / 'native_variants' / f'{FRAME}_{pal}.png').convert('RGBA'), np.float32) / 255
            c, a = v[..., :3], v[..., 3] > 0.5
            vmx, vmn = c.max(2), c.min(2)
            m = a & (vmx < 0.45) & ((vmx - vmn) / np.maximum(vmx, 1e-4) < 0.45)
            m[:, v.shape[1] // 2 - 40:] = False; m[int(v.shape[0] * 0.45):, :] = False
            return np.median(c[m], 0)
        ratio = wing_median(palette) / np.maximum(wing_median('684'), 1e-3)
        print('tier', tier, 'membrane ratio', ratio.round(3))
        src = np.clip(rgb * ratio, 0, 1)
    out = np.clip(src[iy, ix] * GAIN, 0, 1)
    rgba = np.concatenate([out, grow[..., None].astype(np.float32)], -1)[y0:y1, x0:x1]
    img = Image.fromarray((rgba[..., :3] * 255 + 0.5).astype(np.uint8))
    img = img.resize((1024, 1024), Image.LANCZOS)        # power of two RGB for the runtime mip chain
    img.save(HERE / 'textures' / f'wing_{tier}_basecolor.png')
print('WROTE', HERE / 'work' / 'wing_mesh.json')
