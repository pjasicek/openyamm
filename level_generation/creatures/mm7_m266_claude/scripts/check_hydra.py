"""Gates on every clip (after mm6_hyd_claude/scripts/check_heads.py): per frame, triangles of each head (face part k)
overlapping triangles outside head k and neck k (other heads, other necks; the body counts only away from the neck
bases), from BVH trees of the posed mesh; plus the lowest vertex and the lowest body (non-leg) vertex. Prints per clip
the worst frame. Args: -- <blend> [step]"""
import bpy, os, sys
import numpy as np
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); STEP = int(a[1]) if len(a) > 1 else 1
ob = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = ob.data
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
own = np.zeros(len(me.vertices), int); me.attributes['chain_owner'].data.foreach_get('value', own)
polys = [list(p.vertices) for p in me.polygons]
_gn = {g.index: g.name for g in ob.vertex_groups}
DOM = [_gn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in me.vertices]
face_own = np.array([np.bincount(own[p], minlength=6).argmax() for p in polys])
heads = {k: [i for i in range(len(polys)) if part[i] == k] for k in range(1, 6)}
zrest = np.array([me.vertices[p[0]].co.z for p in polys])
others = {k: [i for i in range(len(polys)) if part[i] != k and face_own[i] != k and
              (part[i] > 0 or (face_own[i] > 0 and zrest[i] > 1.05))] for k in range(1, 6)}   # necks above their touching bases
rig.animation_data_create()
for act in bpy.data.actions:
    if act.name.startswith('Stress'):
        continue
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = (0, f0, None); low = 9.0; low_at = None
    for f in range(f0, f1 + 1, STEP):
        bpy.context.scene.frame_set(f)
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        co = [tuple(v.co) for v in ev.data.vertices]
        zz = np.array([c[2] for c in co]); i = int(zz.argmin())
        if zz[i] < low:
            low = float(zz[i]); low_at = (f, DOM[i])
        for k in range(1, 6):
            A = BVHTree.FromPolygons(co, [polys[i] for i in heads[k]])
            B = BVHTree.FromPolygons(co, [polys[i] for i in others[k]])
            hits = A.overlap(B)
            if len(hits) > worst[0]:
                touch = sorted({('H%d' % part[others[k][j]]) if part[others[k][j]] else ('N%d' % face_own[others[k][j]])
                                for _, j in hits})
                worst = (len(hits), f, (k, touch))
    print(f'GATE {act.name}: head overlaps worst {worst[0]} at frame {worst[1]} {worst[2]}; lowest vertex {low * 100:.1f} cm {low_at}',
          flush=True)
