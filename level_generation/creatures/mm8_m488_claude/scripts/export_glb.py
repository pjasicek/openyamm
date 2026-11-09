"""Export the fitted animation master with separate body/head sets and one combined mesh."""
from pathlib import Path
import bpy,sys,json,runpy
import numpy as np
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
hd=np.array([x.value for x in me.attributes['head'].data])
for f in me.polygons:
 if hd[f.index]:
  for li in f.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
me.uv_layers.remove(me.uv_layers['HeadUV']);me.uv_layers.active=me.uv_layers['UVMap']
# Measure the joined UVs; the retained head file stays untouched, so rebuilds are idempotent.
path=P.parent/'claude_shared/head_seam_gain.py'
sys.argv=[str(path),'--','--mesh','Body','--body',str(T/'m488_basecolor_1k.png'),'--head',str(T/'m488_head_basecolor_1k.png'),'--out',str(T/'head_seam.json')]
runpy.run_path(str(path),run_name='__main__')
me.materials.clear()
for name,tag in [('Minotaur_A','m488'),('MinotaurHead_A','m488_head')]:
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=False
 mat['openyamm_specular']=1.;mat['openyamm_specular_mask']=True
 nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
 def tex(suffix,space):
  im=bpy.data.images.load(str(T/(tag+suffix)));im.colorspace_settings.name=space;im.pack()
  n=nt.nodes.new('ShaderNodeTexImage');n.image=im;return n
 nt.links.new(tex('_basecolor_1k.png','sRGB').outputs['Color'],bs.inputs['Base Color'])
 nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('_normal_1k.png','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('_metal_rough_1k.png','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 me.materials.append(mat)
me.polygons.foreach_set('material_index',hd.tolist());body.name=body.data.name='Minotaur'
keep={'Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'}
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
assert {a.name for a in bpy.data.actions}==keep
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();xyz=np.array([tuple(body.matrix_world@v.co) for v in mesh.vertices]);ev.to_mesh_clear()
info={'standing_height_m':float(np.ptp(xyz[:,2])),'standing_z_min':float(xyz[:,2].min()),'triangles':sum(len(f.vertices)-2 for f in me.polygons),'bones':len(rig.data.bones),'clips':{a.name:float(a.frame_range[1])/30 for a in bpy.data.actions}}
(P/'export').mkdir(exist_ok=True);(P/'export/info.json').write_text(json.dumps(info,indent=2)+'\n')
# Store editable attributes in the packed master; omit authoring attributes from the GLB.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/m488_textured_master.blend'))
for obj in bpy.data.objects:obj.select_set(obj in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m488_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
print('EXPORT',info)
