"""Native black spiked mace with silver shaft, rigged release, and corpse hold."""
import bpy,bmesh,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
g=json.loads((P/'work/grip_pose.json').read_text());hm=rig.data.bones['B_R_Hand'].matrix_local
centre=hm@Vector(g['handle_centre_hand_local']);axis=(hm.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized()
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Mace');b.head=centre;b.tail=centre+axis*.15;b.parent=rig.data.edit_bones['B_R_Hand']
bpy.ops.object.mode_set(mode='OBJECT')
bm=bmesh.new();classes=bm.faces.layers.int.new('mace_class')
def cone(a,b,r0,r1,n,cls):
 a,b=Vector(a),Vector(b);d=b-a
 before=set(bm.faces)
 res=bmesh.ops.create_cone(bm,cap_ends=True,segments=n,radius1=r0,radius2=r1,depth=d.length)
 mat=Matrix.Translation((a+b)*.5)@d.to_track_quat('Z','Y').to_matrix().to_4x4()
 bmesh.ops.transform(bm,matrix=mat,verts=res['verts'])
 for f in set(bm.faces)-before:f[classes]=cls
# A long enough leather grip supports the fitted thumb; the narrow metal shaft continues to the black head.
cone(centre-axis*.085,centre+axis*.095,.012,.012,10,1)
cone(centre-axis*.099,centre-axis*.085,.014,.014,10,2)
cone(centre+axis*.095,centre+axis*.365,.010,.009,10,2)
cone(centre+axis*.34,centre+axis*.355,.015,.015,10,2)
hc=centre+axis*.385
before=set(bm.faces);res=bmesh.ops.create_icosphere(bm,subdivisions=2,radius=.054)
bmesh.ops.translate(bm,verts=res['verts'],vec=hc)
for f in set(bm.faces)-before:f[classes]=3
u=axis.orthogonal().normalized();v=axis.cross(u)
for i in range(8):
 a=2*math.pi*i/8;d=u*math.cos(a)+v*math.sin(a)
 cone(hc+d*.046,hc+d*.080,.014,0,5,3)
for sign in (-1,1):cone(hc+axis*.046*sign,hc+axis*.078*sign,.014,0,5,3)
me=bpy.data.meshes.new('MaceMesh');bm.to_mesh(me);bm.free()
mace=bpy.data.objects.new('Mace',me);scene.collection.objects.link(mace)
mace.parent=rig;mod=mace.modifiers.new('Armature','ARMATURE');mod.object=rig
mace.vertex_groups.new(name='Mace').add(list(range(len(me.vertices))),1,'REPLACE')
for c,color in enumerate(((.15,.055,.02,1),(.38,.40,.42,1),(.015,.018,.02,1)),1):
 mat=bpy.data.materials.new('MaceClass'+str(c));mat.diffuse_color=color;me.materials.append(mat)
for f in me.polygons:
 f.material_index=me.attributes['mace_class'].data[f.index].value-1
 f.use_smooth=f.material_index<2
tris=sum(len(f.vertices)-2 for f in me.polygons)
assert tris+sum(len(f.vertices)-2 for f in body.data.polygons)<10000
print('MACE triangles',tris,'BODY',sum(len(f.vertices)-2 for f in body.data.polygons))
def setact(act):
 rig.animation_data.action=act
 if act and len(act.slots):rig.animation_data.action_slot=act.slots[0]
pb=rig.pose.bones['Mace'];pb.rotation_mode='QUATERNION'
# Every clip defines the prop channel; action switching must never retain the dropped transform.
for act in list(bpy.data.actions):
 if not act.use_fake_user:continue
 setact(act)
 for f in (0,int(act.frame_range[1])):
  pb.rotation_quaternion=Quaternion();pb.location=(0,0,0)
  pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
death=bpy.data.actions['Death'];setact(death);end=int(death.frame_range[1]);release=8
scene.frame_set(release);start=pb.matrix.copy();startq=start.to_quaternion();startc=start.translation.copy()
# Finish beside the supine body's right arm, outside the body's footprint, with the shaft lying on the floor.
scene.frame_set(end)
hand=rig.pose.bones['B_R_Hand'].matrix.translation.copy()
finish=Vector((hand.x-.24,hand.y,.09));finaldir=Vector((.20,.96,.0)).normalized()
finalq=finaldir.to_track_quat('Y','Z')
rest=rig.data.bones['Mace'].matrix_local
invrest=rest.inverted();local=[invrest@v.co for v in me.vertices]
settle=min(end,release+25)
for f in range(end+1):
 scene.frame_set(f)
 if f<release:
  target=rig.pose.bones['B_R_Hand'].matrix@rig.data.bones['B_R_Hand'].matrix_local.inverted()@rest
 else:
  t=min(1,(f-release)/max(settle-release,1));s=t*t*(3-2*t)
  c=startc.lerp(finish,s);c.z+=.25*math.sin(math.pi*t)
  q=startq.slerp(finalq,s)@Quaternion((0,0,1),2*math.pi*t)
  target=Matrix.Translation(c)@q.to_matrix().to_4x4()
  low=min((target@v).z for v in local)
  if low<.006:target.translation.z+=.006-low
 pb.matrix=target
 pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
# Dead holds every final channel, including the released mace.
scene.frame_set(end);held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
act=bpy.data.actions.new('Dead');act.use_fake_user=True;setact(act)
for f in (0,30):
 for n,(q,l) in held.items():
  b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l
  b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=30
# Sign continuity and linear sampling avoid interpolation spins between the baked frames.
for act in bpy.data.actions:
 fcs=[fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
 curves={}
 for fc in fcs:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
  if fc.data_path.endswith('rotation_quaternion'):curves.setdefault(fc.data_path,{})[fc.array_index]=fc
 for components in curves.values():
  if len(components)!=4:continue
  ks=[components[i].keyframe_points for i in range(4)];last=None
  for j in range(min(map(len,ks))):
   q=[ks[i][j].co[1] for i in range(4)]
   if last and sum(a*b for a,b in zip(q,last))<0:
    for i in range(4):ks[i][j].co[1]*=-1
    q=[-x for x in q]
   last=q
setact(bpy.data.actions['Dead']);scene.frame_set(0)
ev=mace.evaluated_get(bpy.context.evaluated_depsgraph_get());pm=ev.to_mesh();coords=np.array([tuple(mace.matrix_world@v.co) for v in pm.vertices]);ev.to_mesh_clear()
print('MACE corpse bounds',coords.min(0).round(3).tolist(),coords.max(0).round(3).tolist())
setact(None)
for b in rig.pose.bones:b.matrix_basis.identity()
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v7.blend'))
