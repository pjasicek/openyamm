"""Detailed double axe traced from the selected HD design; metres, +Z shaft, X cutting edges."""
import bpy,bmesh,math,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
K=.00145;CX=461;BOTTOM=995
objects=[]
def world(x,y,d=0):return ((x-CX)*K,d,(BOTTOM-y)*K)
def mesh(name,vs,fs,cl):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);objects.append(ob)
 a=me.attributes.new('material_class','INT','FACE');a.data.foreach_set('value',[cl]*len(fs));return ob
def tube(name,stations,radius,cl=8,n=12):
 vs=[];fs=[]
 for y,r in stations:
  for i in range(n):
   t=2*math.pi*i/n;vs.append((r*math.cos(t),r*math.sin(t),(BOTTOM-y)*K))
 for k in range(len(stations)-1):
  for i in range(n):fs.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
 fs.extend([tuple(reversed(range(n))),tuple((len(stations)-1)*n+i for i in range(n))]);ob=mesh(name,vs,fs,cl)
 uv=ob.data.uv_layers.new(name='UVMap').data
 for poly in ob.data.polygons:
  for li in poly.loop_indices:
   vi=ob.data.loops[li].vertex_index;u=(vi%n)/n;y=stations[vi//n][0]
   uv[li].uv=((420+u*18)/768,1-(175+(y%60))/1024) if cl==9 else ((443+u*34)/768,1-y/1024)
 return ob
# Two matching crescent bits; the native's swept points and negative spaces are geometry.
outline=[(490,169),(548,169),(585,160),(610,142),(622,117),(621,95),(608,72),(586,50),(553,25),(584,27),(614,35),(644,50),(673,71),(696,96),(716,127),(731,159),(740,192),(742,223),(736,255),(724,287),(705,316),(682,341),(654,360),(622,374),(590,383),(555,387),(585,368),(608,345),(622,319),(623,294),(614,272),(596,253),(570,242),(540,237),(490,239)]
for side in [-1,1]:
 xy=[(CX+side*(x-CX),y) for x,y in outline];N=len(xy);vs=[world(x,y,d) for d in [-.009,.009] for x,y in xy];fs=[tuple(reversed(range(N))),tuple(N+i for i in range(N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 ob=mesh('AxeBit'+str(side),vs,fs,9);bpy.context.view_layer.objects.active=ob;ob.select_set(True);bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 mod=ob.modifiers.new('Real cutting bevel','BEVEL');mod.width=.006;mod.segments=1;mod.affect='EDGES';bpy.ops.object.modifier_apply(modifier=mod.name)
 uv=ob.data.uv_layers.new(name='UVMap').data
 for poly in ob.data.polygons:
  for li in poly.loop_indices:
   v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv[li].uv=((v.x/K+CX)/768,1-(BOTTOM-v.z/K)/1024)
 ob.select_set(False)
# Tapered wooden shaft, ferrules and sculptural socket. Wrap relief remains within the solved radius.
tube('Wooden shaft',[(258,.014),(490,.015),(618,.015),(845,.014)],.015,10)
for ya,yb in [(400,620),(641,840)]:
 turns=7;steps=turns*8;vs=[];fs=[]
 for i in range(steps+1):
  t=2*math.pi*turns*i/steps;y=ya+(yb-ya)*i/steps
  for dz,r in [(-.007,.015),(-.005,.0165),(.005,.0165),(.007,.015)]:vs.append((r*math.cos(t),r*math.sin(t),(BOTTOM-y)*K+dz))
 for i in range(steps):
  for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
 fs.extend([tuple(reversed(range(4))),tuple(steps*4+j for j in range(4))]);ob=mesh('Leather wrap',vs,fs,8);uv=ob.data.uv_layers.new(name='UVMap').data
 for poly in ob.data.polygons:
  for li in poly.loop_indices:
   vi=ob.data.loops[li].vertex_index;y=ya+(yb-ya)*(vi//4)/steps;yt=301+(y-ya)/(yb-ya)*171 if ya==400 else y;uv[li].uv=((442+(vi%4)*9)/768,1-yt/1024)
for y in [289,390,630]:tube('Gold ferrule',[(y-5,.016),(y-3,.020),(y+3,.020),(y+5,.016)],.02,9)
tube('Socket',[(160,.034),(167,.05),(180,.05),(237,.05),(247,.043),(269,.028),(281,.027)],.05,9,12)
tube('Butt cap',[(839,.013),(845,.013),(858,.026),(872,.027),(885,.019),(893,.011),(897,.002)],.036,9,12)
tube('Top spike',[(95,.0),(116,.018),(145,.011),(160,.027)],.027,9,8)
# Raised blue gemstones in bezels on both broad faces, sampled from the selected design.
for sign in [-1,1]:
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(0,sign*.051,(BOTTOM-207)*K));ob=bpy.context.object;ob.name='Blue central stone';ob.scale=(.020,.009,.030);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);objects.append(ob);a=ob.data.attributes.new('material_class','INT','FACE');a.data.foreach_set('value',[11]*len(ob.data.polygons));[ob.data.uv_layers.remove(layer) for layer in list(ob.data.uv_layers)];uv=ob.data.uv_layers.new(name='UVMap').data
 for poly in ob.data.polygons:
  for li in poly.loop_indices:
   v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv[li].uv=((461+v.x/.020*14)/768,1-(207-(v.z-(BOTTOM-207)*K)/.030*25)/1024)
# Detailed texture is a direct projection of the generated side design; no colour swatches.
mat=bpy.data.materials.new('MinotaurAxe');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(P/'textures/axe_basecolor.png'));nt.links.new(tx.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Metallic'].default_value=.35;bs.inputs['Roughness'].default_value=.62
for o in bpy.data.objects:o.select_set(o in objects)
for o in objects:
 if o.name.startswith(('AxeBit','Socket','Top','Blue')):
  for v in o.data.vertices:v.co.x*=.75;v.co.y*=.75;v.co.z=1.14+(v.co.z-1.14)*.75
 o.data.materials.clear();o.data.materials.append(mat)
 for f in o.data.polygons:f.material_index=0;f.use_smooth=o.name.startswith(('Wooden','Gold','Socket','Butt','Top','Leather','Blue'))
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();axe=bpy.context.object;axe.name=axe.data.name='Axe';bm=bmesh.new();bm.from_mesh(axe.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(axe.data);bm.free();tri=len(axe.data.polygons);assert 1000<=tri<=3300,tri
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/axe.blend'));bpy.ops.export_scene.gltf(filepath=str(P/'work/axe_preview.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_attributes=False)
scene=bpy.context.scene;common.workbench_clay(scene,textured=True)
for name,direction in [('side',(0,-1,0)),('three_quarter',(.65,-1,.3)),('edge',(1,-.1,0))]:
 c=Vector((0,0,.72));d=Vector(direction).normalized();cam=common.ortho_camera('Review',c+d*3,(0,0,0),1.60);cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.resolution_x=720;scene.render.resolution_y=1080;scene.render.filepath=str(P/f'review/axe_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
(P/'review/axe_geometry.json').write_text(json.dumps({'triangles':tri,'shaft_radius_m':.015,'wrap_max_radius_m':.0165,'blade_width_m':.612,'native_calibration':'Head resized to about 0.61 m, using the native front axe-to-body pixel ratio; shaft remains two-handed.','solved_handle_radius_m':.018,'source':'references_hd/axe_design.png','uv':'Direct design projection, intentionally shared opposite blade faces and repeating circular wrap UVs','features':['two swept crescent bits','six-millimetre geometric bevel','socket','two blue bosses','wood shaft','two helical wraps','six ferrules','stepped butt cap','top spike']},indent=2))
