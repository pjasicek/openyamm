"""Export shared body/head paint and a skinned throat sac for later extraction as the C-only attachment."""
import bpy,sys,os,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];T=P/'textures';E=P/'export';E.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_final.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
head=np.array([x.value for x in me.attributes['head'].data],bool);piece=np.array([x.value for x in me.attributes['piece'].data]);pores=set(json.loads((P/'review/geometry/cleanup.json').read_text())['pores_flattened'])
uv=me.uv_layers['BodyUV'];huv=me.uv_layers['HeadUV']
for f in me.polygons:
 if head[f.index]:
  for li in f.loop_indices:uv.data[li].uv=huv.data[li].uv
for n in [l.name for l in me.uv_layers if l!=uv]:me.uv_layers.remove(me.uv_layers[n])
uv.name='UVMap';me.uv_layers.active=uv;uv.active_render=True
me.materials.clear()
def material(name,kind,res):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True;m['openyamm_specular']=1.;m['openyamm_specular_mask']=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'gloamer_{kind}_{suffix}_{res}.png'));n.image.colorspace_settings.name=space;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color'])
 normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);return m
for name,kind in [('GloamerBody_A','body'),('GloamerHead_A','head'),('GloamerPores_A','body')]:me.materials.append(material(name,kind,'1k'))
for f in me.polygons:f.material_index=2 if piece[f.vertices[0]] in pores else int(head[f.index]);f.use_smooth=True
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(0,-.24,1.13));sac=bpy.context.object;sac.name='ElderSac';sac.scale=(.105,.11,.16)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
sac.data.materials.append(material('GloamerSac_A','sac','256'))
for f in sac.data.polygons:f.use_smooth=True
sac.vertex_groups.new(name='ThroatSac').add(list(range(len(sac.data.vertices))),1.,'REPLACE')
attr=sac.data.attributes.new('piece','INT','POINT')
for v in attr.data:v.value=100
for o in bpy.data.objects:o.select_set(o in (body,sac))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();me=body.data
mod=body.modifiers.new('Triangulate','TRIANGULATE');bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
sc.render.fps=30;sc.render.fps_base=1
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_export.blend'))
# Authoring labels remain in the saved master, but do not become runtime vertex attributes.
for n in ['piece','finger','head','orig_co','source_piece','region']:
 if n in me.attributes:me.attributes.remove(me.attributes[n])
body.name=body.data.name='Gloamer'
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(E/'hes_gloamer_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_extras=True,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('EXPORT',len(me.polygons),'triangles',len(rig.data.bones),'bones',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
