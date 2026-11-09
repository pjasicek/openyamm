#!/usr/bin/env python3
"""Tier base colour by projecting the Codex HD views onto the mesh (no Meshy credits). Usage: project_views.py <tier>
Tier 1's Meshy retexture was painted on an early low-poly upload with poorly packed UVs and reads blotchy. Input:
work/t<N>_surface.npz from finish_tier.py (the High point and normal each LOD0 texel shows). Each reference view's camera
yaw is found by matching its alpha silhouette against High's (elevation from the brief); the silhouette bounds map
onto the alpha bounds. Views are blended per texel, weighted by facing and visibility (z-buffer of High per view).
Texels no view sees keep the baked Meshy colour (work/textures/satchel_t<N>_basecolor_meshy.png from
finish_tier.py). Writes work/textures/satchel_t<N>_projected.png and work/t<N>_projection.json."""
import json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import ROOT

N = int(sys.argv[1])
WORK = os.path.join(ROOT, 'work'); TEX = os.path.join(WORK, 'textures')
REF = os.path.join(ROOT, 'references_hd', f't{N}')
# view file, elevation (deg), yaw offset from the front view (deg; camera at (sin a, -cos a) around the model).
# A round pouch's silhouette barely changes with yaw, so one front yaw is fitted jointly over all views (the brief's
# three-quarter camera sits 35 degrees toward the bag's right; the side view shows its left), then each view is
# refined within +-10 degrees.
VIEWS = [('00_three_quarter.png', 30, -35),
         ('01_front.png', 20, 0),
         ('02_side.png', 20, 90),
         ('03_back.png', 20, 180)]
ZRES = 768

d = np.load(os.path.join(WORK, f't{N}_surface.npz'))
pos, nrm, valid, verts, tris = d['pos'], d['nrm'], d['valid'], d['verts'], d['tris']
RES = pos.shape[0]


def frame(yaw, elev):
    a, e = math.radians(yaw), math.radians(elev)
    to_cam = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    right = np.array([math.cos(a), math.sin(a), 0.0])
    up = np.cross(to_cam, right)
    return to_cam, right, up / np.linalg.norm(up)


def silhouette(right, up, size=128):
    xy = np.stack([verts @ right, verts @ up], 1)
    lo, hi = xy.min(0), xy.max(0)
    p = (xy - lo) * ((size - 1) / (hi - lo)); p[:, 1] = size - 1 - p[:, 1]
    im = Image.new('L', (size, size)); draw = ImageDraw.Draw(im)
    for t in tris:
        draw.polygon([tuple(p[i]) for i in t], fill=255)
    return np.asarray(im) > 0, lo, hi


def zbuffer(to_cam, right, up, lo, hi):
    """Largest depth toward the camera per pixel (larger = nearer), over High's triangles."""
    q = np.stack([(verts @ right - lo[0]) / (hi[0] - lo[0]) * (ZRES - 1),
                  (verts @ up - lo[1]) / (hi[1] - lo[1]) * (ZRES - 1), verts @ to_cam], 1)
    z = np.full((ZRES, ZRES), -np.inf)
    for t in tris:
        a, b, c = q[t]
        x0, x1 = int(max(0, math.floor(min(a[0], b[0], c[0])))), int(min(ZRES - 1, math.ceil(max(a[0], b[0], c[0]))))
        y0, y1 = int(max(0, math.floor(min(a[1], b[1], c[1])))), int(min(ZRES - 1, math.ceil(max(a[1], b[1], c[1]))))
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.01) & (w1 >= -0.01) & (w2 >= -0.01)
        depth = w0 * a[2] + w1 * b[2] + w2 * c[2]
        sub = z[y0:y1 + 1, x0:x1 + 1]
        sub[inside] = np.maximum(sub[inside], depth[inside])
    return z


