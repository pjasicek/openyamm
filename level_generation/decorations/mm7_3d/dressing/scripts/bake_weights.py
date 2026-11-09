"""Stain weight maps for bones_textures.py: where the sprites gather their dirt. For the MM6 bones batch's Meshy
skull and skeleton (read only), per vertex
- cavity = 1 - occlusion (rays over the normal hemisphere against the mesh itself: sockets, sutures, gaps between
  ribs and teeth), stretched to 0..1;
- crown = the height on the skull asset (0 below 45 % of its height, 1 at the top; the skeleton has none);
rasterised into the texture space as work/weight_<source>.npy (SIZE x SIZE x [cavity, crown], row 0 = v 1), with the
islands dilated into their margins. Usage: blender --background --python bake_weights.py -- [skull] [skeleton]"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl = dlib.pl
SIZE = 1024
SOURCES = {'skull': ('skull_tex.blend', 'skull'), 'skeleton': ('skeleton_tex.blend', 'skeleton')}


def rasterise(obj, values):
    """values: (vertex count, channels) -> (SIZE, SIZE, channels) image in uv space (row 0 = v 1), and coverage."""
    me = obj.data
    uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2)
    out = np.zeros((SIZE, SIZE, values.shape[1]), np.float32)
    hit = np.zeros((SIZE, SIZE), bool)
    for poly in me.polygons:
        loops = list(poly.loop_indices)
        for k in range(1, len(loops) - 1):
            tri = [loops[0], loops[k], loops[k + 1]]
            p = uv[tri] * SIZE
            vals = values[[me.loops[i].vertex_index for i in tri]]
            x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
            x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, SIZE - 1), min(y1, SIZE - 1)
            if x1 < x0 or y1 < y0:
                continue
            ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            px, py = xs + 0.5, ys + 0.5
            (ax, ay), (bx, by), (cx, cy) = p
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-9:
                continue
            l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
            l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
            l3 = 1 - l1 - l2
            inside = (l1 >= -0.01) & (l2 >= -0.01) & (l3 >= -0.01)
            if not inside.any():
                continue
            v = l1[..., None] * vals[0] + l2[..., None] * vals[1] + l3[..., None] * vals[2]
            rows = SIZE - 1 - ys[inside]
            out[rows, xs[inside]] = v[inside]
            hit[rows, xs[inside]] = True
    # dilate into the margins (8 passes)
    for _ in range(8):
        grown = hit.copy(); acc = np.zeros_like(out); cnt = np.zeros((SIZE, SIZE), np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(hit, dy, 0), dx, 1)
            acc += np.roll(np.roll(out, dy, 0), dx, 1) * sh[..., None]; cnt += sh
        fill = ~hit & (cnt > 0)
        out[fill] = acc[fill] / cnt[fill, None]
        grown |= fill; hit = grown
    return out


def main():
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(SOURCES)
    for name in names:
        blend, obj_name = SOURCES[name]
        pl.reset()
        with bpy.data.libraries.load(os.path.join(dlib.MM6_BONES, 'work', blend)) as (src, dst):
            dst.objects = [obj_name]
        obj = dst.objects[0]
        bpy.context.scene.collection.objects.link(obj)
        co = np.array([v.co[:] for v in obj.data.vertices])
        size = (co.max(0) - co.min(0)).max()
        pl.vertex_occlusion(obj, rays=48, distance=size * (0.12 if name == 'skull' else 0.04), strength=1.0,
                            floor=False)
        occ = np.empty(len(obj.data.vertices) * 4, np.float32)
        obj.data.color_attributes['Color'].data.foreach_get('color', occ)
        cavity = 1 - occ.reshape(-1, 4)[:, 0]
        cavity = np.clip((cavity - np.percentile(cavity, 20)) / max(np.percentile(cavity, 97) -
                                                                     np.percentile(cavity, 20), 1e-3), 0, 1)
        z = (co[:, 2] - co[:, 2].min()) / max(np.ptp(co[:, 2]), 1e-6)
        crown = np.clip((z - 0.45) / 0.55, 0, 1) if name == 'skull' else np.zeros_like(z)
        img = rasterise(obj, np.stack([cavity, crown], 1))
        path = os.path.join(dlib.WORK, f'weight_{name}.npy')
        np.save(path, np.clip(img, 0, 1).astype(np.float16))
        print('WEIGHT', name, path, 'cavity mean', round(float(cavity.mean()), 3))


main()
