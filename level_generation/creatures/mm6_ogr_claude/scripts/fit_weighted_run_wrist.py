"""Fit constant weapon-arm clearance offsets on the review copy; preserve the source choreography."""
from pathlib import Path
import bpy, json, math, ast
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];out=p/'review/motion_options'
bpy.ops.wm.open_mainfile(filepath=str(out/'ogre_motion_options.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Ogre'];sc=bpy.context.scene;me=body.data
names={g.index:g.name for g in body.vertex_groups}
dom=[names[max(v.groups,key=lambda e:e.weight).group] if v.groups else '' for v in me.vertices]
sword=[v.index for v in me.vertices if dom[v.index]=='Sword']
exclude=lambda i: dom[i]=='Sword' or dom[i].startswith(('B_R_Hand','B_R_Finger'))
polys=[tuple(f.vertices) for f in me.polygons if not any(exclude(i) for i in f.vertices)]
fwd=rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))

def apply(pose, arm, wrist):
    for n,(q,l) in pose.items():
        pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=(1,1,1)
    bpy.context.view_layer.update()
    axis=(rig.pose.bones['B_Spine2'].matrix.to_3x3()@fwd).normalized()
    for n,axis,angle in [('B_R_UpperArm',axis,-arm),('B_R_Hand',axis,wrist)]:
        pb=rig.pose.bones[n];h=pb.head.copy()
        pb.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(angle),4,axis)@Matrix.Translation(-h)@pb.matrix
        pb.scale=(1,1,1)
        bpy.context.view_layer.update()

def depth():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,polys);worst=0
    for i in sword[::2]:
        loc,n,fi,d=tree.find_nearest(co[i],.15)
        if loc is not None and d>worst and d>1e-6 and (co[i]-loc).dot(n)<-.707*d:worst=d
    return worst

report={}
for name in ['Running_Weighted']:
    act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
    poses=[]
    for f in range(int(act.frame_range[1])+1):
        sc.frame_set(f);poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action=None
    # Find the smallest constant proportion correction before baking; dense post-export checks follow.
    candidates=sorted([(arm,wrist) for arm in [0] for wrist in [0,10,20,30,-10,-20,-30]],key=lambda v:v[0]**2+v[1]**2)
    best=None
    for arm,wrist in candidates:
        worst=0
        for pose in poses[::3]:
            apply(pose,arm,wrist);worst=max(worst,depth())
            if worst>.002:break
        print('CLEARANCE_PROBE',name,arm,wrist,round(worst,4),flush=True)
        if worst<.002:
            worst=0
            for pose in poses:
                apply(pose,arm,wrist);worst=max(worst,depth())
                if worst>.002:break
            if worst<.002:best=(arm,wrist,worst);break
    if best is None:raise RuntimeError('No fitting offset cleared '+name)
    rows=[]
    for pose in poses:
        apply(pose,*best[:2]);rows.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_R_UpperArm','B_R_Hand']})
    rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
    for f,row in enumerate(rows):
        for n,q in row.items():
            pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
    report[name]={'upper_arm_abduction_degrees':best[0],'wrist_outward_tilt_about_chest_forward_degrees':best[1],'sampled_sword_depth_m':best[2]}
    print('CLEARANCE_FIT',name,report[name],flush=True)

# Reuse the established twist bake on the fitted channels without editing the skin weights.
tree=ast.parse((p/'scripts/twist_bones.py').read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['twist_about','bake_twist']]
exec(compile(ast.Module(body=functions,type_ignores=[]),'twist_bones.py','exec'),globals());FA=UA=.5
for name in report:bake_twist(bpy.data.actions[name])
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];sc.frame_set(0)
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'ogre_motion_options.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'ogre_motion_options.glb'),use_selection=True,export_format='GLB',
 export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
 export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,
 export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(out/'checks/clearance_fit_weighted_wrist.json').write_text(json.dumps(report,indent=2)+'\n')

import runpy
runpy.run_path(str(p/'scripts/finish_motion_preview.py'),run_name='__main__')
