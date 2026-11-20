"""One fixed 796-triangle axe, shared 1K maps, fixed-ratio lower LODs; no trial search."""
import bpy,bmesh,sys,json,math,copy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];R=P/'review/round4';T=P/'textures/round4_axe';T.mkdir(exist_ok=True)
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,accessor_bytes
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'before/mm6_figc_axe.glb'));source=next(o for o in bpy.data.objects if o.type=='MESH');source.name='AcceptedAxe'
d,raw=read_glb(R/'before/mm6_figc.glb');sk=d['skins'][0];k=[d['nodes'][j]['name'] for j in sk['joints']].index('Axe');ib=Matrix(np.frombuffer(accessor_bytes(d,raw,sk['inverseBindMatrices']),np.float32).reshape(-1,16)[k].reshape(4,4).T.tolist())
eq=json.loads((P/'work/equipment.json').read_text());c=Vector(eq['axe_centre']);axis=Vector(eq['axe_axis']);edge=Vector(eq['axe_edge']);normal=axis.cross(edge).normalized()
verts=[];faces=[];smooth=[]
def vert(p):
 q=ib@Vector((p.x,p.z,-p.y,1));verts.append((q.x,-q.z,q.y));return len(verts)-1
def face(ids,s=True):faces.append(ids);smooth.append(s)
def point(x,y,z):return c+axis*(-.11+(1455-y)*(.58/1430))+edge*((x-512)*(.366/826))+normal*z
outline=[(462,205),(372,204),(325,188),(291,164),(263,123),(240,73),(227,26),(194,62),(161,113),(134,176),(114,236),(101,300),(103,372),(114,434),(138,492),(171,545),(227,590),(241,542),(252,494),(274,449),(306,416),(348,404),(377,407),(462,420)]
for bit in [-1,1]:
 outer=[]
 for side in [-1,1]:
  rings=[]
  for scale,depth in [(1,.0009),(.91,.0065),(.40,.016)]:
   ring=[]
   for i,(x,y) in enumerate(outline):
    x,y=325+(x-325)*scale,307+(y-307)*scale
    thickness=depth if 5<=i<=17 else max(depth,.011+(x-325)*.00004)
    ring.append(vert(point(x if bit<0 else 1024-x,y,side*thickness)))
   rings.append(ring)
  for j in range(2):
   for i in range(24):n=(i+1)%24;face([rings[j][i],rings[j][n],rings[j+1][n],rings[j+1][i]],j>0)
  hub=vert(point(325 if bit<0 else 699,307,side*.017))
  for i in range(24):face([rings[-1][i],rings[-1][(i+1)%24],hub])
  outer.append(rings[0])
 for i in range(24):n=(i+1)%24;face([outer[0][i],outer[0][n],outer[1][n],outer[1][i]],False)
def tube(a,b,profile,sides):
 a,b=Vector(a),Vector(b);direction=(b-a).normalized();u=direction.orthogonal().normalized();v=direction.cross(u).normalized();rings=[]
 for t,r in profile:rings.append([vert(a.lerp(b,t)+(u*math.cos(i*2*math.pi/sides)+v*math.sin(i*2*math.pi/sides))*r) for i in range(sides)])
 for j in range(len(rings)-1):
  for i in range(sides):n=(i+1)%sides;face([rings[j][i],rings[j][n],rings[j+1][n],rings[j+1][i]])
 face(rings[0][::-1],False);face(rings[-1],False)
tube(c-axis*.105,c+axis*.43,[(0,.0104),(1,.011)],8)
# The accepted grip envelope survives; the eight spiral turns become baked detail.
tube(c-axis*.085,c+axis*.126,[(0,.0115),(1,.0115)],12)
tube(c-axis*.116,c-axis*.087,[(0,.014*.76),(.20,.014),(.75,.014),(1,.014*.82)],8)
tube(c+axis*.112,c+axis*.128,[(0,.0124),(1,.0124)],8)
rings=[]
for py,rx,rz in [(150,.026,.017),(171,.030,.021),(452,.029,.020),(486,.025,.017)]:
 rings.append([vert(point(512+rx*math.cos(i*2*math.pi/8)/(.366/826),py,rz*math.sin(i*2*math.pi/8))) for i in range(8)])
