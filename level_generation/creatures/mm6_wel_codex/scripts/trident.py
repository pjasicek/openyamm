"""Separate native three-prong bronze trident, fitted to the solved palm tunnel."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];D=json.loads((P/'work/rig.json').read_text());G=json.loads((P/'work/grip_pose.json').read_text());H=rig.data.bones['B_R_Hand'].matrix_local
origin=H@Vector(G['handle_centre_hand_local']);axis=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();x=H.to_3x3()@Vector((0,1,0));x=(x-axis*x.dot(axis)).normalized();z=x.cross(axis);R=Matrix((x,axis,z)).transposed()
verts=[];faces=[]
def tube(points,radii,sides=8):
 offset=len(verts)
 for i,p in enumerate(points):
  a=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)]);a.normalize();b=Vector((0,0,1));c=a.cross(b).normalized()
  for j in range(sides):verts.append(tuple(origin+R@(Vector(p)+radii[i]*(b*math.cos(j*2*math.pi/sides)+c*math.sin(j*2*math.pi/sides)))))
 faces.append(tuple(offset+j for j in range(sides-1,-1,-1)))
 for i in range(len(points)-1):
  for j in range(sides):faces.append((offset+i*sides+j,offset+i*sides+(j+1)%sides,offset+(i+1)*sides+(j+1)%sides,offset+(i+1)*sides+j))
 faces.append(tuple(offset+(len(points)-1)*sides+j for j in range(sides)))
tube([(0,-.85,0),(0,1.05,0),(0,1.43,0),(0,1.62,0)],[.010,.013,.024,0],10)
for sign in [-1,1]:
 tube([(0,.96,0),(sign*.08,.98,0),(sign*.16,1.04,0),(sign*.21,1.15,0),(sign*.20,1.35,0),(sign*.14,1.53,0)],[.013,.014,.014,.013,.019,0])
for y in [-.75,.52,.57,.98]:tube([(0,y,0),(0,y+.018,0)],[.018,.018],10)
me=bpy.data.meshes.new('Trident');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Trident',me);bpy.context.collection.objects.link(ob)
mat=bpy.data.materials.new('TridentBronze');mat.diffuse_color=(.18,.068,.036,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.18,.068,.036,1);bs.inputs['Metallic'].default_value=.65;bs.inputs['Roughness'].default_value=.48;me.materials.append(mat)
for f in me.polygons:f.use_smooth=True
bpy.context.view_layer.objects.active=rig;bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,h,t,parent in [('Trident',origin,origin+axis*.1,'B_R_Hand'),('Socket_Trident_Head',origin+axis*1.47,origin+axis*1.57,'Trident')]:
 b=rig.data.edit_bones.new(name);b.head=h;b.tail=t;b.align_roll(z);b.parent=rig.data.edit_bones[parent];D['bones'][name]={'head':list(h),'tail':list(t),'parent':parent,'rot':list(map(list,R))}
bpy.ops.object.mode_set(mode='OBJECT')
g=ob.vertex_groups.new(name='Trident');g.add(list(range(len(me.vertices))),1,'REPLACE');ob.parent=rig;mod=ob.modifiers.new('Rigid attachment','ARMATURE');mod.object=rig
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
D['trident']={'grip_hand':G['handle_centre_hand_local'],'axis_hand':G['handle_axis_hand_local'],'radius':G['radius'],'below_grip':.85,'above_grip':1.62};D['bone_count']=len(rig.data.bones)
(P/'work/rig.json').write_text(json.dumps(D,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_prop.blend'))
assert D['bone_count']<=128
print('TRIDENT',len(verts),'vertices',len(faces),'polygons',D['bone_count'],'bones')