def reference(name):
    ref = Image.open(os.path.join(REF, name)).convert('RGBA')
    alpha = np.asarray(ref)[..., 3]
    ys, xs = np.nonzero(alpha > 128)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    mask = np.asarray(ref.crop(box).getchannel('A').resize((128, 128), Image.BILINEAR)) > 128
    return ref, box, mask, (box[2] - box[0]) / (box[3] - box[1])


def score(yaw, elev, mask, ref_aspect):
    _, right, up = frame(yaw, elev)
    sil, lo, hi = silhouette(right, up)
    aspect = (hi - lo)[0] / (hi - lo)[1]
    return (sil & mask).sum() / (sil | mask).sum() * min(aspect, ref_aspect) / max(aspect, ref_aspect), lo, hi


refs = {name: reference(name) for name, _, _ in VIEWS}
curves = {name: np.array([score(y, elev, refs[name][2], refs[name][3])[0] for y in range(0, 360, 4)])
          for name, elev, _ in VIEWS}
front = max(range(0, 360, 4), key=lambda f: sum(curves[name][((f + off) % 360) // 4] for name, _, off in VIEWS))
print('PROJECT joint front yaw', front, flush=True)
report = {'front_yaw': front}
weight_sum = np.zeros((RES, RES)); colour_sum = np.zeros((RES, RES, 3))
size = np.ptp(verts, axis=0).max()
for name, elev, off in VIEWS:
    ref, box, mask, ref_aspect = refs[name]
    yaw, (best, lo, hi) = max(((y, score(y, elev, mask, ref_aspect)) for y in range(front + off - 10, front + off + 11, 2)),
                              key=lambda t: t[1][0])
    report[name] = {'yaw': yaw % 360, 'score': round(float(best), 3)}
    print('PROJECT', name, 'yaw', yaw % 360, 'score', round(float(best), 3), flush=True)
    to_cam, right, up = frame(yaw, elev)
    u = (pos @ right - lo[0]) / (hi[0] - lo[0])
    v = (pos @ up - lo[1]) / (hi[1] - lo[1])
    px = np.clip((box[0] + u * (box[2] - box[0])).astype(int), 0, ref.width - 1)
    py = np.clip((box[3] - v * (box[3] - box[1])).astype(int), 0, ref.height - 1)
    sample = np.asarray(ref, np.float64)[py, px] / 255
    z = zbuffer(to_cam, right, up, lo, hi)
    zx = np.clip((u * (ZRES - 1)).round().astype(int), 0, ZRES - 1)
    zy = np.clip((v * (ZRES - 1)).round().astype(int), 0, ZRES - 1)
    visible = (pos @ to_cam) >= z[zy, zx] - 0.012 * size
    facing = np.abs((nrm * to_cam).sum(2))            # winding is unreliable; the z-buffer handles occlusion
    w = facing ** 2 * visible * valid * np.clip((sample[..., 3] - 0.5) * 2, 0, 1)
    weight_sum += w; colour_sum += w[..., None] * sample[..., :3]

fallback = np.asarray(Image.open(os.path.join(TEX, f'satchel_t{N}_basecolor_meshy.png')).convert('RGB'),
                      np.float64)[::-1] / 255                 # Blender pixel rows run bottom-up
projected = colour_sum / np.maximum(weight_sum, 1e-6)[..., None]
blend = np.clip(weight_sum / 0.04, 0, 1)[..., None]
out = projected * blend + fallback * (1 - blend)
Image.fromarray((np.clip(out[::-1], 0, 1) * 255 + 0.5).astype(np.uint8)).save(
    os.path.join(TEX, f'satchel_t{N}_projected.png'))
Image.fromarray((np.clip(blend[::-1, :, 0], 0, 1) * 255).astype(np.uint8)).save(os.path.join(WORK, f't{N}_projection_weight.png'))
report['covered_fraction'] = round(float((weight_sum[valid] > 0.04).mean()), 3)
json.dump(report, open(os.path.join(WORK, f't{N}_projection.json'), 'w'), indent=1)
print('PROJECT done', report)
