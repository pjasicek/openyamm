"""Attach the separate sword and palm spell socket; bake the dropped sword into the death."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_final_motion.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text());C=Vector(G['handle_centre_hand_local']);Y=Vector(G['handle_axis_hand_local']).normalized()
def setact(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
a=bpy.data.actions['Attack'];setact(a);time=json.loads((P/'work/clip_timing.json').read_text())
tips=[];directions=[]
for frame in range(int(a.frame_range[1])+1):
 sc.frame_set(frame);h=rig.pose.bones['B_R_Hand'].matrix;direction=h.to_3x3()@Y;tips.append(h@(C+Y*1.361));directions.append(direction)
speeds=[(b-a).length*30 for a,b in zip(tips,tips[1:])];candidates=[i for i in range(len(speeds)) if directions[i].y<-.5 and tips[i].y<-.6];peak=max(candidates,key=lambda i:speeds[i]);time['attack_impact_s']=(peak+.5)/30;time['attack_tip_speed_mps']=speeds[peak];(P/'work/clip_timing.json').write_text(json.dumps(time,indent=1));f=time['attack_impact_s']*30
sc.frame_set(int(f));h=rig.pose.bones['B_R_Hand'].matrix.copy();p0=h@(C+Y*1.361)
sc.frame_set(int(f)+1);p1=rig.pose.bones['B_R_Hand'].matrix@(C+Y*1.361)
X=h.to_3x3().inverted()@(p1-p0);X=(X-Y*X.dot(Y)).normalized();Z=X.cross(Y).normalized();X=Y.cross(Z).normalized()
local=Matrix((X,Y,Z)).transposed().to_4x4();local.translation=C
setact(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,parent,m in [('Socket_Sword','B_R_Hand',rig.data.edit_bones['B_R_Hand'].matrix@local),('Socket_Spell','B_L_Hand',rig.data.edit_bones['B_L_Hand'].matrix@Matrix.Translation((0,.085,-.025)))]:
    b=rig.data.edit_bones.new(name);b.head=m.translation;b.tail=b.head+m.col[1].to_3d()*.06;b.align_roll(m.col[2].to_3d());b.parent=rig.data.edit_bones[parent];b.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
# The prop preview and final export use this socket frame with +Y toward the blade tip.
with bpy.data.libraries.load(str(P/'work/sword.blend'),link=False) as (src,dst):dst.objects=['SwordMesh']
sword=dst.objects[0];bpy.context.collection.objects.link(sword)
sword.parent=rig;sword.parent_type='BONE';sword.parent_bone='Socket_Sword'
# Blender bone parenting locates the child at the tail; cancel that translation.
sword.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones['Socket_Sword'].length,0));sword.matrix_basis=Matrix()
death=bpy.data.actions['Death'];setact(death);sc.frame_set(12);start=rig.pose.bones['Socket_Sword'].matrix.copy()
dir=Vector((-.24,-.97,0)).normalized();z=Vector((0,0,1));x=dir.cross(z).normalized();end=Matrix((x,dir,z)).transposed().to_4x4();end.translation=Vector((-.78,-.5,.033))
for ac in list(bpy.data.actions):
    if not ac.use_fake_user:continue
    setact(ac);prev=None
    for f in range(int(ac.frame_range[1])+1):
        sc.frame_set(f);pb=rig.pose.bones['Socket_Sword'];pb.rotation_mode='QUATERNION';pb.matrix_basis=Matrix();bpy.context.view_layer.update()
        if ac.name in ('Death','Dead'):
            t=1 if ac.name=='Dead' else max(0,min(1,(f-12)/17));e=t*t*(3-2*t)
            if t>0:
                m=start.to_quaternion().slerp(end.to_quaternion(),e).to_matrix().to_4x4();m.translation=start.translation.lerp(end.translation,e)
                # An arc and eased settling; the blade's full length remains above the floor while turning.
                m.translation.z+=.18*math.sin(math.pi*t)
                low=min((m@Vector((0,y,0))).z for y in (-.289,1.361))
                if low<.018:m.translation.z+=.018-low
                pb.matrix=m;bpy.context.view_layer.update()
        q=pb.rotation_quaternion.copy()
        if prev is not None and q.dot(prev)<0:q=-q
        prev=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
        spell=rig.pose.bones['Socket_Spell'];spell.rotation_mode='QUATERNION';spell.matrix_basis=Matrix();spell.keyframe_insert('rotation_quaternion',frame=f);spell.keyframe_insert('location',frame=f)
setact(None)
(P/'work/sockets.json').write_text(json.dumps({'sword_local_matrix':[list(row) for row in local],'sword_release_s':.4,'sword_settle_s':29/30,'spell_node':'Socket_Spell','sword_node':'Socket_Sword'},indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_assembled.blend'))
common.workbench_clay(sc)
for name in ['Standing','Attack','Death','Cast']:
    ac=bpy.data.actions[name];setact(ac)
    for i in range(5):
        f=ac.frame_range[1]*i/4;sc.frame_set(int(f),subframe=f-int(f))
        common.render_views(str(P/f'review/assembled/{name}_{i}'),1.0,3.4,views=('front','left','three_quarter'),resolution=(280,400),target=(0,.15))
