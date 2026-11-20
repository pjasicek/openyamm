"""Hand-built weapon from the generated standalone design, in canonical (axis, flat, -edge) coordinates."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);verts=[];faces=[];classes=[];parts=[]
def add(points):
 k=len(verts);verts.extend(points);return k
def p(a,s,f):return (a,f,-s)
def face(v,cl,part):faces.append(v);classes.append(cl);parts.append(part)
def tube(stations,cl,part,n=12):
 rings=[add([p(a,r*math.cos(2*math.pi*j/n),r*math.sin(2*math.pi*j/n))for j in range(n)])for a,r in stations]
 for k,l in zip(rings,rings[1:]):
  for j in range(n):face((k+j,l+j,l+(j+1)%n,k+(j+1)%n),cl,part)
 face(tuple(rings[0]+j for j in reversed(range(n))),cl,part);face(tuple(rings[-1]+j for j in range(n)),cl,part)
# Convex cutting edge, a recessed fuller on each broad face, three pointed root teeth.
ts=sorted(set([0,.022,.035,.05,.06,.075,.09,.1,.115,.13,.17,.22,.28,.36,.44,.52,.60,.68,.76,.82,.88,.93,.97]))
rings=[];widths=[]
for t in ts:
 a=.135+.715*t;curve=-.18*t*t;tooth=max(max(0,1-abs(t-c)/.015) for c in [.035,.075,.115]);back=-.04-.027*tooth
 taper=1 if t<=.76 else max(.025,(1-t)/.24)
 edge=.055*taper;back*=taper;depth=.005*(.8+.2*taper)
 # Cross section from cutting edge to spine, then the reverse side: fuller is genuine concavity.
 smooth_back=-.04*taper;span=edge-smooth_back;recess=min(1,max(0,(t-.17)/.10))*min(1,max(0,(.97-t)/.12))
 sections=[(edge,0),(edge-.18*span,depth*.9),(smooth_back+.51*span,depth),(smooth_back+.44*span,depth*(1-.48*recess)),(smooth_back+.23*span,depth*(1-.48*recess)),(smooth_back+.16*span,depth),(smooth_back+.06*span,depth*.85),(back,.0012*taper)]
 loop=sections+[(s,-f)for s,f in reversed(sections[1:])];rings.append(add([p(a,curve+s,f)for s,f in loop]));widths.append(len(loop))
for k,l,n in zip(rings,rings[1:],widths):
 for j in range(n):face((k+j,l+j,l+(j+1)%n,k+(j+1)%n),9,0)
tip=add([p(.85,-.18,0)]);n=widths[-1]
for j in range(n):face((rings[-1]+j,tip,rings[-1]+(j+1)%n),9,0)
face(tuple(rings[0]+j for j in reversed(range(widths[0]))),9,0)
# The grip's outer radius never exceeds the already-solved 14 mm clearance envelope.
tube([(-.191,.0102),(-.18,.0104),(-.04,.0105),(.094,.0104),(.106,.0102)],8,1)
turns=9;steps=turns*12;rings=[]
for j in range(steps+1):
 theta=j/steps*turns*2*math.pi;a=-.181+j/steps*.277
 rings.append(add([p(a+da,r*math.cos(theta),r*math.sin(theta))for da,r in [(-.014,.0104),(-.012,.0118),(.012,.0118),(.014,.0104)]]))
for k,l in zip(rings,rings[1:]):
 for j in range(4):face((k+j,l+j,l+(j+1)%4,k+(j+1)%4),8,2)
face(tuple(rings[0]+j for j in reversed(range(4))),8,2);face(tuple(rings[-1]+j for j in range(4)),8,2)
for a in [-.192,.109]:tube([(a-.005,.011),(a-.003,.0155),(a+.003,.0155),(a+.005,.011)],9,3,12)
# Faceted steel pommel with stepped neck and a raised end boss.
tube([(-.233,.006),(-.231,.013),(-.223,.020),(-.21,.023),(-.198,.019),(-.191,.011)],9,4,12)
tube([(-.236,.003),(-.235,.008),(-.232,.010)],9,4,12)
# Compact curved guard: tapered horns protect the hand without an oversized crossguard.
outline=[(.114,-.015),(.106,-.029),(.106,-.040),(.111,-.048),(.120,-.052),(.115,-.043),(.116,-.034),(.129,-.020),(.134,0),(.130,.020),(.119,.034),(.119,.041),(.125,.047),(.115,.046),(.106,.040),(.103,.031),(.109,.016)]
centre=Vector((.120,0));layers=[]
for scale,f in [(.83,-.006),(1,-.003),(1,.003),(.83,.006)]:
 layers.append(add([p(*(centre+(Vector(q)-centre)*scale),f)for q in outline]))
n=len(outline)
for k,l in zip(layers,layers[1:]):
 for j in range(n):face((k+j,l+j,l+(j+1)%n,k+(j+1)%n),9,5)
face(tuple(layers[0]+j for j in reversed(range(n))),9,5);face(tuple(layers[-1]+j for j in range(n)),9,5)
# Two small rivet bosses; texture supplies the recessed engraving and fine wear.
for sign in [-1,1]:
 rings=[]
 for r,f in [(.0038,.0058),(.0043,.007),(.0034,.008)]:
  rings.append(add([p(.119+r*math.cos(2*math.pi*j/10),r*math.sin(2*math.pi*j/10),sign*f)for j in range(10)]))
 for k,l in zip(rings,rings[1:]):
  for j in range(10):face((k+j,l+j,l+(j+1)%10,k+(j+1)%10),9,6)
 face(tuple(rings[-1]+j for j in range(10)),9,6)
me=bpy.data.meshes.new('KnightSwordRound1');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
ob=bpy.data.objects.new('Sword',me);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
for name,values in [('material_class',classes),('sword_part',parts)]:
 attr=me.attributes.new(name,'INT','FACE');attr.data.foreach_set('value',values)
mat=bpy.data.materials.new('SwordMetalAndLeather');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.20,.205,.22,1);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.6;me.materials.append(mat)
# Blade face normals remain split across the real bevel and recessed fuller.
for poly,part in zip(me.polygons,parts):poly.use_smooth=part in [0,1,2,3]
# Keep bevel/fuller's cross-section edges crisp, while smoothing along the curved blade.
for ed in me.edges:
 a,b=ed.vertices
 if a<len(ts)*15 and b<len(ts)*15 and abs(a-b)==15:ed.use_edge_sharp=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(58),island_margin=.012,area_weight=.0,correct_aspect=True);bpy.ops.object.mode_set(mode='OBJECT')
triangles=sum(len(f)-2 for f in faces);assert 1000<=triangles<=3000,triangles
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1/sword_clay.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/round1/sword_upload.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_attributes=False)
(P/'work/round1/geometry.json').write_text(json.dumps({'vertices':len(verts),'triangles':triangles,'grip_max_radius_m':.0118,'grip_axis_range_m':[-.191,.106],'tip_axis_edge_flat':[.85,-.18,0],'author_coordinates':'Blender X=axis Y=flat Z=-edge','source_design':'references_hd/sword_round1/design.png'},indent=2))
scene=bpy.context.scene;common.workbench_clay(scene,textured=False);scene.render.resolution_x=1400;scene.render.resolution_y=620
for name,direction in [('side',Vector((0,-1,0))),('three_quarter',Vector((-.25,-1,.55)))]:
 centre=Vector((.30,0,.065));d=direction.normalized();cam=common.ortho_camera('ReviewCamera',centre+d*3,(0,0,0),1.28);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.filepath=str(P/f'review/round1/sword_clay_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
print('SWORD GEOMETRY',triangles,'triangles')

import runpy
runpy.run_path(str(P/'scripts/sword_uv_round1.py'),run_name='__main__')
