import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import phase
"""G6 for the real (curved) scimitar: the straight stand-in blade of g6_contacts.py misses the scimitar's curve (up to
23 cm off the grip axis). Plays the EXPORTED GLB at 1/48 s; per frame the posed Staff-weighted vertices are tested
against the posed body (all other vertices): inside = behind the closest body face within a 45 deg cone of its normal
(the g6_contacts.py rule). Reports per clip the deepest blade vertex (cm), the frame and the body region (dominant bone).
Args: -- <glb>"""
import bpy, sys, math, json
from pathlib import Path
REPORT={}
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
me = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent is arm and 'LOD' not in o.name and 'Shadow' not in o.name)
g = me.vertex_groups['Staff'].index
names = {vg.index: vg.name for vg in me.vertex_groups}
sw = np.array([any(e.group == g and e.weight > 0.5 for e in v.groups) for v in me.data.vertices])
dom = [names[max(v.groups, key=lambda e: e.weight).group] if v.groups else '' for v in me.data.vertices]
# body = everything but the staff and the gripping hand (the handle sits inside the fist by design)
grip = np.array([d_.startswith('B_R_Hand') or d_.startswith('B_R_Finger') for d_ in dom])
body_polys = [p for p in me.data.polygons if not sw[p.vertices[0]] and not grip[p.vertices[0]]]
left_grip=np.array([d.startswith(('B_L_Hand','B_L_Finger')) for d in dom])
body_without_left=[p for p in body_polys if not left_grip[p.vertices[0]]]
body_with_hands=[p for p in me.data.polygons if not sw[p.vertices[0]]]
staff_faces=np.array([tuple(p.vertices)for p in me.data.polygons if all(sw[i]for i in p.vertices)],dtype=int)
staff_edges=np.unique(np.sort(np.concatenate([staff_faces[:,[0,1]],staff_faces[:,[1,2]],staff_faces[:,[2,0]]]),axis=1),axis=0)
rest_points=np.array([tuple(v.co)for v in me.data.vertices]);rest_samples=np.concatenate([rest_points[sw],rest_points[staff_faces].mean(1),rest_points[staff_edges].mean(1)])
sc = bpy.context.scene
import os
ONLY = set(os.environ['CLIPS'].split(',')) if os.environ.get('CLIPS') else None
for act in [a for a in bpy.data.actions if ONLY is None or a.name in ONLY]:
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; t = f0; worst = (0.0, None, ''); detail={}
    while t <= f1 + 1e-6:
        sc.frame_set(int(t), subframe=t - int(t))
        ev = me.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.array([tuple(me.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        polys=body_without_left if act.name=='Attack' and phase('Attack',.4)<=t/sc.render.fps<=phase('Attack',1.2) else body_polys
        if act.name=='Dead' or (act.name=='Death' and t/sc.render.fps>phase('Death',.25)):polys=body_with_hands
        tree = BVHTree.FromPolygons([tuple(c) for c in co], [tuple(p.vertices) for p in polys])
        samples=np.concatenate([co[sw],co[staff_faces].mean(1),co[staff_edges].mean(1)])
        for i,point in enumerate(samples):
            loc, nrm, fi, d = tree.find_nearest(Vector(point), 0.2)
            if loc is None:
                continue
            v = Vector(point) - loc
            if v.dot(nrm) < -0.7*d and d > worst[0]:
                # Confirm inside: nearest normals beside disconnected/open armour may point behind a distant face.
                directions=[Vector(q).normalized() for q in [(1,.13,.27),(-1,.31,.17),(.19,1,.41),(.23,-1,.37),(.31,.21,1),(.11,.27,-1),(1,1,1)]]
                exits=0
                for ray in directions:
                    hit,normal,_,_=tree.ray_cast(Vector(point)+ray*1e-6,ray,10)
                    exits+=hit is not None and normal.dot(ray)>0
                if exits<5:continue
                worst = (d, round(t, 1), dom[polys[fi].vertices[0]])
                detail={'staff_surface_sample':int(i),'staff_local':list(arm.data.bones['Staff'].matrix_local.inverted()@Vector(rest_samples[i])),'wrist_distance_m':float((Vector(point)-arm.pose.bones['B_R_Hand'].head).length)}
        t += sc.render.fps / 48
    print(f'G6SWORD {act.name:9s} deepest blade vertex inside the body: {worst[0] * 100:.1f} cm at frame {worst[1]} ({worst[2]})')

    REPORT[act.name]={'depth_m':worst[0],'frame':worst[1],'region':worst[2],**detail}
Path(__file__).resolve().parents[1].joinpath('work/g6_staff_mesh.json').write_text(json.dumps(REPORT,indent=2))
