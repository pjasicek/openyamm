"""G1 crossbow source review at its original 30 fps, with a hand-attached prop."""
import bpy, sys, json, math, os
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).parent))
import common
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(Path('anim_library/humanoid_set/2Hand Crossbow.glb').resolve()))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
arm.rotation_mode='XYZ'
arm.rotation_euler=(0,0,math.pi)
acts={a.name.split('@')[-1].split('|')[-1]:a for a in bpy.data.actions}
for o in bpy.data.objects:
    if o.type=='MESH' and o.parent is not arm:
        o.hide_render=True
def set_pose(name,frame):
    a=acts[name]
    arm.animation_data.action=a
    if a.slots: arm.animation_data.action_slot=a.slots[0]
    scene.frame_set(int(frame),subframe=frame-int(frame))
    bpy.context.view_layer.update()
def centre(side):
    # Curl-centre estimate in the aim pose, never the importer's long bone tails.
    centres=[]
    for i in range(1,5):
        pts=np.array([arm.matrix_world @ arm.pose.bones[f'B_{side}_Finger{i}{suffix}'].head for suffix in ('','1','2')])
        c=pts.mean(0); basis=np.linalg.svd(pts-c)[2][:2]
        xy=(pts-c)@basis.T
        sol=np.linalg.lstsq(np.column_stack((2*xy,np.ones(3))),np.sum(xy*xy,axis=1),rcond=None)[0]
        centres.append(c+sol[:2]@basis)
    return Vector(np.mean(centres,axis=0))
set_pose('2HandCrossbowAiming',acts['2HandCrossbowAiming'].frame_range[1])
grip=centre('R'); support=centre('L')
forward=(support-grip).normalized()
up=Vector((0,0,1)); right=forward.cross(up).normalized();up=right.cross(forward).normalized()
assert forward.y < -0.25, list(forward)
basis=Matrix((right,forward,up)).transposed().to_4x4()
basis.translation=grip
bind=(arm.matrix_world@arm.pose.bones['B_R_Hand'].matrix).inverted()@basis
wood=bpy.data.materials.new('stock');wood.diffuse_color=(0.44,0.20,0.05,1)
bow=bpy.data.materials.new('brass');bow.diffuse_color=(0.72,0.52,0.13,1)
string=bpy.data.materials.new('string');string.diffuse_color=(0.06,0.06,0.06,1)
parts=[]
def rod(a,b,r,material):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=(b-a).length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    o.data.materials.append(material)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    parts.append(o)
rod((0,-.18,.05),(0,.72,.05),.045,wood)
rod((0,0,-.12),(0,0,.06),.035,wood)
rod((-.36,.60,.05),(-.16,.72,.05),.025,bow)
rod((-.16,.72,.05),(.16,.72,.05),.025,bow)
rod((.16,.72,.05),(.36,.60,.05),.025,bow)
rod((-.36,.60,.05),(0,.34,.05),.005,string)
rod((0,.34,.05),(.36,.60,.05),.005,string)
rod((0,.25,.105),(0,.82,.105),.007,string)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.join()
prop=bpy.context.object;prop.name='SourceCrossbowStandin'
common.workbench_clay(scene)
scene.display.shading.color_type='MATERIAL'
out=P/'review/source_selected';out.mkdir(parents=True,exist_ok=True)
clips=['2HandCrossbowAttack2','2HandCrossbowWalk','2HandCrossbowGetHitF1','2HandCrossbowDeath1']
report={'fps':30,'source':'anim_library/humanoid_set/2Hand Crossbow.glb','grip_world':list(grip),'support_world':list(support),'forward':list(forward),'prop_hand_matrix':[list(r) for r in bind],'clips':[]}
rows=[]
for clip in clips:
    a=acts[clip]; f0,f1=a.frame_range
    n=9 if clip=='2HandCrossbowAimingFire' else 5
    info={'name':clip,'range':[f0,f1],'seconds':(f1-f0)/30,'samples':[]}
    for view in ('three_quarter',):
        row=[]
        for i in range(n):
            f=f0+(f1-f0)*i/(n-1)
            set_pose(clip,f)
            prop.matrix_world=arm.matrix_world@arm.pose.bones['B_R_Hand'].matrix@bind
            path=common.render_views(str(out/f'{clip}_{i}'),1.2,3.0,views=(view,),resolution=(240,320))[0]
            row.append([path,f'{clip} f{f:.1f} {view}'])
            if view=='front':info['samples'].append({'frame':f,'right_hand':list(arm.matrix_world@arm.pose.bones['B_R_Hand'].head),'left_hand':list(arm.matrix_world@arm.pose.bones['B_L_Hand'].head)})
        rows.append(row)
    report['clips'].append(info)
(out/'frames.json').write_text(json.dumps(rows,indent=2))
(P/'work/source_selected_review.json').write_text(json.dumps(report,indent=2))
print('G1 SOURCE PREVIEW COMPLETE',flush=True)

