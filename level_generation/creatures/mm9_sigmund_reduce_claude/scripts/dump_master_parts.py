"""Per-face labels of Sigmund's last master before export (../mm9_sigmund_claude/work/linings_v1.blend, opened read-only, never
saved) and of its pre-lining state (geo_v3.blend): face attributes head, hand, lined; `added` = the face is not in geo_v3 (a lining,
rim strip or hair twin face of linings_sig.sh); world-space rest centroid (Blender frame, z up) -> work/final_parts.npz"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, '..', 'mm9_sigmund_claude', 'work')


def load(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(W, name))
    body = bpy.data.objects['Body']; rig = body.parent; me = body.data
    if rig and rig.animation_data: rig.animation_data.action = None
    if rig:
        for b in rig.pose.bones: b.matrix_basis.identity()
    bpy.context.view_layer.update()
    M = np.array(body.matrix_world)
    co = np.array([v.co[:] for v in me.vertices]); co = co @ M[:3, :3].T + M[:3, 3]
    fv = [p.vertices[:] for p in me.polygons]
    cen = np.array([co[list(f)].mean(0) for f in fv])
    at = {}
    for k in ('head', 'hand', 'lined'):
        x = np.zeros(len(me.polygons), np.int32)
        if k in me.attributes: me.attributes[k].data.foreach_get('value', x)
        at[k] = x
    return co, cen, at, np.array([len(f) for f in fv])


co0, cen0, _, nv0 = load('geo_v3.blend')
co, cen, at, nv = load('linings_v1.blend')
assert (nv == 3).all()
key = lambda c: [tuple(x) for x in np.round(c, 5)]
k0 = set(key(cen0)); added = np.array([k not in k0 for k in key(cen)])
d = np.zeros(len(cen))
print('geo_v3 faces', len(cen0), 'linings_v1', len(cen), 'added', int(added.sum()), 'matched max', d[~added].max())
np.savez(os.path.join(HERE, 'work', 'final_parts.npz'), cen=cen, co=co, added=added, **at)
for k in ('head', 'hand', 'lined'):
    print(k, {int(a): int((at[k] == a).sum()) for a in np.unique(at[k])}, 'added', int((added & (at[k] == 1)).sum()))
