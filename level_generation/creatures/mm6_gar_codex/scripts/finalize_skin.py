"""Distribute observed arm roll using the shared helper, retaining frozen texture geometry."""
import bpy,runpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
shared=Path('level_generation/creatures/mm6_bar1_claude/scripts/twist_bones.py')
sys.argv=[str(shared),'--',str(P/'work/pilots_reduced.blend'),str(P/'work/pilots_skin.blend')]
runpy.run_path(str(shared),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
# Chest wall vertices below the armpit belong to the torso, with a soft transition into the deltoid.
for v in body.data.vertices:
 if v.co.z<1.05 or v.co.z>1.48:continue
 if sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith('W_'))>.05:continue
 cutoff=.10-.05*np.clip((v.co.z-1.3)/.13,0,1);keep=float(np.clip((abs(v.co.x)-cutoff)/.10,0,1))
 moved=0
 for g in list(v.groups):
    group=body.vertex_groups[g.group]
    if any(t in group.name for t in ['UpperArm','Forearm','Hand','Clavicle']):
        amount=g.weight*(1-keep);moved+=amount;group.add([v.index],g.weight*keep,'REPLACE')
 if moved:
    t=float(np.clip((v.co.z-1.22)/.18,0,1));body.vertex_groups['B_Spine1'].add([v.index],moved*(1-t),'ADD');body.vertex_groups['B_Spine2'].add([v.index],moved*t,'ADD')
# Keep the long native claw hands within their anatomical wrist range; preserve forearm-driven swiping.
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 for f in sorted(set([float(x) for x in np.arange(act.frame_start,act.frame_end,.5)]+[float(act.frame_end)])):
    scene.frame_set(math.floor(f),subframe=f%1)
    for sd in ['L','R']:
        pb=rig.pose.bones[f'B_{sd}_Hand'];hb=rig.data.bones[pb.name];fb=rig.data.bones[f'B_{sd}_Forearm']
        axis=(hb.matrix_local.to_3x3().inverted()@(hb.head_local-fb.head_local)).normalized()
        q=pb.rotation_quaternion.copy();angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);angle=(angle+math.pi)%(2*math.pi)-math.pi
        swing=q@Quaternion(axis,angle).inverted()
        if swing.w<0:swing=-swing
        if swing.angle>math.radians(35):swing=Quaternion().slerp(swing,math.radians(35)/swing.angle)
        pb.rotation_quaternion=swing@Quaternion(axis,float(np.clip(angle,-math.radians(75),math.radians(75))))
        pb.keyframe_insert('rotation_quaternion',frame=f,group=pb.name)
# Bake continuous twist at fractional endpoints too; avoid an atan2 wrap becoming a false forearm spin.
def twist(q,axis):return 2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 prev={};start={}
 for f in sorted(set([float(x) for x in np.arange(act.frame_start,act.frame_end,.5)]+[float(act.frame_end)])):
    scene.frame_set(math.floor(f),subframe=f%1)
    for sd in ['L','R']:
        fb,hb,ub=[rig.data.bones[f'B_{sd}_{n}'] for n in ['Forearm','Hand','UpperArm']]
        seg=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
        ua=(ub.matrix_local.inverted()@fb.head_local).normalized()
        for nm,axis,value,factor in [(f'B_{sd}_ForearmTwist',seg,twist(rel@rest.inverted(),seg),.7),(f'B_{sd}_UpperArmTwist',ua,twist(rig.pose.bones[ub.name].rotation_quaternion,ua),-.45)]:
            value=(value+math.pi)%(2*math.pi)-math.pi
            if nm in prev:value=prev[nm]+(value-prev[nm]+math.pi)%(2*math.pi)-math.pi
            prev[nm]=value;pb=rig.pose.bones[nm];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(axis,value*factor)
            if f==act.frame_start:start[nm]=pb.rotation_quaternion.copy()
            if act.name=='Flight' and f==act.frame_end:pb.rotation_quaternion=start[nm]
            pb.keyframe_insert('rotation_quaternion',frame=f,group=nm)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
for v in body.data.vertices:
 groups=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-5],key=lambda x:-x[1]);total=sum(w for gi,w in groups[:8]);assert total>.1
 for gi,w in groups[8:]:body.vertex_groups[gi].remove([v.index])
 for gi,w in groups[:8]:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
(P/'work/skin_finalize.json').write_text(json.dumps({'bones':len(rig.data.bones),'twist_source':str(shared),'geometry_unchanged':True,'corrections':['Chest-wall ownership below the armpit','Fractional, continuous forearm and upper-arm twist distribution']},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots_skin.blend'))
print('SKIN_FINAL',len(rig.data.bones))
