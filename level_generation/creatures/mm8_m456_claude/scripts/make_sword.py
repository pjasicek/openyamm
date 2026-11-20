"""Native serrated blade from the selected HD silhouette; solid bevel, guard, grip and pommel."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
D=json.loads((p/'textures/props/sword_profile.json').read_text());px=D['metres_per_pixel'];cx,cy=D['grip_centre'];x0,y0,x1,y1=D['crop']
bpy.ops.wm.read_factory_settings(use_empty=True);V=[];F=[];UV=[]
def add(x,y,z):
 V.append(((x-cx)*px,(cy-y)*px,z));UV.append(((x-x0)/(x1-x0),1-(y-y0)/(y1-y0)));return len(V)-1
def rings(rows):
 last=None
 for row,l,r,th in rows:
  wd=r-l;cur=[add(x,row,z) for x,z in [(l,0),(l+.12*wd,th),(r-.12*wd,th),(r,0),(r-.12*wd,-th),(l+.12*wd,-th)]]
  if last:
   for k in range(6):F.append([last[k],cur[k],cur[(k+1)%6],last[(k+1)%6]])
  else:F.append(cur[::-1])
  last=cur
 F.append(last)
rings([(int(y),*v,.003*min(1,(int(y)-38)/70)) for y,v in sorted(D['rows'].items(),key=lambda a:-int(a[0]))])
# Short recurved quillons, following the native and HD silhouette.
last=None
for x,row in [(408,1182),(430,1196),(475,1210),(512,1214),(549,1210),(594,1196),(615,1182)]:
 cur=[add(x,row+dy,z) for dy,z in [(-8,-.006),(-8,.006),(8,.006),(8,-.006)]]
 if last:
  for k in range(4):F.append([last[k],cur[k],cur[(k+1)%4],last[(k+1)%4]])
 else:F.append(cur[::-1])
 last=cur
F.append(last)
last=None
for row,r in [(1230,.012),(1260,.012),(1330,.012),(1405,.011)]:
 cur=[add(cx+r/px*math.cos(2*math.pi*k/10),row,r*math.sin(2*math.pi*k/10)) for k in range(10)]
 if last:
  for k in range(10):F.append([last[k],cur[k],cur[(k+1)%10],last[(k+1)%10]])
 else:F.append(cur[::-1])
 last=cur
F.append(last)
last=None
for j in range(7):
 t=math.pi*j/6;row=1461+33*math.cos(t);r=.030*math.sin(t);cur=[add(cx+r/px*math.cos(2*math.pi*k/12),row,r*math.sin(2*math.pi*k/12)) for k in range(12)]
 if last:
  for k in range(12):F.append([last[k],cur[k],cur[(k+1)%12],last[(k+1)%12]])
 last=cur
me=bpy.data.meshes.new('SwordMesh');me.from_pydata(V,[],F);me.update();uv=me.uv_layers.new(name='UVMap')
for f in me.polygons:
 for li in f.loop_indices:uv.data[li].uv=UV[me.loops[li].vertex_index]
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-7);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free();assert not me.validate()
o=bpy.data.objects.new('SwordMesh',me);bpy.context.scene.collection.objects.link(o);mat=bpy.data.materials.new('DragonHunterSword_A');mat.use_nodes=True;n=mat.node_tree.nodes;bs=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'textures/props/sword_basecolor.png'));mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.42;me.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/sword.blend'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_ready.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.context.view_layer.update();g=json.loads((p/'work/grip_pose.json').read_text());h=rig.data.bones['B_L_Hand'].matrix_local;c=h@Vector(g['handle_centre_hand_local']);axis=(h.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized()
kn=rig.data.bones['B_L_Finger2'].head_local;edge=kn-c;edge=(edge-axis*edge.dot(axis)).normalized();flat=edge.cross(axis).normalized();R=Matrix([edge,axis,flat]).transposed();assert abs(R.determinant()-1)<1e-5
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');bone=rig.data.edit_bones.new('Sword');bone.head=c;bone.tail=c+axis*.15;bone.align_roll(flat);bone.parent=rig.data.edit_bones['B_L_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(p/'work/sword.blend'),link=False) as (_,dst):dst.objects=['SwordMesh']
o=dst.objects[0];bpy.context.scene.collection.objects.link(o)
for v in o.data.vertices:v.co=c+R@v.co
vg=o.vertex_groups.new(name='Sword');vg.add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;m=o.modifiers.new('Armature','ARMATURE');m.object=rig
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_equipped.blend'))
print('SWORD',len(o.data.polygons),'triangles')
