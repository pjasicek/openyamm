"""Project-local selected-to-active bake from the accepted unreduced body."""
import bpy,sys,json,time,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';T=P/'textures/round3';R=P/'review/round3'
sys.path.insert(0,str(P.parents[2]/'tools'))
import struct
def read_glb(path):
 raw=path.read_bytes();n=struct.unpack_from("<I",raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
# Use the last passing ten-percent silhouette step.
sys.path.insert(0,str(P/'scripts'));import reduce_round2 as old
body,rig=old.reset(0)
for o in list(bpy.data.objects):
 if o not in [body,rig]:bpy.data.objects.remove(o,do_unlink=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
print('VALIDATE',body.data.validate(clean_customdata=False),flush=True)
body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
for face in body.data.polygons:face.use_smooth=True
body.data.update()
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT')
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(W/'high_body.glb'));added=set(bpy.data.objects)-before
high=next(o for o in added if o.type=='MESH' and o.name.startswith('KnightPlate'));hrig=next(o for o in added if o.type=='ARMATURE');hrig.animation_data.action=None
for pb in hrig.pose.bones:pb.matrix_basis.identity()
for o in added:
 if o not in [high,hrig]:bpy.data.objects.remove(o,do_unlink=True)
# Separate disconnected armour parts during projection to prevent rays hitting neighbouring plates.
from mathutils import Vector,kdtree
def components(obj):
 parent=list(range(len(obj.data.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def join(a,b):parent[root(b)]=root(a)
 coords={}
 for v in obj.data.vertices:
  key=tuple(round(x,6)for x in v.co)
  if key in coords:join(v.index,coords[key])
  else:coords[key]=v.index
 for e in obj.data.edges:join(*e.vertices)
 return [root(i)for i in range(len(parent))]
from collections import Counter
hi=components(high);lo=components(body);unique=sorted(set(hi));tree=kdtree.KDTree(len(hi))
for v in high.data.vertices:tree.insert(v.co,v.index)
tree.balance();mapping={}
for c in set(lo):mapping[c]=Counter(hi[tree.find(v.co)[1]]for v in body.data.vertices if lo[v.index]==c).most_common(1)[0][0]
restore={};print('BAKE COMPONENTS',len(unique),len(mapping),flush=True)
for obj,ids in [(high,hi),(body,[mapping[x]for x in lo])]:
 restore[obj]=[v.co.copy()for v in obj.data.vertices]
 for v,piece in zip(obj.data.vertices,ids):
  k=unique.index(piece);v.co+=Vector(((k%9)*3,(k//9)*3,0))
 obj.data.update()
bpy.context.view_layer.update()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.03;scene.render.bake.max_ray_distance=.10;scene.render.bake.margin=16;scene.render.bake.use_clear=True
scene.render.bake.normal_space='TANGENT';scene.render.bake.normal_r='POS_X';scene.render.bake.normal_g='POS_Y';scene.render.bake.normal_b='POS_Z'
# Extract the accepted maps verbatim; R in the MR texture is the engine specular mask.
d,b=read_glb(W/'high_body.glb');paths={}
for i,key in [(0,'normal'),(1,'basecolor'),(2,'metal_rough'),(3,'region_mask')]:
 v=d['bufferViews'][d['images'][i]['bufferView']];path=W/f'high_{key}.png';path.write_bytes(bytes(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]));paths[key]=path
source=high.data.materials[0];nodes=source.node_tree.nodes;links=source.node_tree.links;output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');original=output.inputs['Surface'].links[0].from_socket
emit=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage');links.new(tex.outputs['Color'],emit.inputs['Color'])
mat=bpy.data.materials.new('Rebaked KnightPlate');mat.use_nodes=True;body.data.materials.clear();body.data.materials.append(mat);bs=mat.node_tree.nodes.get('Principled BSDF');target=mat.node_tree.nodes.new('ShaderNodeTexImage');mat.node_tree.nodes.active=target
bpy.ops.object.select_all(action='DESELECT');high.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=body
receipt={'source':'work/round3/high_body.glb','triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'cage_extrusion_m':.03,'max_ray_distance_m':.10,'margin_px':16,'separated_armour_parts':True,'method':'Cycles selected-to-active, fresh non-overlapping reduced-mesh atlas, OpenGL tangent normals','maps':{}}
for key,size,color in [('basecolor',2048,'sRGB'),('region_mask',1024,'Non-Color'),('metal_rough',1024,'Non-Color'),('normal',1024,'Non-Color')]:
 image=bpy.data.images.new(f'Knight rebake {key}',width=size,height=size,alpha=False,float_buffer=False);image.colorspace_settings.name=color;target.image=image
 if key=='normal':links.new(original,output.inputs['Surface']);kind='NORMAL'
 else:
  tex.image=bpy.data.images.load(str(paths[key]),check_existing=False);tex.image.colorspace_settings.name=color;links.new(emit.outputs[0],output.inputs['Surface']);kind='EMIT'
 started=time.time();bpy.ops.object.bake(type=kind);image.filepath_raw=str(T/f'knight_{key}.png');image.file_format='PNG';image.save();receipt['maps'][key]={'path':f'textures/round3/knight_{key}.png','size':size,'seconds':time.time()-started};print('BAKE',key,receipt['maps'][key],flush=True)
links.new(original,output.inputs['Surface'])
for obj,coords in restore.items():
 for v,co in zip(obj.data.vertices,coords):v.co=co
 obj.data.update()
bpy.context.view_layer.update()
# Give the reduced mesh the rebaked PBR maps; runtime metadata is preserved during packaging.
for key,socket in [('basecolor','Base Color'),('metal_rough',None),('normal',None)]:
 n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'knight_{key}.png'),check_existing=True)
 if key!='basecolor':n.image.colorspace_settings.name='Non-Color'
 if socket:mat.node_tree.links.new(n.outputs['Color'],bs.inputs[socket])
 elif key=='normal':
  nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(n.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 else:
  sep=mat.node_tree.nodes.new('ShaderNodeSeparateColor');mat.node_tree.links.new(n.outputs['Color'],sep.inputs[0]);mat.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness'])
bs.inputs['Metallic'].default_value=0
for o in [high,hrig]:bpy.data.objects.remove(o,do_unlink=True)
mat.node_tree.nodes.active=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'basecolor'in n.image.name)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(W/'rebaked_l0.blend'))
bpy.ops.export_scene.gltf(filepath=str(W/'geometry_body_l0.glb'),export_format='GLB',use_selection=True,export_animations=False,export_all_influences=True,export_attributes=False)
(R/'bake.json').write_text(json.dumps(receipt,indent=2))
