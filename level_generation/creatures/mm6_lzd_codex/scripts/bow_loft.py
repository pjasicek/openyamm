"""Distant bow shells follow the authored curve; the detailed wrap and horn bake from the original."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
def replace_bow(path,tag,n,zs):
 bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 mat=next(m for m in body.data.materials if 'Bow'in m.name);matrix=rig.data.bones['Bow'].matrix_local
 # The source grip was widened in round 3 while retaining the limb profile.
 verts=[];faces=[]
 for z in zs:
  t=min(1,abs(z)/.55);y=.215*(abs(z)/.55)**1.65;rx=.017*(1-.65*t);ry=.010*(1-.45*t)
  if abs(z)<=.086:rx=.0280;ry=.02125
  elif abs(z)<=.095:rx=.0270;ry=.01890
  if abs(z)>=.528:rx=.008;ry=.007
  if abs(z)>=.564:rx=.001;ry=.001
  for j in range(n):verts.append(matrix@Vector((rx*math.cos(2*math.pi*j/n),y+ry*math.sin(2*math.pi*j/n),z)))
 for i in range(len(zs)-1):
  for j in range(n):faces.append((i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n))
 faces+=[tuple(reversed(range(n))),tuple((len(zs)-1)*n+j for j in range(n))]
 me=bpy.data.meshes.new('BowLoft');me.from_pydata(verts,[],faces);me.materials.append(mat);me.attributes.new('piece','INT','POINT').data.foreach_set('value',[201]*len(verts));ob=bpy.data.objects.new('BowLoft',me);bpy.context.collection.objects.link(ob);ob.vertex_groups.new(name='Bow').add(list(range(len(verts))),1,'REPLACE')
 uv=me.uv_layers.new(name='UVMap')
 for f in me.polygons:
  f.use_smooth=True
  for li in f.loop_indices:
   v=me.loops[li].vertex_index;uv.data[li].uv=((v%n)/n,(v//n)/(len(zs)-1))
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 bm=bmesh.new();bm.from_mesh(body.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[la]==201],context='VERTS');bm.to_mesh(body.data);bm.free();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
 # Generate a non-overlapping new bow UV domain; rays rebake every texture.
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for f in body.data.polygons:f.select=all(body.data.attributes['piece'].data[i].value==201 for i in f.vertices)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.151917,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
 path=P/f'work/rebake/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));return path
