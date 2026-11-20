"""Collision gate for the hydra clips: every frame of every clip, the triangles of each head (part k, skull and stub)
overlapping any triangle outside head k and neck k (other heads, other necks, the body), from BVH trees of the posed
mesh. Prints per clip the worst frame. Run on work/anim_v1.blend:
  blender --background work/anim_v1.blend --python scripts/check_heads.py"""
import bpy, json, os
import numpy as np
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
obj = bpy.data.objects['Hydra']; rig = bpy.data.objects['Hydra_Rig']; me = obj.data
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
chains = json.load(open(os.path.join(HERE, 'work', 'rig.json')))['chains']
bone_chain = {nm: ci for ci, c in enumerate(chains) for nm in c['names']}
gname = {g.index: g.name for g in obj.vertex_groups}
owner = np.array([bone_chain[gname[max(v.groups, key=lambda x: x.weight).group]] for v in me.vertices])
face_chain = np.array([np.bincount(owner[list(p.vertices)], minlength=6).argmax() for p in me.polygons])
polys = [list(p.vertices) for p in me.polygons]
report = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    worst = (0, f0, None)
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        co = [tuple(v.co) for v in ev.data.vertices]
        for k in range(1, 6):
            mine = [i for i in range(len(polys)) if part[i] == k]
            rest = [i for i in range(len(polys)) if part[i] != k and face_chain[i] != k]
            a = BVHTree.FromPolygons(co, [polys[i] for i in mine]); b = BVHTree.FromPolygons(co, [polys[i] for i in rest])
            hits = a.overlap(b)
            if len(hits) > worst[0]:
                others = sorted({int(face_chain[rest[j]]) if part[rest[j]] == 0 else 10 + int(part[rest[j]]) for _, j in hits})
                worst = (len(hits), f, (k, others))
    report[act.name] = worst
    print(f'HEADS {act.name}: worst {worst[0]} overlapping triangle pairs at frame {worst[1]} (head, touching: '
          f'chains 0-5 / heads 11-15) {worst[2]}', flush=True)
