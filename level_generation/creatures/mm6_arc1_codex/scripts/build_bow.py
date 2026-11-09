"""Canonical bow: Z limb axis, Y string side, X thickness; modelled from the retained HD design."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
verts=[];faces=[];classes=[];parts=[]
def add(v):
 k=len(verts);verts.extend(v);return k
def face(v,c,p):faces.append(v);classes.append(c);parts.append(p)
def tube(stations,n,cl,part):
 rings=[]
 for i,(x,y,z,rx,ry) in enumerate(stations):
  tangent=Vector(stations[min(i+1,len(stations)-1)][:3])-Vector(stations[max(i-1,0)][:3]);tangent.normalize()
  u=Vector((1,0,0));v=tangent.cross(u).normalized()
  rings.append(add([tuple(Vector((x,y,z))+u*(rx*math.cos(j*2*math.pi/n))+v*(ry*math.sin(j*2*math.pi/n)))for j in range(n)]))
 for k,l in zip(rings,rings[1:]):
  for j in range(n):face((k+j,l+j,l+(j+1)%n,k+(j+1)%n),cl,part)
 face(tuple(rings[0]+j for j in reversed(range(n))),cl,part);face(tuple(rings[-1]+j for j in range(n)),cl,part)
def catmull(pts,count):
 out=[]
 for i in range(len(pts)-1):
  a,b,c,d=[Vector(pts[min(max(j,0),len(pts)-1)])for j in (i-1,i,i+1,i+2)]
  for k in range(count):
   t=k/count;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 out.append(Vector(pts[-1]));return out
# Laminated recurved limbs; thick root, tapering tip, swept hook at the string nock.
for sign in (-1,1):
 path=catmull([(0,.055),(-.008,.13),(.005,.23),(.058,.35),(.13,.46),(.18,.52),(.192,.563),(.164,.587),(.133,.582),(.117,.562)],3)
 stations=[]
 for i,(y,z) in enumerate(path):
  t=i/(len(path)-1);rx=.011*(1-.66*t);ry=.017*(1-.62*t)
  if t>.8:rx*=1.2;ry*=1.3
  stations.append((0,y,sign*z,rx,ry))
 tube(stations,12,1,0)
# 22 mm maximum handle diameter, below the solved skin-clearance envelope.
tube([(0,0,z,.0093,.0093)for z in [-.065,-.06,.06,.065]],12,8,1)
rings=[]
for j in range(73):
 t=j/72;theta=t*6*2*math.pi;z=-.06+t*.12
 rings.append(add([(r*math.cos(theta),r*math.sin(theta),z+dz)for r,dz in [(.0093,-.010),(.011,-.008),(.011,.008),(.0093,.010)]]))
for k,l in zip(rings,rings[1:]):
 for j in range(4):face((k+j,l+j,l+(j+1)%4,k+(j+1)%4),8,1)
face(tuple(rings[0]+j for j in reversed(range(4))),8,1);face(tuple(rings[-1]+j for j in range(4)),8,1)
# Binding at both nocks, actual small raised winding rings.
for sign in (-1,1):
 for k in range(3):
  z=sign*(.536+k*.004);tube([(0,.187,z-.0013,.010,.010),(0,.187,z,.011,.011),(0,.187,z+.0013,.010,.010)],10,8,2)
# Arrow canonical Z, later mounted along its own bone; a shaped dull steel bodkin and three feather vanes.
tube([(.10,0,z,.003,.003)for z in [-.32,.29]],8,1,3)
tube([(.10,0,z,r,r)for z,r in [(.287,.004),(.298,.008),(.322,.004),(.341,.0004)]],4,9,4)
for angle in [0,2*math.pi/3,4*math.pi/3]:
 points=[]
 for z,r in [(-.292,.003),(-.29,.016),(-.262,.022),(-.21,.004)]:
  points.append((.1+math.cos(angle)*r,math.sin(angle)*r,z))
 k=add(points+[(x+math.sin(angle)*.0008,y-math.cos(angle)*.0008,z)for x,y,z in points]);face((k,k+1,k+2,k+3),8,5);face((k+7,k+6,k+5,k+4),8,5)
 for j in range(4):face((k+j,k+(j+1)%4,k+4+(j+1)%4,k+4+j),8,5)
me=bpy.data.meshes.new('BowAndArrow');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
ob=bpy.data.objects.new('BowAsset',me);bpy.context.collection.objects.link(ob);ob.select_set(True);bpy.context.view_layer.objects.active=ob
for name,v in [('material_class',classes),('bow_part',parts)]:me.attributes.new(name,'INT','FACE').data.foreach_set('value',v)
mat=bpy.data.materials.new('GoldenWoodAndLeather');mat.diffuse_color=(.38,.24,.09,1);mat.use_nodes=True;me.materials.append(mat)
for f in me.polygons:f.use_smooth=parts[f.index]!=4
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.007);bpy.ops.object.mode_set(mode='OBJECT')
tris=sum(len(f)-2 for f in faces);assert 1000<=tris<=3000,tris
(P/'texturing').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bow_clay.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/bow_upload.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_attributes=False)
(P/'work/bow_geometry.json').write_text(json.dumps({'triangles':tris,'grip_radius_m':.011,'nock':[0,.187,.545],'design':'references_hd/bow_design.png'},indent=2))
scene=bpy.context.scene;common.workbench_clay(scene)
for name,direction in [('side',Vector((1,0,0))),('three_quarter',Vector((1,-.65,.05)))]:
 d=direction.normalized();centre=Vector((0,.07,0));cam=common.ortho_camera('PropCamera',centre+d*3,(0,0,0),1.4);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.resolution_x=700;scene.render.resolution_y=1000;scene.render.filepath=str(P/f'review/bow_clay_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
print('BOW',tris,'triangles')
