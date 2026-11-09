"""Native-derived bow: curved tapered limbs, wrapped grip, horn nocks and a bevelled arrowhead."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
verts=[];faces=[];classes=[];parts=[]
def face(v,cl,part):faces.append(v);classes.append(cl);parts.append(part)
def rings_mesh(rings,cl,part):
 ids=[]
 for ring in rings:
  ids.append(len(verts));verts.extend(ring)
 n=len(rings[0])
 for a,b in zip(ids,ids[1:]):
  for j in range(n):face((a+j,b+j,b+(j+1)%n,a+(j+1)%n),cl,part)
 face(tuple(ids[0]+j for j in reversed(range(n))),cl,part);face(tuple(ids[-1]+j for j in range(n)),cl,part)
def tube(stations,cl,part,n=10):
 rings_mesh([[(x+rx*math.cos(2*math.pi*j/n),y+ry*math.sin(2*math.pi*j/n),z)for j in range(n)]for x,y,z,rx,ry in stations],cl,part)
def bow_y(z):return .215*(abs(z)/.55)**1.65
# Broad limb faces and bevelled elliptical edges spend polygons on the curved silhouette.
st=[]
for i in range(65):
 z=-.55+1.10*i/64;t=abs(z)/.55;st.append((0,bow_y(z),z,.017*(1-.65*t),.010*(1-.45*t)))
tube(st,10,0,8)
tube([(0,bow_y(z),z,.020,.014)for z in [-.095,-.087,.087,.095]],8,1,12)
# Raised overlapping leather wrap, tapered at both ends.
rings=[]
for i in range(97):
 a=2*math.pi*8*i/96;z=-.086+.172*i/96
 rings.append([(r*math.cos(a),bow_y(z)+r*.76*math.sin(a),z+dz)for r,dz in [(.0195,-.006),(.021,-.0045),(.021,.0045),(.0195,.006)]])
rings_mesh(rings,8,2)
for sign in [-1,1]:
 tube([(0,bow_y(sign*z),sign*z,rx,ry)for z,rx,ry in [(.528,.0078,.0068),(.54,.0088,.0078),(.548,.007,.006),(.555,.0065,.0055),(.565,.001,.001)]],4,3,10)
 # A real groove around the horn nock.
 for zz in [.535,.545]:tube([(0,bow_y(sign*z),sign*z,.009,.0078)for z in [zz-.0015,zz+.0015]],8,4,10)
# Arrow alongside the bow for the texture upload; part IDs keep it separable at assembly.
x=.22;y=.03
tube([(x,y,z,.0033,.0033)for z in [-.32,.29]],10,5,8)
# Broadhead: diamond cross section, socket and two cutting bevels.
rings_mesh([[(x+dx,y+dy,z)for dx,dy in [(-w,0),(0,d),(w,0),(0,-d)]]for z,w,d in [(.282,.004,.003),(.301,.018,.004),(.346,.0005,.0004)]],9,6)
tube([(x,y,z,.0055,.0055)for z in [.271,.288]],9,6,8)
for a in [0,2*math.pi/3,4*math.pi/3]:
 pts=[(-.31,.003),(-.27,.022),(-.20,.022),(-.18,.003)];k=len(verts)
 for depth in [-.00065,.00065]:
  for z,r in pts:verts.append((x+r*math.cos(a)-depth*math.sin(a),y+r*math.sin(a)+depth*math.cos(a),z))
 face((k,k+1,k+2,k+3),11,7);face((k+7,k+6,k+5,k+4),11,7)
 for j in range(4):face((k+j,k+(j+1)%4,k+4+(j+1)%4,k+4+j),11,7)
for z in [-.315,-.182,.266]:tube([(x,y,t,.0045,.0045)for t in [z-.004,z+.004]],8,8,8)
me=bpy.data.meshes.new('BowArrow');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
ob=bpy.data.objects.new('BowArrow',me);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
for name,values in [('material_class',classes),('prop_part',parts)]:me.attributes.new(name,'INT','FACE').data.foreach_set('value',values)
for poly in me.polygons:poly.use_smooth=parts[poly.index] not in [6,7]
mat=bpy.data.materials.new('BowWoodLeatherHorn');mat.diffuse_color=(.15,.08,.035,1);mat.use_nodes=True;me.materials.append(mat)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(75),island_margin=.012,area_weight=0);bpy.ops.object.mode_set(mode='OBJECT')
triangles=sum(len(f)-2 for f in faces);assert 1000<=triangles<=3000,triangles
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bow_clay.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/bow_upload.glb'),export_format='GLB',use_selection=True,export_animations=False,export_attributes=False)
(P/'work/bow_geometry.json').write_text(json.dumps({'triangles':triangles,'grip_radius_m':.021,'bow_tip_local':[[0,bow_y(-.55),-.55],[0,bow_y(.55),.55]],'arrow_offset':[x,y,0],'source':'references_hd/bow_design.png'},indent=2))
scene=bpy.context.scene;common.workbench_clay(scene)
for name,d in [('side',Vector((1,0,0))),('three_quarter',Vector((1,-.7,.12)))]:
 centre=Vector((.1,.12,0));d.normalize();cam=common.ortho_camera('PropCamera',centre+d*3,(0,0,0),1.28);cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.resolution_x=700;scene.render.resolution_y=1000;scene.render.filepath=str(P/f'review/bow_clay_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
print('BOW',triangles,'triangles')
