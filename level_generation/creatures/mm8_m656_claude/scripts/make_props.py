"""Two low-poly rigid props with planar UVs from the selected HD sheet."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.context.view_layer.update()
G=json.loads((P/'work/grip_pose.json').read_text());Hm=rig.data.bones['B_R_Hand'].matrix_local
c=Hm@Vector(G['handle_centre_hand_local']);axis=(Hm.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,par,head,along,roll in [('Sword','B_R_Hand',c,axis,Hm.to_3x3().col[2]),('Scabbard','B_Pelvis',Vector((.245,0,.98)),Vector((-.28,-.12,.953)).normalized(),Vector((1,0,0)))]:
 b=rig.data.edit_bones.new(name);b.head=head;b.tail=head+along*.15;b.parent=rig.data.edit_bones[par];b.align_roll(roll)
bpy.ops.object.mode_set(mode='OBJECT')
def build(name):
 bm=bmesh.new();uvl=bm.loops.layers.uv.new('UVMap');scale=.89/(1487-35) if name=='Sword' else .735/(1470-235)
 x0,x1,centre,row=(240,480,358,1310) if name=='Sword' else (578,766,672,235)
 def uv(v):return ((centre+v.co.x/scale-x0)/(x1-x0),1-(row-v.co.y/scale)/1536)
 def rings(rows,sides=4):
  # Each cross-section is (row, half-width, half-thickness), widths in metres.
  previous=None
  for r,w,t in rows:
   ring=[bm.verts.new((w*math.cos(2*math.pi*k/sides),(row-r)*scale,t*math.sin(2*math.pi*k/sides))) for k in range(sides)]
   if previous:
    for i in range(sides):bm.faces.new((previous[i],previous[(i+1)%sides],ring[(i+1)%sides],ring[i]))
   else:bm.faces.new(list(reversed(ring)))
   previous=ring
  bm.faces.new(previous)
 if name=='Sword':
  rings([(35,.0005,.0005),(100,.0125,.002),(200,.019,.003),(600,.022,.003),(1169,.025,.003)])
  rings([(1170,.065,.007),(1208,.065,.007)],4)
  rings([(1210,.0105,.0105),(1385,.0105,.0105)],8)
  rings([(1390,.011,.005),(1410,.021,.005),(1450,.025,.005),(1487,.004,.004)],8)
 else:
  rings([(235,.025,.010),(260,.028,.011),(290,.028,.010),(620,.027,.009),(1100,.024,.008),(1360,.018,.007),(1468,.002,.002)],8)
  # Two flat leather belt straps bridge the sheath to its waist attachment.
  for r in [265,350]:
   rings([(r,.038,.012),(r+22,.038,.012)],8)
 bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bmesh.ops.triangulate(bm,faces=bm.faces[:])
 assert bm.calc_volume(signed=True)>0
 for f in bm.faces:
  for l in f.loops:l[uvl].uv=uv(l.vert)
 me=bpy.data.meshes.new(name+'Mesh');bm.to_mesh(me);bm.free()
 obj=bpy.data.objects.new(name+'Mesh',me);bpy.context.collection.objects.link(obj)
 transform=rig.data.bones[name].matrix_local
 for v in me.vertices:v.co=transform@v.co
 obj.vertex_groups.new(name=name).add(list(range(len(me.vertices))),1,'REPLACE')
 mod=obj.modifiers.new('Rig','ARMATURE');mod.object=rig
 print('PROP',name,len(me.polygons),'triangles')
 return obj
for name in ['Sword','Scabbard']:build(name)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_equipped.blend'))
# Diagnose the transient shoulder/head contact without changing the selected master.
from g6_head_clearance import Clearance
C=Clearance(body);a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
bpy.context.scene.frame_set(81);b=rig.pose.bones['B_Neck'];original=b.rotation_quaternion.copy()
print('HEAD baseline',C.measure(),C.last_hit)
for axis in ['X','Y','Z']:
 for deg in [-9,-6,-3,3,6,9]:
  b.rotation_quaternion=original@Quaternion(Vector({'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis]),math.radians(deg));bpy.context.view_layer.update()
  print('HEAD probe',axis,deg,C.measure(),C.last_hit)
b.rotation_quaternion=original
