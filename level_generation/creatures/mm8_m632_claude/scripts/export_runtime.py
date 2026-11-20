"""Portable textured dwarf master and full-detail runtime export; clips are already fitted and timed."""
import bpy,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
sc=bpy.context.scene;assert sc.render.fps==120
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['Crossbow'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
head=np.array([v.value for v in me.attributes['head'].data])
for f in me.polygons:
 if head[f.index]:
  for li in f.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
for layer in list(me.uv_layers):
 if layer.name!='UVMap':me.uv_layers.remove(layer)
me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers['UVMap'].active_render=True
def material(name,prefix):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,color):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(P/'textures'/f'{prefix}_{suffix}.png'));n.image.colorspace_settings.name=color;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color'])
 nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('orm','Non-Color').outputs['Color'],sep.inputs['Color'])
 nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);return m
me.materials.clear()
for name,prefix in [('Dwarf_A','m632_body'),('DwarfHead_A','m632_head')]:me.materials.append(material(name,prefix))
me.polygons.foreach_set('material_index',head.tolist())
prop.data.materials.clear();prop.data.materials.append(material('Crossbow_A','m632_crossbow'))
for f in prop.data.polygons:f.material_index=0
for o in bpy.data.objects:o.select_set(o in (body,prop))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='DarkDwarf'
for a in list(body.data.attributes):
 if a.name in ('piece','head','finger','orig_co'):body.data.attributes.remove(a)
for act in bpy.data.actions:common.action_continuity(act)
expected={'Standing':2,'Walking':.8,'Running':44/60,'Attack':1.55,'Hit':.6,'Death':1.5,'Dead':1,'Fidget':1.25}
assert set(a.name for a in bpy.data.actions)==set(expected)
for a in bpy.data.actions:assert abs((a.frame_range[1]-a.frame_range[0])/120-expected[a.name])<1e-5,(a.name,a.frame_range[:])
assert len(rig.data.bones)<128
assert max(sum(g.weight>1e-6 for g in v.groups) for v in body.data.vertices)<=8
bpy.ops.outliner.orphans_purge(do_recursive=True);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m632.blend'))
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m632_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,
 export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
co=np.array([tuple(v.co) for v in body.data.vertices]);a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();posed=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear()
height=float(posed[:,2].max()-posed[:,2].min());info={'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'bones':len(rig.data.bones),'upright_height_m':height,'native_height_px':166,'runtime_scale':166/height,'clips_seconds':expected}
(P/'export/export_info.json').write_text(json.dumps(info,indent=2));print('EXPORTED',info,flush=True)
