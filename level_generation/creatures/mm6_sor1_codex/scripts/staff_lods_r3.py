"""Original lathed shaft, ferrules, leather grip, four curved crown prongs and faceted jewel."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
def rebuild_staff(staff,scene,level):
 data=json.loads(scene['staff']);G=json.loads((Path(__file__).resolve().parents[1]/'work/grip_pose.json').read_text());rig=bpy.data.objects['Rig'];H=rig.matrix_world@rig.data.bones['B_R_Hand'].matrix_local;C=H@Vector(G['handle_centre_hand_local']);axis=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
 Q=Vector((0,0,1)).rotation_difference(axis);verts=[];faces=[];uvs=[];smooth=[]
 def uv(region,u,v):return ((region+.02+.96*u)/4,.015+.97*v)
 def surface(rings,region,sides=20,flat=False):
  start=len(verts)
  for z,r in rings:
   for k in range(sides):
    a=2*math.pi*k/sides;verts.append((r*math.cos(a),r*math.sin(a),z))
  for j in range(len(rings)-1):
   for k in range(sides):
    faces.append((start+j*sides+k,start+j*sides+(k+1)%sides,start+(j+1)*sides+(k+1)%sides,start+(j+1)*sides+k))
    uvs.append([uv(region,k/sides,j/(len(rings)-1)),uv(region,(k+1)/sides,j/(len(rings)-1)),uv(region,(k+1)/sides,(j+1)/(len(rings)-1)),uv(region,k/sides,(j+1)/(len(rings)-1))]);smooth.append(not flat)
  for j in (0,len(rings)-1):
   face=tuple(start+j*sides+k for k in range(sides))
   faces.append(tuple(reversed(face)) if j==0 else face);uvs.append([uv(region,.5+.45*math.cos(2*math.pi*k/sides),.5+.45*math.sin(2*math.pi*k/sides)) for k in (list(reversed(range(sides))) if j==0 else range(sides))]);smooth.append(False)
 if level==1:
  surface([(0,.0105),(.92,.0105),(.94,.0092),(1.145,.0092),(1.16,.0105),(1.61,.0105)],0,sides=8)
  surface([(.94,.0105),(1.0425,.0105),(1.145,.0105)],2,sides=8)
  surface([(0,.010),(.012,.014),(.026,.013),(.036,.015),(.040,.012)],1,sides=8)
  for z in [.90,1.15,1.45]:surface([(z,.011),(z+.009,.013),(z+.018,.011)],1,sides=8)
  surface([(1.57,.011),(1.58,.018),(1.593,.014),(1.61,.017),(1.647,.028),(1.66,.024)],1,sides=8)
 elif level==2:
  surface([(0,.0105),(.94,.0105),(1.61,.0105)],0,sides=8)
  surface([(0,.010),(.025,.015),(.040,.012)],1,sides=8)
  for z in [.90,1.15,1.45]:surface([(z,.011),(z+.009,.013),(z+.018,.011)],1,sides=4)
  surface([(1.57,.011),(1.647,.028),(1.66,.024)],1,sides=6)
 else:
  surface([(0,.0105),(1.61,.0105)],0,sides=8)
  surface([(1.57,.011),(1.647,.028),(1.66,.024)],1,sides=6)
 # Curved narrow cage fingers preserve the native small crown silhouette.
 for finger in range(4):
  angle=finger*math.pi/2;rad=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-math.sin(angle),math.cos(angle),0))
  profile=[(1.645,.022,.008),(1.66,.031,.008),(1.68,.039,.007),(1.702,.041,.006),(1.726,.035,.005),(1.749,.025,.003),(1.76,.020,.0008)]
  profile=[profile[i] for i in ([0,1,2,3,4,5,6] if level==1 else [0,2,3,4,6] if level==2 else [0,3,6])]
  start=len(verts);n=4 if level==1 else 3
  for z,r,width in profile:
   for k in range(n):
    a=2*math.pi*k/n;pos=rad*r+Vector((0,0,z))+side*(width*math.cos(a))+rad*(width*.62*math.sin(a));verts.append(tuple(pos))
  for j in range(len(profile)-1):
   for k in range(n):
    faces.append((start+j*n+k,start+j*n+(k+1)%n,start+(j+1)*n+(k+1)%n,start+(j+1)*n+k));uvs.append([uv(1,k/n,j/(len(profile)-1)),uv(1,(k+1)/n,j/(len(profile)-1)),uv(1,(k+1)/n,(j+1)/(len(profile)-1)),uv(1,k/n,(j+1)/(len(profile)-1))]);smooth.append(True)
  for j in (0,len(profile)-1):
   f=tuple(start+j*n+k for k in range(n));faces.append(tuple(reversed(f)) if j==0 else f);uvs.append([uv(1,.5,.5)]*n);smooth.append(False)
 surface([(1.664,.009),(1.679,.026),(1.706,.034),(1.731,.026),(1.751,.008)] if level<3 else [(1.664,.009),(1.706,.034),(1.751,.008)],3,sides=8 if level==1 else 6,flat=True)
 mesh=bpy.data.meshes.new('StaffDetailed')
 mesh.from_pydata([C+Q@(Vector(v)-Vector((0,0,data['grip_from_foot']))) for v in verts],[],faces);mesh.update()
 layer=mesh.uv_layers.new(name='UVMap')
 for poly,coords,sm in zip(mesh.polygons,uvs,smooth):
  poly.use_smooth=sm
  for li,co in zip(poly.loop_indices,coords):layer.data[li].uv=co
 import bmesh
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
 old=staff.data;staff.data=mesh
 if old.users==0:bpy.data.meshes.remove(old)
 (staff.vertex_groups.get('B_Staff') or staff.vertex_groups.new(name='B_Staff')).add(list(range(len(mesh.vertices))),1,'REPLACE')
 assert all(len(poly.vertices)==len(coords) for poly,coords in zip(mesh.polygons,uvs))
 report={'triangles':sum(len(f)-2 for f in faces),'height_m':1.76,'grip_radius_mm':10.5,'crown_width_mm':94,'source':'references_hd/staff_design.png','features':['8-sided wooden shaft','rebaked grip wrap and engraving','simplified ferrules and socket','four curved cage fingers','faceted dark-red jewel']}
 (Path(__file__).resolve().parents[1]/f'work/staff_lod{level}_geometry.json').write_text(json.dumps(report,indent=2))
 print('STAFF',report)
