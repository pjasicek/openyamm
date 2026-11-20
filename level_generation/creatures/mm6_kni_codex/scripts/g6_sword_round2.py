"""G6 for the real (curved) scimitar: the straight stand-in blade of g6_contacts.py misses the scimitar's curve (up to
23 cm off the grip axis). Plays the EXPORTED GLB at 1/48 s; per frame the posed Sword-weighted vertices are tested
against the posed body (all other vertices): inside = behind the closest body face within a 45 deg cone of its normal
(the g6_contacts.py rule). Reports per clip the deepest blade vertex (cm), the frame and the body region (dominant bone).
Args: -- <glb>"""
import bpy, sys, math, json
from pathlib import Path
REPORT={}
HAND={}
BLADE={}
import numpy as np
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
hand_polys=[p for p in me.data.polygons if not sw[p.vertices[0]] and grip[p.vertices[0]]]
W=json.loads((Path(__file__).resolve().parents[1]/'work/weapon_fit.json').read_text());c=np.array(W['centre_rest']);ax=np.array(W['axis_rest']);edge=np.array(W['cut_direction_rest']);flat=np.cross(ax,edge)
canonical={i:(np.array(me.data.vertices[i].co)-c)@np.column_stack([ax,edge,flat]) for i in np.where(sw)[0]}
non_grip=[i for i in np.where(sw)[0] if not -.196 < canonical[i][0] < .108]
sc = bpy.context.scene
import os
ONLY = set(os.environ['CLIPS'].split(',')) if os.environ.get('CLIPS') else None
for act in [a for a in bpy.data.actions if ONLY is None or a.name in ONLY]:
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; t = f0; worst = (0.0, None, ''); hand_worst=(0.0,None);worst_vertex=None;blade_worst=0.0
    while t <= f1 + 1e-6:
        sc.frame_set(int(t), subframe=t - int(t))
        ev = me.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.array([tuple(me.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        tree = BVHTree.FromPolygons([tuple(c) for c in co], [tuple(p.vertices) for p in body_polys])
        for i in np.where(sw)[0]:
            loc, nrm, fi, d = tree.find_nearest(Vector(co[i]), 0.2)
            if loc is None:
                continue
            v = Vector(co[i]) - loc
            if v.dot(nrm) < -0.7*d and (d > worst[0] or (canonical[i][0]>.135 and d>blade_worst)):
                # Confirm inside: nearest normals beside disconnected/open armour may point behind a distant face.
                directions=[Vector(q).normalized() for q in [(1,.13,.27),(-1,.31,.17),(.19,1,.41),(.23,-1,.37),(.31,.21,1),(.11,.27,-1),(1,1,1)]]
                exits=0
                for ray in directions:
                    hit,normal,_,_=tree.ray_cast(Vector(co[i])+ray*1e-6,ray,10)
                    exits+=hit is not None and normal.dot(ray)>0
                if exits<5:continue
                if d>worst[0]:
                    worst = (d, round(t, 1), dom[body_polys[fi].vertices[0]]);worst_vertex=canonical[i].tolist()
                if canonical[i][0]>.135:blade_worst=max(blade_worst,d)
        hand_tree=BVHTree.FromPolygons([tuple(c)for c in co],[tuple(p.vertices)for p in hand_polys])
        for i in non_grip:
            loc,nrm,fi,d=hand_tree.find_nearest(Vector(co[i]),.05)
            if loc is None or d<=hand_worst[0] or (Vector(co[i])-loc).dot(nrm)>=-.7*d:continue
            exits=0
            for q in [(1,.13,.27),(-1,.31,.17),(.19,1,.41),(.23,-1,.37),(.31,.21,1),(.11,.27,-1),(1,1,1)]:
                ray=Vector(q).normalized();hit,normal,_,_=hand_tree.ray_cast(Vector(co[i])+ray*1e-6,ray,10);exits+=hit is not None and normal.dot(ray)>0
            if exits>=5:hand_worst=(d,round(t,2))
        t += sc.render.fps / 48
    print(f'G6SWORD {act.name:9s} deepest sword vertex inside the body: {worst[0] * 100:.1f} cm at frame {worst[1]} ({worst[2]})')

    REPORT[act.name]={'depth_m':worst[0],'frame':worst[1],'region':worst[2],'weapon_axis_edge_flat':worst_vertex}
    print('CONTACT VERTEX',act.name,worst_vertex)
    BLADE[act.name]={'depth_m':blade_worst}
    HAND[act.name]={'depth_m':hand_worst[0],'frame':hand_worst[1]};print('HAND-FURNITURE',act.name,hand_worst)
P=Path(__file__).resolve().parents[1]
(P/'review/round2/g6_sword.json').write_text(json.dumps(REPORT,indent=2));(P/'review/round2/g6_hand_furniture.json').write_text(json.dumps(HAND,indent=2))
(P/'review/round2/g6_blade_only.json').write_text(json.dumps(BLADE,indent=2))
assert max(v['depth_m']for v in BLADE.values())==0,BLADE
assert max(v['depth_m']for v in REPORT.values())<.002,REPORT
assert max(v['depth_m']for v in HAND.values())<.002,HAND
