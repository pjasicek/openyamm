"""Local repairs of the packed texture-pass layout, so the 19-minute xatlas pack is kept (uv_atlas_v3.py -> this script
-> the upload). Runs once, before the upload goes to Meshy; a later run would invalidate the paint.

1. Throat cap (mouth_bag = 2): head_fix.py mapped it planar, which left near-degenerate triangles (7 of zero area), and
   xatlas threw one sliver across the atlas. The cap is a flat near-black patch deep in the throat, so its UVs need no
   fidelity: the ring is laid on a circle (a convex polygon, so its triangulation cannot overlap or collapse) in the
   widest free spot of the atlas.
2. Remaining overlaps inside a chart (a boundary corner poking into a neighbouring triangle): the corner closest to a
   fix moves by the smallest step, searched on a texel grid, that clears every overlap and keeps its triangles' winding.

Args: <uv_v3_packed blend> <out blend> <upload glb> <in bag npz> <out bag npz> <report json>
"""
import bpy, sys, os, json
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, BAG_IN, BAG_OUT, REPORT = argv
S = 2048
CAP_RADIUS = 26.0                # texels
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = mesh.data
bag = np.array([d.value for d in me.attributes['mouth_bag'].data])
tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
flat = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
UV = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64) * S       # texels, v up
n = len(tri)


def signed(p):
    return ((p[..., 1, 0] - p[..., 0, 0]) * (p[..., 2, 1] - p[..., 0, 1])
            - (p[..., 2, 0] - p[..., 0, 0]) * (p[..., 1, 1] - p[..., 0, 1])) / 2


def texels(p):
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-6:
        return np.zeros(0, int), np.zeros(0, int)
    x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), S - 1)
    y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    iy, ix = np.nonzero((l1 > 1e-3) & (l2 > 1e-3) & (1 - l1 - l2 > 1e-3))
    return iy + y0, ix + x0


# ---------------------------------------------------------------- 1. the cap on a circle in free space
cap = np.nonzero(bag == 2)[0]
occ = np.zeros((S, S), bool)
for t in np.nonzero(bag != 2)[0]:
    iy, ix = texels(UV[t])
    occ[iy, ix] = True
    # thin triangles can miss texel centres: their corners count too
    q = np.clip(UV[t].astype(int), 0, S - 1)
    occ[q[:, 1], q[:, 0]] = True
