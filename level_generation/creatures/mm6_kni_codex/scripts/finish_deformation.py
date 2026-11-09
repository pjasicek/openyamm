"""Remove hidden upper leggings under the solid fauld; ease only the free hand's opening/closing."""
import bpy,bmesh,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body_pre_cloth.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
# Three overlapping plate sections articulate independently; no thigh can shear through its own rigid tasset.
source=bmesh.new();source.from_mesh(body.data);pl=source.verts.layers.int['piece'];bmesh.ops.delete(source,geom=[f for f in source.faces if any(v[pl]!=8 for v in f.verts)],context='FACES')
parts=[]
for part,side in [(200,0),(201,1),(202,-1)]:
 bm=source.copy();geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
 bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-6,plane_co=(0,0,.96 if side==0 else 1.03),plane_no=(0,0,1),clear_inner=side==0,clear_outer=side!=0)
 if side:
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,0),plane_no=(1,0,0),clear_inner=side==1,clear_outer=side==-1)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));attr=bm.verts.layers.int['piece']
 for v in bm.verts:v[attr]=part
 mesh=bpy.data.meshes.new('Fauld');bm.to_mesh(mesh);bm.free();ob=bpy.data.objects.new('Fauld',mesh);bpy.context.scene.collection.objects.link(ob)
 for mat in body.data.materials:mesh.materials.append(mat)
 for g in body.vertex_groups:ob.vertex_groups.new(name=g.name)
 for v in mesh.vertices:
  for e in v.groups[:]:ob.vertex_groups[e.group].remove([v.index])
 name='B_Pelvis' if not side else 'B_L_Thigh' if side==1 else 'B_R_Thigh';ob.vertex_groups[name].add(list(range(len(mesh.vertices))),1,'REPLACE');parts.append(ob)
source.free();bm=bmesh.new();bm.from_mesh(body.data);pl=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if all(v[pl]==8 for v in f.verts)],context='FACES');bm.to_mesh(body.data);bm.free()
for o in bpy.data.objects:o.select_set(o in parts or o==body)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
# Hidden upper leggings use the same thigh transform as the moving tasset; recess their upper contour.
from mathutils import Vector
pv=body.data.attributes['piece'].data
for v in body.data.vertices:
 if pv[v.index].value!=6:continue
 side='L' if v.co.x>0 else 'R';h=rig.data.bones[f'B_{side}_Thigh'].head_local;k=rig.data.bones[f'B_{side}_Calf'].head_local;axis=(k-h).normalized();along=(v.co-h).dot(axis);centre=h+axis*along
 t=max(0,min(1,(v.co.z-.70)/.18));v.co=centre+(v.co-centre)*(1-.50*t)
 blend=max(0,min(1,(v.co.z-.95)/.07))
 for e in v.groups[:]:body.vertex_groups[e.group].remove([v.index])
 body.vertex_groups[f'B_{side}_Thigh'].add([v.index],1-blend,'REPLACE');body.vertex_groups['B_Pelvis'].add([v.index],blend,'REPLACE')
names=[b.name for b in rig.pose.bones if b.name.startswith('B_L_Finger')]
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0);home={n:rig.pose.bones[n].rotation_quaternion.copy() for n in names}
for role,frames in [('Attack',10),('Fidget',24)]:
 ac=bpy.data.actions[role];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];samples=[]
 for f in range(frames+1):scene.frame_set(f);samples.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in names})
 for f,pose in enumerate(samples):
  u=f/frames;u=u*u*(3-2*u)
  for n,q in pose.items():
   q0=home[n]
   if q0.dot(q)<0:q=-q
   pb=rig.pose.bones[n];pb.rotation_quaternion=q0.slerp(q,u);pb.keyframe_insert('rotation_quaternion',frame=f)
# A look-around fidget keeps the empty hand relaxed, without the source's incidental finger clench.
ac=bpy.data.actions['Fidget'];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0]
for f in range(int(ac.frame_range[1])+1):
 for n,q in home.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_body.blend'))
