import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fixed.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
G=json.loads((P/'work/grip_pose.json').read_text());c=Vector(G['handle_centre_hand_local']);ax=Vector(G['handle_axis_hand_local']).normalized();Hm=rig.data.bones['B_R_Hand'].matrix_local
side=Hm.inverted()@rig.data.bones['B_R_Finger2'].head_local-c;side=(side-ax*side.dot(ax)).normalized()
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];mats=[];times=np.arange(0,float(a.frame_range[1])+1e-6,30/48)
for f in times:scene.frame_set(int(f),subframe=f-int(f));mats.append((rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix).copy())
def mapping(roll):
 ed=Matrix.Rotation(math.radians(roll),3,ax)@side;flat=ax.cross(ed);M=Matrix((ax*.8,flat*.88,-ed*.88)).transposed().to_4x4();M.translation=c;return M,ed
sweep=[]
for r in range(0,360,5):
 M,ed=mapping(r);loc=M@Vector((.405,0,-.175));points=np.array([tuple(m@loc)for m in mats]);vel=np.diff(points,axis=0)*48;forward=np.array([-(m.to_3x3()@ax).y for m in mats[:-1]]);speeds=np.linalg.norm(vel,axis=1);score=np.where(forward>.50,speeds,0);k=int(np.argmax(score));edge=(mats[k].to_3x3()@ed).normalized();signed=float(Vector(vel[k]).normalized().dot(edge));flat=(mats[k].to_3x3()@ax.cross(ed)).normalized();share=abs(float(Vector(vel[k]).dot(edge)))/max(math.hypot(Vector(vel[k]).dot(edge),Vector(vel[k]).dot(flat)),1e-8);sweep.append({'roll':r,'signed_lead':signed,'edge_share':share,'speed_m_s':float(speeds[k]),'impact_s':float((times[k]+times[k+1])/60)})
best=max(sweep,key=lambda x:x['signed_lead']);M,ed=mapping(best['roll']);print('AXE ROLL',best);(P/'work/axe_attachment.json').write_text(json.dumps({'selected':best,'hand_local_matrix':[list(r)for r in M],'sweep':sweep,'geometry_scale':[.8,.88,.88]},indent=2))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
with bpy.data.libraries.load(str(P/'work/axe_clay.blend'),link=False)as(src,dst):dst.objects=['Axe']
axe=dst.objects[0];bpy.context.collection.objects.link(axe);axe.data.transform(Hm@M);axe.matrix_world=Matrix.Identity(4)
for o in bpy.data.objects:o.select_set(o==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new('Axe');b.head=Hm@c;b.tail=b.head+(Hm.to_3x3()@ax)*.1;b.parent=rig.data.edit_bones['B_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
axe.vertex_groups.new(name='Axe').add(list(range(len(axe.data.vertices))),1,'REPLACE');mod=axe.modifiers.new('Rig','ARMATURE');mod.object=rig;axe.parent=rig
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilot.blend'))
common.workbench_clay(scene)
for n in ['Standing','Walking','Attack','Fidget','Death']:
 a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i in range(5):
  f=float(a.frame_range[1])*i/4;scene.frame_set(int(f),subframe=f-int(f));common.render_views(str(P/f'review/pilot_axe_{n}_{i}'),.72,2.0,views=('front','left','three_quarter'),resolution=(270,390))
