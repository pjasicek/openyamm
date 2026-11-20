"""Fit a three-finger archery hook: palm beside the cheek, knuckles vertical, wrist roll shared by the forearm."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_complete.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;act=bpy.data.actions['Attack']
def action(a):
    rig.animation_data.action=a
    if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def worldrot(n,R):
    b=rig.pose.bones[n];m=R.to_4x4();m.translation=b.head;b.matrix=m;bpy.context.view_layer.update()
def turn(n,axis,angle):worldrot(n,Quaternion(axis,angle).to_matrix()@rig.pose.bones[n].matrix.to_3x3())
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
names=[n for n in rig.pose.bones.keys()if n in ['B_R_Forearm','B_R_Hand']or n.startswith('B_R_Finger')]
H0=rig.data.bones['B_R_Hand'].matrix_local
fwd=(sum((rig.data.bones[f'B_R_Finger{i}'].head_local for i in range(1,5)),Vector())/4-H0.translation).normalized()
across=(rig.data.bones['B_R_Finger1'].head_local-rig.data.bones['B_R_Finger4'].head_local).normalized()
across=(across-fwd*fwd.dot(across)).normalized();local=H0.to_3x3().inverted()@Matrix((fwd,across,fwd.cross(across))).transposed()
forward=Vector((0,-1,0));up=Vector((0,0,1));goal=Matrix((forward,up,forward.cross(up))).transposed()@local.transposed()
action(act);scene.frame_set(25);snap={b.name:b.matrix_basis.copy()for b in rig.pose.bones};action(None)
for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
worldrot('B_R_Hand',goal)
for n in names:
    if 'Finger'in n:rig.pose.bones[n].matrix_basis.identity()
bpy.context.view_layer.update()
for i in range(1,5):
    chain=[f'B_R_Finger{i}',f'B_R_Finger{i}1',f'B_R_Finger{i}2']
    tip=Vector(json.loads((P/'work/finger_joints.json').read_text())['R'][str(i)][-1])
    for j,n in enumerate(chain):
        a=rig.pose.bones[n].head
        b=rig.pose.bones[chain[j+1]].head if j<2 else rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@tip
        q=(b-a).rotation_difference(forward);worldrot(n,q.to_matrix()@rig.pose.bones[n].matrix.to_3x3())
    for n,angle in zip(chain,[8,80,22] if i<4 else [75,75,30]):turn(n,up,math.radians(angle))
# The thumb stays relaxed against the side of the index, clear of the arrow nock.
turn('B_R_Finger0',Vector((1,0,0)),math.radians(50))
turn('B_R_Finger0.001',Vector((1,0,0)),math.radians(25))
hook={n:rig.pose.bones[n].rotation_quaternion.copy()for n in names if 'Finger'in n}
raw=[]
for f in range(int(act.frame_range[1])+1):
    action(act);scene.frame_set(f);raw.append({b.name:b.matrix_basis.copy()for b in rig.pose.bones})
result=[];report=[]
for f,p in enumerate(raw):
    action(None)
    for n,m in p.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update();w=smooth((f-17)/4)*(1-smooth((f-28)/7))
    current=rig.pose.bones['B_R_Hand'].matrix.to_3x3();target=current.to_quaternion().slerp(goal.to_quaternion(),w).to_matrix()
    sw,tw=armik.wrist_cost(rig,'R',target)
    axis=(rig.pose.bones['B_R_Hand'].head-rig.pose.bones['B_R_Forearm'].head).normalized()
    turn('B_R_Forearm',axis,math.radians(tw)*.75*w);worldrot('B_R_Hand',target)
    for n,q in hook.items():rig.pose.bones[n].rotation_quaternion=p[n].to_quaternion().slerp(q,w)
    bpy.context.view_layer.update();result.append({n:rig.pose.bones[n].rotation_quaternion.copy()for n in names})
    report.append({'frame':f,'weight':w,'wrist_before':[sw,tw],'wrist_after':armik.wrist_cost(rig,'R',target)})
action(act)
for f,p in enumerate(result):
    for n,q in p.items():b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
scene.frame_set(25);common.workbench_clay(scene);center=rig.pose.bones['B_R_Hand'].head
common.render_views(str(P/'review/draw_hook'),center.z,.35,views=('front','left','right','three_quarter'),resolution=(550,550),target=(center.x,center.y))
(P/'work/draw_hand.json').write_text(json.dumps(report,indent=2))
action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/draw_hook_trial.blend'))
