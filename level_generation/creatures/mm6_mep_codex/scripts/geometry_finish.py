import bpy,bmesh,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common,pose_helpers as ph
bpy.ops.wm.open_mainfile(filepath=str(p/'work/anim_twist.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ph.init(r);ph.setact(None)
for pb in r.pose.bones:pb.matrix_basis.identity()
ph.update();bm=bmesh.new();bm.from_mesh(b.data);part=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[part]==7],context='VERTS');bm.to_mesh(b.data);bm.free()
# Replace the inflated waist knot with the folded sash seen in the native frames.
verts=[];faces=[];N=64;profiles=[(1.034,.97),(1.041,1.02),(1.054,1.035),(1.071,1.01),(1.089,1.025),(1.099,.97)]
for z,fac in profiles:
 for i in range(N):
  a=math.tau*i/N;verts.append((.168*fac*math.cos(a),.008+.161*fac*math.sin(a),z+.002*math.sin(3*a)))
for j in range(len(profiles)-1):
 for i in range(N):
  a=j*N+i;d=j*N+(i+1)%N;faces.extend([(a,d,d+N),(a,d+N,a+N)])
mesh=bpy.data.meshes.new('Sash');mesh.from_pydata(verts,[],faces);ob=bpy.data.objects.new('Sash',mesh);bpy.context.collection.objects.link(ob);mesh.attributes.new('piece','INT','POINT').data.foreach_set('value',[7]*len(verts));vg=ob.vertex_groups.new(name='B_Pelvis');vg.add(list(range(len(verts))),1.,'REPLACE')
ob.data.materials.append(b.data.materials[0]);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);b.select_set(True);bpy.context.view_layer.objects.active=b;bpy.ops.object.join()
for poly in b.data.polygons:poly.use_smooth=True
# Carry one curved natural-wood staff from the fitted right-hand grip.
G=json.loads((p/'work/grip_pose.json').read_text());h=r.data.bones['B_R_Hand'];gc=Vector(G['handle_centre_hand_local']);ga=Vector(G['handle_axis_hand_local']);head=h.matrix_local@gc;axis=h.matrix_local.to_3x3()@ga
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');eb=r.data.edit_bones.new('Staff');eb.head=head;eb.tail=head+axis*.12;eb.parent=r.data.edit_bones['B_R_Hand'];eb.use_deform=True;bpy.ops.object.mode_set(mode='OBJECT');M=r.data.bones['Staff'].matrix_local.copy()
ph.setact(bpy.data.actions['Standing']);bpy.context.scene.frame_set(0);gripz=r.pose.bones['Staff'].head.z;bottom=-gripz+.012;top=.33
V=[];F=[];UV=[];rings=45;sides=20
for j in range(rings):
 t=j/(rings-1);y=bottom+(top-bottom)*t;gripfade=min(1,abs(y)/.14);dx=gripfade*(.007*math.sin(t*math.tau*1.2)+.003*math.sin(t*math.tau*3));dz=gripfade*.004*math.sin(t*math.tau*2)
 radius=.0065+.009*t
 if abs(y)<.10:radius=.0125;dx=dz=0
 for i in range(sides):
  a=math.tau*i/sides;knots=sum(.0025*math.exp(-((t-k)/.015)**2)*max(0,math.cos(a-aa))**6 for k,aa in [(.24,1),(.55,3.1),(.82,5.1)]);rad=radius+knots+gripfade*.0006*math.sin(5*a+8*t)
  V.append(tuple(M@Vector((dx+rad*math.cos(a),y,dz+rad*math.sin(a)))))
for j in range(rings-1):
 for i in range(sides):
  a=j*sides+i;d=j*sides+(i+1)%sides;F.append((a,d,d+sides,a+sides));UV.append([(i/sides,j/(rings-1)),((i+1)/sides,j/(rings-1)),((i+1)/sides,(j+1)/(rings-1)),(i/sides,(j+1)/(rings-1))])
for j in [0,rings-1]:
 ids=list(range(j*sides,(j+1)*sides));ids=ids[::-1] if j==0 else ids;F.append(tuple(ids));UV.append([(.5+.03*math.cos(math.tau*i/sides),.99 if j else .01) for i in range(sides)])
me=bpy.data.meshes.new('StaffMesh');me.from_pydata(V,[],F);staff=bpy.data.objects.new('StaffMesh',me);bpy.context.collection.objects.link(staff);uv=me.uv_layers.new(name='UVMap')
for f,coords in zip(me.polygons,UV):
 for li,xy in zip(f.loop_indices,coords):uv.data[li].uv=xy
 f.use_smooth=True
