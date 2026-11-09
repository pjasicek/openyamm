"""Skin through the skirts, on a GLB (copy of ../mm7_m190_claude/scripts/skirt_poke.py for the runtime file, which has no
'piece'/'garment' attributes): every vertex of the mesh node takes the shell and garment of the nearest source vertex at
rest (work/source_pieces.npz). At rest: the skin vertices (garment 0) behind the closest face of each listed skirt shell
(within 6 cm). Per clip and frame: the deepest of them in FRONT of the closest skirt face (poking out).
Usage: blender -b -P skirt_poke_glb.py -- <glb> <pieces a,b> <clip> [...]   (mesh node REA_NODE, default Dwarf)"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.abspath(a[0]))
PIECES = [int(x) for x in a[1].split(',')]; acts = a[2:]
body = bpy.data.objects[os.environ.get('REA_NODE', 'Dwarf')]; me = body.data
rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE')


def mesh_co():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def side(bvh, P, sign):
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
s = np.load(os.path.join(HERE, 'work', 'source_pieces.npz'))
kd = KDTree(len(s['co']))
for i, c in enumerate(s['co']):
    kd.insert(c, i)
kd.balance(); q = [kd.find(c) for c in rest]
idx = np.array([x[1] for x in q]); dist = np.array([x[2] for x in q]); pv, gv = s['piece'][idx], s['garment'][idx]
print(f'SKIRTPOKE {os.path.basename(a[0])}: {len(rest)} vertices, label distance max {dist.max() * 1000:.2f} mm')
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
