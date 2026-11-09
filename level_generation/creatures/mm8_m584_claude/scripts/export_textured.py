"""Build packed editable/portable tiers and a shared-texture runtime input, retaining 60 Hz animation."""
import bpy,json,sys,runpy
import numpy as np
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];T=P/'textures';sys.path.insert(0,str(P/'scripts'));import common
for directory in ['export','review/textured','review/viewer']:(P/directory).mkdir(exist_ok=True)
def export(src,out):
 s=P/'scripts/export_glb.py';sys.argv=[str(s),'--',str(src),str(out)];runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
body=bpy.data.objects['Body'];prop=bpy.data.objects['PolearmMesh'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
head=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',head)
uv=me.uv_layers['UVMap'].data;huv=me.uv_layers['HeadUV'].data
for face in me.polygons:
 if head[face.index]:
  for loop in face.loop_indices:uv[loop].uv=huv[loop].uv
me.uv_layers.remove(me.uv_layers['HeadUV']);me.uv_layers.active=me.uv_layers['UVMap']
def material(name,prefix):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
 def texture(suffix,color):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'{prefix}_{suffix}_1k.png'),check_existing=True);n.image.colorspace_settings.name=color;return n
 base=texture('basecolor','sRGB');base.name='BaseColor';nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);nt.nodes.active=base
 normal=texture('normal','Non-Color');nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(normal.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 orm=texture('metal_rough','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(orm.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 return mat
me.materials.clear();me.materials.append(material('Raven_A','raven'));me.materials.append(material('RavenHead_A','raven_head'));me.polygons.foreach_set('material_index',head)
prop.data.materials.clear();prop.data.materials.append(material('RavenPolearm_A','raven_polearm'))
for face in prop.data.polygons:face.material_index=0
prop.data.uv_layers.active.name='UVMap'
# The shared attachment splitter consumes one Body LOD chain; the polearm keeps its rigid joint and material.
for o in bpy.data.objects:o.select_set(o in (body,prop))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
assert len(body.data.polygons)==14290+1536
runtime=P/'work/runtime_textured.blend';bpy.ops.wm.save_as_mainfile(filepath=str(runtime));export(runtime,P/'export/raven_runtime_lod0_raw.glb')
for tier in 'abc':
 bpy.ops.wm.open_mainfile(filepath=str(runtime));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
 for mat,prefix in zip(body.data.materials,('raven','raven_head','raven_polearm')):
  mat.name={'raven':'Raven','raven_head':'RavenHead','raven_polearm':'RavenPolearm'}[prefix]+'_'+tier.upper()
  mat.node_tree.nodes['BaseColor'].image=bpy.data.images.load(str(T/f'{prefix}_preview_raven_{tier}.png'))
 if tier=='a':
  for t in 'bc':
   for prefix in ('raven','raven_head','raven_polearm'):bpy.data.images.load(str(T/f'{prefix}_preview_raven_{t}.png'))
 bpy.ops.file.pack_all();path=P/f'work/portable_{tier}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if tier=='a':bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/raven_master.blend'))
 a=bpy.data.actions['Standing'];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 sc.frame_set(8);common.workbench_clay(sc,textured=True)
 common.render_views(str(P/'review/textured'/f'raven_{tier}'),1.05,4.2,views=('front','left','back','three_quarter'),resolution=(1024,768))
 common.render_views(str(P/'review/textured'/f'raven_{tier}_head'),2.14,.55,views=('front','left'),resolution=(512,512))
 export(path,P/f'review/viewer/raven_{tier}.glb')
