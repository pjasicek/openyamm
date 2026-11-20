"""Skin through a skirt (user review 2026-10-20: in the walk the Dwarf's thighs poked through the mail skirt at the hip).
At rest: the skin vertices (garment label 0) that lie inside the listed skirt pieces (behind the closest skirt face,
within 6 cm). Per action and frame: the deepest of them that is in FRONT of the closest skirt face (the G6 cone test
inverted), i.e. poking out. Prints per action and piece the worst depth (cm), its frame and the frames above 0.5 cm.
Args: -- <blend> <pieces a,b> <action> [...]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
PIECES = [int(x) for x in a[1].split(',')]; acts = a[2:]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)


def mesh_co():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def side(bvh, P, sign):
    """Per point: distance if it lies on the `sign` side of the closest face (cone test), else 0."""
    out = np.zeros(len(P))
    for k, p in enumerate(P):
        h = bvh.find_nearest(Vector(p), 0.06)
        if h[0] is None:
            continue
        d = Vector(p) - h[0]; L = d.length
        if L > 1e-6 and sign * d.dot(h[1]) > 0.7 * L:
            out[k] = L
    return out


rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
rest = mesh_co()
skin = np.where(gv == 0)[0]
TR = {p: [tuple(f.vertices) for f in me.polygons if all(pv[i] == p for i in f.vertices)] for p in PIECES}
UNDER = {}
for p in PIECES:
    bvh = BVHTree.FromPolygons([Vector(c) for c in rest], TR[p])
    UNDER[p] = skin[side(bvh, rest[skin], -1) > 0]
    print(f'SKIRTPOKE piece {p}: {len(TR[p])} faces, {len(UNDER[p])} skin vertices under it at rest')
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    res = {p: [] for p in PIECES}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); co = mesh_co()
        for p in PIECES:
            bvh = BVHTree.FromPolygons([Vector(c) for c in co], TR[p])
            d = side(bvh, co[UNDER[p]], +1)
            res[p].append(d.max() if len(d) else 0.0)
    for p in PIECES:
        r = np.array(res[p]); fr = np.arange(f0, f1 + 1)
        print(f'SKIRTPOKE {an} piece {p}: worst {r.max() * 100:.1f} cm at frame {int(fr[np.argmax(r)])}; '
              f'> 0.5 cm: {[int(x) for x in fr[r > 0.005]][:24]}')
