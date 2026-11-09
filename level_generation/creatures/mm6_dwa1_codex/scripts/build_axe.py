"""Native crescent axe, from references_hd/axe_design.png; detailed silhouette and wrapped grip."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);V=[];F=[];C=[];parts=[]
def add(points):
 k=len(V);V.extend(points);return k
def pt(a,s,f):return(a,f,-s)
def face(ids,cl,part):F.append(ids);C.append(cl);parts.append(part)
def tube(stations,cl,part,n=20):
 rings=[add([pt(a,r*math.cos(2*math.pi*j/n),r*math.sin(2*math.pi*j/n))for j in range(n)])for a,r in stations]
 for k,l in zip(rings,rings[1:]):
  for j in range(n):face((k+j,l+j,l+(j+1)%n,k+(j+1)%n),cl,part)
 face(tuple(rings[0]+j for j in reversed(range(n))),cl,part);face(tuple(rings[-1]+j for j in range(n)),cl,part)
# Five-piece bevelled section gives the broad blade a real ground edge.
def plate(outline,cl,part,thick=.006):
 center=sum((Vector(q)for q in outline),Vector((0,0)))/len(outline);loops=[]
 for scale,depth in [(1,0),(.94,-thick),(.94,thick)]:
  loops.append(add([pt(*(center+(Vector(q)-center)*scale),depth)for q in outline]))
 n=len(outline)
 for a,b in [(0,1),(2,0)]:
  for j in range(n):face((loops[a]+j,loops[b]+j,loops[b]+(j+1)%n,loops[a]+(j+1)%n),cl,part)
 face(tuple(loops[1]+j for j in reversed(range(n))),cl,part);face(tuple(loops[2]+j for j in range(n)),cl,part)
# Long convex cutting edge from the rear horn to the front horn, concave inner opening under the haft.
outer=[(.405+.17*math.cos(t),.025+.15*math.sin(t))for t in [math.pi-j*math.pi/28 for j in range(29)]]
inner=[(.55,.040),(.519,.062),(.483,.074),(.465,.065),(.458,.045),(.458,-.012),(.359,-.012),(.359,.050),(.346,.069),(.321,.075),(.284,.064),(.258,.049)]
plate(outer+inner,9,0,.006)
# Angular back spike is the native counterweight, not a second broad axe bit.
plate([(.325,-.025),(.373,-.056),(.414,-.175),(.426,-.079),(.444,-.045),(.476,-.025)],9,1,.007)
tube([(-.105,.015),(-.095,.016),(.05,.016),(.20,.017),(.35,.018),(.46,.018),(.475,.017)],10,2,20)
tube([(.349,.025),(.357,.030),(.453,.030),(.461,.025)],9,3,20)
for a in [-.106,.066,.344,.466]:tube([(a-.005,.017),(a-.003,.021),(a+.003,.021),(a+.005,.017)],9,4,20)
tube([(-.126,.005),(-.122,.016),(-.114,.021),(-.106,.019)],9,5,20)
# Actual leather ribbon, bevelled across width, entirely inside the calibrated handle envelope.
rings=[];steps=8*16
for j in range(steps+1):
 th=j/steps*8*2*math.pi;a=-.098+j/steps*.16
 rings.append(add([pt(a+da,r*math.cos(th),r*math.sin(th))for da,r in [(-.011,.016),(-.009,.018),(.009,.018),(.011,.016)]]))
for k,l in zip(rings,rings[1:]):
 for j in range(4):face((k+j,l+j,l+(j+1)%4,k+(j+1)%4),8,6)
face(tuple(rings[0]+j for j in reversed(range(4))),8,6);face(tuple(rings[-1]+j for j in range(4)),8,6)
# Visible socket pins on both broad faces.
for side in [-1,1]:
 rings=[]
 for r,f in [(.008,.027),(.009,.031),(.007,.034)]:rings.append(add([pt(.403+r*math.cos(j*math.tau/12),r*math.sin(j*math.tau/12),side*f)for j in range(12)]))
 for k,l in zip(rings,rings[1:]):
  for j in range(12):face((k+j,l+j,l+(j+1)%12,k+(j+1)%12),9,7)
 face(tuple(rings[-1]+j for j in range(12)),9,7)
me=bpy.data.meshes.new('DwarfAxe');me.from_pydata(V,[],F);me.update()
for n,data in [('material_class',C),('axe_part',parts)]:a=me.attributes.new(n,'INT','FACE');a.data.foreach_set('value',data)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
o=bpy.data.objects.new('Axe',me);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True)
m=bpy.data.materials.new('AxeMetalWoodLeather');m.use_nodes=True;m.diffuse_color=(.25,.25,.27,1);me.materials.append(m)
for f in me.polygons:f.use_smooth=me.attributes['axe_part'].data[f.index].value>=2
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
tris=len(me.polygons);assert 1000<=tris<=3500,tris
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/axe_clay.blend'));bpy.ops.export_scene.gltf(filepath=str(P/'work/axe_upload.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_attributes=False)
(P/'work/axe_geometry.json').write_text(json.dumps({'triangles':tris,'grip_radius_m':.018,'haft_axis':'X','cutting_edge_direction':'-Z','source':'references_hd/axe_design.png'},indent=2))
scene=bpy.context.scene;common.workbench_clay(scene);scene.render.resolution_x=1100;scene.render.resolution_y=650
for name,d in [('side',Vector((0,-1,0))),('three_quarter',Vector((-.3,-1,.6)))]:
 center=Vector((.23,0,0));d.normalize();cam=common.ortho_camera('Camera',center+d*3,(0,0,0),.78);cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.filepath=str(P/f'review/axe_clay_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
print('AXE',tris)
