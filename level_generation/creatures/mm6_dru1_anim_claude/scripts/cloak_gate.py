"""Cloak gates for the druidess (merged and adapted from mm6_thf_claude cloak_poke.py / cloak_stretch.py).
Per clip:
- POKE: leg/boot vertices (pieces 2, 6, 7) behind the pelvis, above the hem and inside the cloak's height range, whose
  ray toward the back (the pelvis heading) meets no cloak face, counted per frame; 'through' = a ray straight down from
  the vertex still meets cloak (it pokes through the cloth, not out from under the hem). Upright clips only.
- TEAR: cloak edges stretched > 2x, by their opening in cm (a ratio is meaningless on short hem edges); the worst
  edge per clip with its frame and dominant bones.
Args: -- <blend> clip [clip ...]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
cfaces = [tuple(p.vertices) for p in me.polygons if all(pv[v] == 100 for v in p.vertices)]
lverts = np.where(np.isin(pv, (2, 6, 7)))[0]
cv = set(np.where(pv == 100)[0].tolist())
E = np.array([tuple(e.vertices) for e in me.edges if e.vertices[0] in cv and e.vertices[1] in cv])
R = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); rl = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1)
G = {g.index: g.name for g in body.vertex_groups}
PEL_FWD = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
for clip in a[1:]:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    tot = high = 0; worst = (0.0, 0, 0, 0, 0.0); upright = clip != 'Death'
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        dl = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1); k = dl / np.maximum(rl, 1e-6)
        gain = np.where(k > 2, dl - rl, 0); i = int(np.argmax(gain))
        if gain[i] * 100 > worst[0]:
            worst = (float(gain[i]) * 100, f, int(E[i, 0]), int(E[i, 1]), float(k[i]))
        if not upright:
            continue
        tree = BVHTree.FromPolygons([Vector(p) for p in P], cfaces)
        pm = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
        back = -(pm.to_3x3() @ PEL_FWD); back.z = 0; back.normalize()
        hem = P[list(cv)][:, 2].min()
        ph = np.array(pm.translation)
        for i_ in lverts:
            p = Vector(P[i_])
            if (P[i_] - ph) @ np.array(back) < 0.02 or p.z < hem + 0.03 or p.z > 0.9:
                continue
            if tree.ray_cast(p + back * 1e-4, back, 1.0)[0] is None:
                tot += 1
                if tree.ray_cast(p, Vector((0, 0, -1)), 1.0)[0] is not None:
                    high += 1
    s, f, v0, v1, kk = worst
    w = lambda v: sorted(((round(g.weight, 2), G[g.group]) for g in me.vertices[v].groups), reverse=True)[:2]
    print(f'CLOAKGATE {clip}: poke (vertex-frames) {tot}, through the cloth {high} | worst tear {s:.1f} cm (x{kk:.1f}) '
          f'frame {f} {w(v0)} | {w(v1)}')