# widest free square, on a 4-texel grid (Blender's Python has no scipy): dilate the occupied blocks until nothing is left
block = occ.reshape(S // 4, 4, S // 4, 4).any(axis=(1, 3))
block[0] = block[-1] = block[:, 0] = block[:, -1] = True
free = np.zeros(block.shape, np.int32)
grown = block.copy()
while not grown.all():
    free[~grown] += 1
    g = grown.copy()
    g[1:] |= grown[:-1]
    g[:-1] |= grown[1:]
    g[:, 1:] |= grown[:, :-1]
    g[:, :-1] |= grown[:, 1:]
    g[1:, 1:] |= grown[:-1, :-1]
    g[:-1, :-1] |= grown[1:, 1:]
    g[1:, :-1] |= grown[:-1, 1:]
    g[:-1, 1:] |= grown[1:, :-1]
    grown = g
by, bx = np.unravel_index(np.argmax(free), free.shape)
cy, cx = by * 4 + 2, bx * 4 + 2
room = float(free[by, bx] * 4)
radius = min(CAP_RADIUS, room - 4.0)
assert radius >= 8.0, f'no room for the cap: {room}'
verts = sorted({int(v) for t in cap for v in tri[t]})
co = np.array([me.vertices[v].co[:] for v in verts])
centre = co.mean(0)
_, _, axes = np.linalg.svd(co - centre)                 # the ring's own plane
ang = np.arctan2((co - centre) @ axes[1], (co - centre) @ axes[0])
order = np.argsort(ang)
place = {verts[i]: (cx + 0.5 + radius * np.cos(2 * np.pi * k / len(order)),
                    cy + 0.5 + radius * np.sin(2 * np.pi * k / len(order))) for k, i in enumerate(order)}
for t in cap:
    UV[t] = [place[int(v)] for v in tri[t]]
report = {'cap': {'faces': len(cap), 'centre': [int(cx), int(cy)], 'radius': round(float(radius), 1),
                  'free_radius': round(room, 1), 'smallest_area_px': round(float(np.abs(signed(UV[cap])).min()), 3)}}
assert np.abs(signed(UV[cap])).min() > 0.05, 'cap triangles still collapse'


# ---------------------------------------------------------------- 2. overlaps inside charts
def overlaps():
    owner = -np.ones((S, S), np.int32)
    pairs = {}
    for t in range(n):
        iy, ix = texels(UV[t])
        prev = owner[iy, ix]
        for q in np.unique(prev[prev >= 0]):
            pairs[(int(q), t)] = int((prev == q).sum())
        owner[iy, ix] = t
    return pairs


def local_clear(faces, others):
    """No texel of `faces` is shared with any of `others` (or among themselves)."""
    seen = {}
    for t in others:
        iy, ix = texels(UV[t])
        seen.update(((y, x), t) for y, x in zip(iy.tolist(), ix.tolist()))
    for t in faces:
        iy, ix = texels(UV[t])
        for y, x in zip(iy.tolist(), ix.tolist()):
            if (y, x) in seen:
                return False
            seen[(y, x)] = t
    return True


moved = []
pairs = overlaps()
report['overlap_pairs_before'] = {f'{a},{b}': c for (a, b), c in pairs.items()}
for (a, b), _ in sorted(pairs.items(), key=lambda kv: -kv[1]):
    if len(overlaps_now := {k: v for k, v in overlaps().items() if k == (a, b)}) == 0:
        continue
    best = None
    centre_px = UV[[a, b]].reshape(-1, 2).mean(0)
    near = np.nonzero((np.abs(UV.reshape(n, -1, 2).mean(1) - centre_px) < 90).all(1))[0]
    corners = {(int(tri[t][k]), tuple(UV[t][k].round(4))) for t in (a, b) for k in range(3)}
    shared = {c for c in corners if sum(c in {(int(tri[t][k]), tuple(UV[t][k].round(4))) for k in range(3)} for t in (a, b)) == 2}
    for vert, old in sorted(corners - shared):
        users = [(int(t), int(k)) for t in near for k in range(3)
                 if int(tri[t][k]) == vert and np.allclose(UV[t][k], old, atol=1e-3)]
        faces = sorted({t for t, _ in users})
        others = [int(t) for t in near if t not in faces]
        sign = np.sign(signed(UV[faces]))
        keep = {(t, k): UV[t][k].copy() for t, k in users}
        for dist in np.arange(0.5, 12.5, 0.5):
            for ang_ in np.arange(0, 360, 15.0):
                step = dist * np.array([np.cos(np.radians(ang_)), np.sin(np.radians(ang_))])
                for (t, k), p in keep.items():
                    UV[t][k] = p + step
                if (np.sign(signed(UV[faces])) == sign).all() and \
                        (np.abs(signed(UV[faces])) > 0.25).all() and local_clear(faces, others):
                    best = (float(dist), vert, step.copy(), keep, faces) if best is None or dist < best[0] else best
                    break
            for (t, k), p in keep.items():
                UV[t][k] = p
            if best and best[1] == vert:
                break
    assert best, f'no local move clears faces {a}, {b}'
    dist, vert, step, keep, faces = best
    for (t, k), p in keep.items():
        UV[t][k] = p + step
    moved.append({'faces': [a, b], 'vertex': vert, 'moved_texels': dist, 'faces_touched': faces})
report['corners_moved'] = moved
left = overlaps()
report['overlap_pairs_after'] = len(left)
report['overlap_texels_after'] = int(sum(left.values()))
assert not left, left
out = np.zeros_like(flat)
for p in me.polygons:
    out[list(p.loop_indices)] = UV[p.index] / S
me.uv_layers['UVMap'].data.foreach_set('uv', out.ravel())
me.update()
B = dict(np.load(BAG_IN))
B['uv_new'] = (UV[np.nonzero(bag)[0]] / S).astype(B['uv_new'].dtype)
rel = np.array([d.value for d in me.attributes['relocated'].data])
B['rel_uv_new'] = (UV[rel > 0] / S).astype(B['rel_uv_new'].dtype)
np.savez(BAG_OUT, **B)
json.dump(report, open(REPORT, 'w'), indent=1)
print('UV_FIX', json.dumps({k: v for k, v in report.items() if k != 'overlap_pairs_before'}))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = mesh.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UV fixed; upload', UPLOAD, len(mesh.data.polygons))