vg=staff.vertex_groups.new(name='Staff');vg.add(list(range(len(V))),1.,'REPLACE');mod=staff.modifiers.new('Armature','ARMATURE');mod.object=r;staff.parent=r
ph.setact(None)
for pb in r.pose.bones:pb.matrix_basis.identity()
ph.update();bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');eb=r.data.edit_bones.new('Socket_Staff_Head');eb.head=M@Vector((0,top,0));eb.tail=eb.head+axis*.05;eb.parent=r.data.edit_bones['Staff'];eb.use_deform=False;bpy.ops.object.mode_set(mode='OBJECT')
# The death clip releases the stick; all other roles carry it from the fitted hand.
held=None
for role in ['Standing','Fidget','Walking','Running','Hit','Attack','Cast','Death','Dead']:
 act=bpy.data.actions[role];ph.setact(act);pb=r.pose.bones['Staff'];pb.rotation_mode='QUATERNION';previous=None
 for f in range(int(act.frame_range[1])+1):
  bpy.context.scene.frame_set(f);pb.matrix_basis.identity();ph.update()
  if role=='Death':
   if f==18:release=pb.matrix.copy()
   if f>18:
    t=ph.smooth((f-18)/24);q=release.to_quaternion().slerp(Vector((0,1,0)).rotation_difference(Vector((1,0,0))),t);m=q.to_matrix().to_4x4();m.translation=release.translation.lerp(Vector((-.65,-.25,.025)),t);pb.matrix=m;ph.update()
    world=[pb.matrix@(M.inverted()@Vector(v)) for v in V];low=min(v.z for v in world)
    if low<.002:m=pb.matrix.copy();m.translation.z+=.002-low;pb.matrix=m;ph.update()
   held=pb.matrix.copy()
  elif role=='Dead':pb.matrix=held;ph.update()
  q=pb.rotation_quaternion.copy()
  if previous is not None and q.dot(previous)<0:q.negate();pb.rotation_quaternion=q
  previous=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
ph.setact(None)
for pb in r.pose.bones:pb.matrix_basis.identity()
ph.update();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/geometry_final.blend'))
# Static uploads retain exact topology; Meshy's body UV layout is transferred back to this animated master.
if 'head' in b.data.attributes:b.data.attributes.remove(b.data.attributes['head'])
weights=np.array([sum(g.weight for g in v.groups if b.vertex_groups[g.group].name in ['B_Head','B_Neck']) for v in b.data.vertices]);hd=[int(np.mean(weights[list(f.vertices)])>.5) for f in b.data.polygons];b.data.attributes.new('head','INT','FACE').data.foreach_set('value',hd)
for layer in list(b.data.uv_layers):b.data.uv_layers.remove(layer)
b.data.uv_layers.new(name='UVMap');headuv=b.data.uv_layers.new(name='HeadUV');b.data.uv_layers.active=headuv
bpy.ops.object.select_all(action='DESELECT');b.select_set(True);bpy.context.view_layer.objects.active=b
for f in b.data.polygons:f.select=bool(hd[f.index])
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.006);bpy.ops.uv.pack_islands(margin=.006,rotate=True);bpy.ops.object.mode_set(mode='OBJECT');b.data.uv_layers.active=b.data.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/texture_master.blend'))
for kind in ['body','head']:
 ob=b.copy();ob.data=b.data.copy();ob.parent=None;ob.modifiers.clear();ob.vertex_groups.clear();bpy.context.collection.objects.link(ob)
 if kind=='head':
  bm=bmesh.new();bm.from_mesh(ob.data);tag=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[tag]],context='FACES');bm.to_mesh(ob.data);bm.free()
 ob.data.uv_layers.active=ob.data.uv_layers['HeadUV' if kind=='head' else 'UVMap']
 for uv in list(ob.data.uv_layers):
  if uv!=ob.data.uv_layers.active:ob.data.uv_layers.remove(uv)
 ob.data.materials.clear();bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.gltf(filepath=str(p/f'texturing/mep_{kind}_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False,export_materials='NONE')
 bpy.data.objects.remove(ob,do_unlink=True)
(p/'work/staff_geometry.json').write_text(json.dumps({'triangles':sum(len(f.vertices)-2 for f in me.polygons),'length_m':top-bottom,'grip_radius_m':.0125,'bottom':bottom,'top':top,'release_seconds':.6},indent=2))