for j in range(3):
 for i in range(8):n=(i+1)%8;face([rings[j][i],rings[j][n],rings[j+1][n],rings[j+1][i]])
face(rings[0][::-1],False);face(rings[-1],False)
me=bpy.data.meshes.new('Axe796');me.from_pydata(verts,[],faces);me.update()
for f,s in zip(me.polygons,smooth):f.use_smooth=s
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
low=bpy.data.objects.new('Axe',me);bpy.context.scene.collection.objects.link(low)
for o in bpy.data.objects:o.select_set(o==low)
bpy.context.view_layer.objects.active=low
mat=bpy.data.materials.new('FighterChainGear_A_reduced');mat.use_nodes=True;me.materials.append(mat)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.04);bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles();assert len(me.loop_triangles)==796,len(me.loop_triangles)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=False;scene.render.bake.cage_extrusion=.008;scene.render.bake.max_ray_distance=.035;scene.render.bake.margin=16;scene.render.bake.use_clear=True
source_mat=source.data.materials[0];nt=source_mat.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');target_node=mat.node_tree.nodes.new('ShaderNodeTexImage');mat.node_tree.nodes.active=target_node
ad,ab=read_glb(R/'before/mm6_figc_axe.glb');am=ad['materials'][0];tex_indices={'basecolor':am['pbrMetallicRoughness']['baseColorTexture']['index'],'metal_rough':am['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],'region_mask':am['extras']['openyamm_region_mask']['index']}
images={}
for kind in ['basecolor','metal_rough','region_mask','normal']:
 if kind=='normal':nt.links.new(bs.outputs[0],out.inputs['Surface'])
 else:
  im=ad['images'][ad['textures'][tex_indices[kind]]['source']];v=ad['bufferViews'][im['bufferView']];f=R/f'accepted_axe_{kind}.png';f.write_bytes(ab[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);image=bpy.data.images.load(str(f));image.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color';node=nt.nodes.new('ShaderNodeTexImage');node.image=image;em=nt.nodes.new('ShaderNodeEmission');nt.links.new(node.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface'])
 image=bpy.data.images.new('axe_'+kind,width=1024,height=1024,alpha=False);image.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color';target_node.image=image;images[kind]=image
 for o in bpy.data.objects:o.select_set(o in [source,low])
 bpy.context.view_layer.objects.active=low;bpy.ops.object.bake(type='NORMAL' if kind=='normal' else 'EMIT',normal_space='TANGENT')
 image.filepath_raw=str(T/f'{kind}.png');image.file_format='PNG';image.save();image.pack();print('AXE_BAKED',kind,flush=True)
nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
def tex(kind):
 n=nt.nodes.new('ShaderNodeTexImage');n.image=images[kind];return n
nt.links.new(tex('basecolor').outputs['Color'],bs.inputs['Base Color']);n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough').outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
source.hide_render=True;source.hide_set(True)
counts=[]
for level,target in enumerate([796,432,196,78]):
 ob=low if level==0 else low.copy()
 if level:
  ob.data=low.data.copy();scene.collection.objects.link(ob);ob.name=f'Axe_LOD{level}'
  for o in bpy.data.objects:o.select_set(o==ob)
  bpy.context.view_layer.objects.active=ob;m=ob.modifiers.new('Fixed target','DECIMATE');m.ratio=target/796;m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
 ob.data.calc_loop_triangles();counts.append(len(ob.data.loop_triangles))
 for o in bpy.data.objects:o.select_set(o==ob)
 bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.gltf(filepath=str(R/f'axe_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_morph=False,export_image_format='AUTO')
 ob.hide_render=level>0
bpy.ops.wm.save_as_mainfile(filepath=str(R/'axe_authoring.blend'))
(R/'axe_counts.json').write_text(json.dumps({'before':[2122,945,356,118],'after':counts,'reduction_passes':1,'structural_correction':'bit necks extend into socket after removing raised langets; same fixed triangle targets','map_size':[1024,1024]},indent=2));print('AXE_COUNTS',counts,flush=True)
