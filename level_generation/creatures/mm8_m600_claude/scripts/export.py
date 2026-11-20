"""Pack the animated master, shared PBR skin without baked attack effects."""
from pathlib import Path
import bpy,json
import numpy as np
P=Path(__file__).resolve().parents[1];repo=P.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['NightmareRig'];body=bpy.data.objects['Nightmare'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()

def material(name,prefix):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=False;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
 def tex(path,space):
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path));t.image.colorspace_settings.name=space;return t
 base=tex(P/'textures'/f'{prefix}_basecolor.png','sRGB');l.new(base.outputs['Color'],bs.inputs['Base Color']);n.active=base
 nm=n.new('ShaderNodeNormalMap');l.new(tex(P/'textures'/f'{prefix}_normal.png','Non-Color').outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs['Normal'])
 sep=n.new('ShaderNodeSeparateColor');l.new(tex(P/'textures'/f'{prefix}_orm.png','Non-Color').outputs['Color'],sep.inputs['Color']);l.new(sep.outputs['Green'],bs.inputs['Roughness']);l.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 return m
body.data.materials.clear();body.data.materials.append(material('Nightmare','body'))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
# The native front outline is 146/187 of its height; the geometry's earlier 0.70 width was too narrow.
rig.scale.x=(146/187)/.70
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([(body.matrix_world@v.co)[:] for v in m.vertices]);ev.to_mesh_clear()
height=co[:,2].max()-co[:,2].min();scale=187*1.5/height
(P/'work/scale.json').write_text(json.dumps({'height_m':float(height),'native_height_px':187,'native_frame_scale':1.5,'scale':float(scale),'width_fit':146/187,'root_x_scale':rig.scale.x},indent=2))
for img in bpy.data.images:
 if img.source=='FILE' and img.filepath:img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/nightmare_final.blend'))
for at in list(body.data.attributes):
 if at.name=='owner':body.data.attributes.remove(at)
for o in bpy.data.objects:o.select_set(o in [body,rig])
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m600_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('EXPORTED',len(rig.data.bones),'bones',len(body.data.polygons),'body triangles', {a.name:float(a.frame_range[1])/120 for a in bpy.data.actions})
