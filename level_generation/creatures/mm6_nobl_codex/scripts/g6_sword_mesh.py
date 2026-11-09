"""G6 for the real (curved) scimitar: the straight stand-in blade of g6_contacts.py misses the scimitar's curve (up to
23 cm off the grip axis). Plays the EXPORTED GLB at 1/48 s; per frame the posed Sword-weighted vertices are tested
against the posed body (all other vertices): inside = behind the closest body face within a 45 deg cone of its normal
(the g6_contacts.py rule). Reports per clip the deepest blade vertex (cm), the frame and the body region (dominant bone).
Args: -- <glb>"""
import bpy, sys, math
import numpy as np
from volume_contact import inside
from mathutils.bvhtree import BVHTree
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
me = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent is arm and 'LOD' not in o.name and 'Shadow' not in o.name)
g = me.vertex_groups['Sword'].index
names = {vg.index: vg.name for vg in me.vertex_groups}
sw = np.array([any(e.group == g and e.weight > 0.5 for e in v.groups) for v in me.data.vertices])
dom = [names[max(v.groups, key=lambda e: e.weight).group] if v.groups else '' for v in me.data.vertices]
# body = everything but the sword and the gripping hand (the handle sits inside the fist by design)
grip = np.array([d_.startswith('B_R_Hand') or d_.startswith('B_R_Finger') for d_ in dom])
body_polys = [p for p in me.data.polygons if not sw[p.vertices[0]] and not grip[p.vertices[0]]]
restM=arm.matrix_world@arm.data.bones['Sword'].matrix_local
local=[restM.inverted()@(me.matrix_world@v.co) for v in me.data.vertices]
blade=sw & np.array([v.y>.061 for v in local])
assert blade.sum()>10
sc = bpy.context.scene
import os
ONLY = set(os.environ['CLIPS'].split(',')) if os.environ.get('CLIPS') else None
for act in [a for a in bpy.data.actions if ONLY is None or a.name in ONLY]:
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; t = f0; worst = (0.0, None, '')
    while t <= f1 + 1e-6:
        sc.frame_set(int(t), subframe=t - int(t))
        ev = me.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.array([tuple(me.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        tree = BVHTree.FromPolygons([tuple(c) for c in co], [tuple(p.vertices) for p in body_polys])
        for i in np.where(blade)[0]:
            loc, nrm, fi, d = tree.find_nearest(Vector(co[i]), 0.2)
            if loc is None:
                continue
            v = Vector(co[i]) - loc
            if v.dot(nrm) < 0 and v.length > 1e-6 and (-v).normalized().angle(nrm) < math.radians(45) and d > worst[0] and inside(tree,co[i]):
                worst = (d, round(t, 1), dom[body_polys[fi].vertices[0]])
        t += sc.render.fps / 48
    assert worst[0]<1e-5,(act.name,worst)
    print(f'G6SWORD {act.name:9s} deepest blade vertex inside the body: {worst[0] * 100:.4f} cm at frame {worst[1]} ({worst[2]})')
