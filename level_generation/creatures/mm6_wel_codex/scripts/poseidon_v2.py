"""Low polygon Poseidon weapon with beveled steel blades and a wrapped shaft atlas."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/surface_v2.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
old=bpy.data.objects['Trident'];bpy.data.objects.remove(old,do_unlink=True)
G=json.loads((P/'work/grip_pose.json').read_text());H=rig.data.bones['B_R_Hand'].matrix_local
origin=H@Vector(G['handle_centre_hand_local']);axis=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();x=H.to_3x3()@Vector((0,1,0));x=(x-axis*x.dot(axis)).normalized();z=x.cross(axis);R=Matrix((x,axis,z)).transposed()
verts=[];faces=[];uvs=[];smooth=[];factor=2.47/1735
def yfrom(px):return 1.62-(px-5)*factor
def face(ids,coords,soft=False):faces.append(ids);uvs.append(coords);smooth.append(soft)
def uvblade(x,y):return ((x-230)/426*.625,1-y/540)
def blade(outline):
 n=len(outline);offset=len(verts);cx=sum(p[0] for p in outline)/n;cy=sum(p[1] for p in outline)/n
 for depth,shrink in [(-.015,.96),(-.002,1),(.002,1),(.015,.96)]:
  for px,py in outline:
   qx=cx+(px-cx)*shrink;qy=cy+(py-cy)*shrink;verts.append(((qx-443)*factor,yfrom(qy),depth))
 for k in range(3):
  for j in range(n):
   ids=[offset+k*n+j,offset+k*n+(j+1)%n,offset+(k+1)*n+(j+1)%n,offset+(k+1)*n+j]
   face(ids,[uvblade(verts[v][0]/factor+443,5+(1.62-verts[v][1])/factor) for v in ids])
 for layer,reverse in [(0,True),(3,False)]:
  ids=[offset+layer*n+j for j in range(n)];ids=ids[::-1] if reverse else ids
  face(ids,[uvblade(verts[v][0]/factor+443,5+(1.62-verts[v][1])/factor) for v in ids])
centre=[(443,5),(461,188),(474,293),(498,365),(469,356),(458,351),(460,453),(468,498),(453,516),(432,516),(418,498),(426,450),(428,351),(415,358),(390,365),(409,288),(425,176)]
branch=[(432,504),(416,494),(397,467),(356,448),(348,436),(319,413),(287,398),(329,401),(340,395),(339,383),(244,185),(365,360),(392,393),(421,431)]
blade(branch);blade([(886-x,y) for x,y in branch][::-1]);blade(centre)
# The grip remains 20 mm in diameter; thicker collars are outside the palm tunnel.
rings=[(515,.021),(526,.026),(538,.021),(562,.015),(570,.021),(582,.021),(592,.014),(608,.019),(620,.019),(626,.025),(647,.025),(655,.013),(697,.013),(705,.018),(716,.018),(724,.024),(744,.024),(752,.012),(904,.012),(915,.021),(925,.018),(935,.022),(949,.022),(958,.017),(966,.021),(978,.021),(988,.011),(1119,.011),(1126,.022),(1144,.022),(1155,.010),(1554,.010),(1568,.022),(1580,.022),(1595,.018),(1602,.027),(1680,.027),(1701,.012),(1710,.017),(1740,0)]
# Move the lower silver collar away from the grip center at source y=1143.
rings=[(y,.011+(r-.011)*.50 if r>.011 else r) for y,r in rings]
rings=[(y+40 if 1119<=y<=1155 else y,r) for y,r in rings];rings.sort()
ref_width=[(515,27),(540,23),(562,22),(590,19),(620,31),(647,31),(655,20),(697,21),(716,25),(724,30),(744,30),(752,22),(904,22),(915,30),(925,27),(949,31),(978,28),(988,22),(1119,23),(1126,31),(1144,31),(1155,23),(1554,24),(1568,28),(1580,26),(1602,36),(1680,36),(1701,13),(1710,22),(1740,1)]
def width(y):
 for (a,x),(b,z) in zip(ref_width,ref_width[1:]):
  if y<=b:return x+(z-x)*max(0,(y-a)/(b-a))
 return 1
offset=len(verts);sides=8
for py,rad in rings:
 for k in range(sides):
  a=2*math.pi*k/sides;verts.append((rad*math.cos(a),yfrom(py),rad*math.sin(a)))
for j in range(len(rings)-1):
 for k in range(sides):
  ids=[offset+j*sides+k,offset+j*sides+(k+1)%sides,offset+(j+1)*sides+(k+1)%sides,offset+(j+1)*sides+k];coords=[]
  for v in ids:
   ring=(v-offset)//sides;corner=(v-offset)%sides;py=rings[ring][0];source_y=py-40 if 1159<=py<=1195 else py;px=443+width(source_y)*.90*math.cos(2*math.pi*corner/sides)
   coords.append((.65+(px-403)/80*.35,1-(source_y-515)/1230))
  face(ids,coords,True)
me=bpy.data.meshes.new('Poseidon');me.from_pydata([origin+R@Vector(v) for v in verts],[],faces);me.update();uv=me.uv_layers.new(name='UVMap')
for f,coords,soft in zip(me.polygons,uvs,smooth):
 f.use_smooth=soft
 for i,t in zip(f.loop_indices,coords):uv.data[i].uv=t
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
ob=bpy.data.objects.new('Trident',me);bpy.context.collection.objects.link(ob);g=ob.vertex_groups.new(name='Trident');g.add(list(range(len(me.vertices))),1,'REPLACE');ob.parent=rig;mod=ob.modifiers.new('Rigid attachment','ARMATURE');mod.object=rig
mat=bpy.data.materials.new('Poseidon');mat.use_nodes=True;nt=mat.node_tree;tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'textures/wel_trident_basecolor.png'));nt.links.new(tex.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);me.materials.append(mat)
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
(P/'review/feedback_v2/poseidon.json').write_text(json.dumps({'triangles':len(me.polygons),'shaft_grip_diameter_m':.020,'texture':'textures/wel_trident_basecolor.png','reference':'references_feedback_v2/poseidon_front.png','source_item':'MM6 item 2037, 6trident5 Poseidon'},indent=2))
assert len(me.polygons)<1500
