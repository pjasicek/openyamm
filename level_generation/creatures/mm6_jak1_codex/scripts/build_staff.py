"""Native hooked staff: modelled steel bevel, ferrules, wrapped grips, 1-3k triangles."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);verts=[];faces=[];classes=[];parts=[]
def add(points):
 k=len(verts);verts.extend(points);return k
def face(v,cl,part):faces.append(v);classes.append(cl);parts.append(part)
def tube(stations,cl,part,n=10):
 rings=[add([(r*math.cos(2*math.pi*j/n),r*math.sin(2*math.pi*j/n),z)for j in range(n)])for z,r in stations]
 for k,l in zip(rings,rings[1:]):
  for j in range(n):face((k+j,k+(j+1)%n,l+(j+1)%n,l+j),cl,part)
 face(tuple(rings[0]+j for j in reversed(range(n))),cl,part);face(tuple(rings[-1]+j for j in range(n)),cl,part)
tube([(0,.010),(.015,.011),(.3,.011),(.9,.011),(1.42,.011),(1.48,.009)],10,0)
# The hook has an octagonal bevelled cross section and a narrowing free tip.
path=[]
for j in range(9):path.append((0,1.48+j/8*.29))
for j in range(1,19):
 a=math.pi-j/18*math.pi;path.append((.055+.055*math.cos(a),1.77+.11*math.sin(a)))
for j in range(1,13):
 t=j/12;path.append((.11-.025*t+.015*t*t,1.77-.245*t))
rings=[]
for i,(x,z) in enumerate(path):
 d=Vector((path[min(i+1,len(path)-1)][0]-path[max(0,i-1)][0],0,path[min(i+1,len(path)-1)][1]-path[max(0,i-1)][1])).normalized();n=Vector((d.z,0,-d.x));w=.012*(1 if i<len(path)-8 else max(.12,(len(path)-i)/8));thick=.005
 profile=[(-w,0),(-w*.65,-thick),(w*.65,-thick),(w,0),(w*.65,thick),(-w*.65,thick)]
 rings.append(add([tuple(Vector((x,0,z))+n*e+Vector((0,f,0)))for e,f in profile]))
for k,l in zip(rings,rings[1:]):
 for j in range(6):face((k+j,k+(j+1)%6,l+(j+1)%6,l+j),9,1)
face(tuple(rings[0]+j for j in reversed(range(6))),9,1);face(tuple(rings[-1]+j for j in range(6)),9,1)
# Gold sockets with stepped rims, native turquoise rings, and two fine leather wraps.
for lo,hi in [(.015,.055),(.26,.34),(.405,.48),(1.02,1.06),(1.35,1.47)]:
 tube([(lo,.012),(lo+.003,.017),(lo+.008,.018),(lo+.013,.016),(hi-.009,.016),(hi-.004,.018),(hi,.012)],9,2)
for z in [.35,.376,1.25,1.285]:
 tube([(z,.012),(z+.003,.015),(z+.017,.015),(z+.02,.012)],11,3)
for z in [.34,.373,.398,1.238,1.273,1.309]:tube([(z,.012),(z+.003,.016),(z+.008,.016),(z+.011,.012)],9,2)
for lo,hi,turns in [(.06,.255,7),(1.065,1.235,6)]:
 tube([(lo,.011),(hi,.011)],8,4);rr=[]
 for j in range(turns*8+1):
  a=j/(turns*8)*turns*2*math.pi;z=lo+(hi-lo)*j/(turns*8)
  rr.append(add([(r*math.cos(a),r*math.sin(a),z+dz)for r,dz in [(.0108,-.012),(.0126,-.010),(.0126,.010),(.0108,.012)]]))
 for k,l in zip(rr,rr[1:]):
  for j in range(4):face((k+j,k+(j+1)%4,l+(j+1)%4,l+j),8,4)
me=bpy.data.meshes.new('HookedStaff');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('Staff',me);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
for name,vals in [('material_class',classes),('staff_part',parts)]:a=me.attributes.new(name,'INT','FACE');a.data.foreach_set('value',vals)
mat=bpy.data.materials.new('StaffMetalWoodLeather');mat.use_nodes=True;me.materials.append(mat);mat.diffuse_color=(.22,.22,.22,1)
for f in me.polygons:f.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(58),island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
tris=sum(len(f)-2 for f in faces);assert 1000<=tris<=3000,tris
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/staff_clay.blend'));bpy.ops.export_scene.gltf(filepath=str(P/'work/staff_upload.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_attributes=False)
(P/'work/staff_geometry.json').write_text(json.dumps({'triangles':tris,'height_m':1.88,'shaft_radius_m':.011,'grip_radius_m':.0126,'design':'references_hd/staff_design.png'},indent=2))
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/staff_clay'),.94,2.03,views=('front','three_quarter'),resolution=(500,1100),target=(.035,0))
print('Staff triangles',tris,flush=True)
