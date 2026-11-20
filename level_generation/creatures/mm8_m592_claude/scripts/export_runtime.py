"""Pack the editable Guardian and export its runtime roles at 60 Hz, preserving authored seconds."""
from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1];T=P/'textures';E=P/'export';E.mkdir(exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(P/'work/attack_revision_03.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
old=bpy.data.actions.get('Cast')
if old:bpy.data.actions.remove(old)
cast=bpy.data.actions['Attack'].copy();cast.name='Cast';cast.use_fake_user=True
keep={'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'}
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
assert set(a.name for a in bpy.data.actions)==keep
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
from mathutils import Vector
# A rigid palm marker follows the fitted hand and never changes the skin weights.
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
fs=json.loads((P/'work/claws_fit.json').read_text())['R'];palm=(sum((Vector(f['base']) for f in fs),Vector())/3+rig.data.edit_bones['B_R_Hand'].head)/2
bone=rig.data.edit_bones.new('Socket_Palm_Right');bone.head=palm;bone.tail=palm+Vector((0,0,.035));bone.parent=rig.data.edit_bones['B_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
hd=[v.value for v in body.data.attributes['head'].data]
for f in body.data.polygons:
 if hd[f.index]:
  for li in f.loop_indices:body.data.uv_layers['UVMap'].data[li].uv=body.data.uv_layers['HeadUV'].data[li].uv
body.data.uv_layers.active=body.data.uv_layers['UVMap']
for uv in body.data.uv_layers:uv.active_render=uv.name=='UVMap'
def material(name,prefix):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(kind,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'{prefix}_{kind}_1k.png'),check_existing=True);n.image.colorspace_settings.name=space;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color']);n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);return m
body.data.materials.clear()
for name,prefix in [('PlaneGuardian_A','m592'),('PlaneGuardianHead_A','m592_head')]:body.data.materials.append(material(name,prefix))
for f in body.data.polygons:f.material_index=int(hd[f.index])
body.hide_set(False);body.hide_render=False;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(E/'mm8_m592.blend'));a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();height=float(np.ptp(co[:,2]));info={'standing_visible_height_m':height,'native_visible_height_world':264.0,'runtime_scale':264/height,'chaos_runtime_scale':158.399604/height,'body_triangles':len(body.data.polygons),'head_triangles':sum(hd),'bones':len(rig.data.bones),'maximum_influences':max(sum(g.weight>1e-6 for g in v.groups) for v in body.data.vertices),'clips':{a.name:float((a.frame_range[1]-a.frame_range[0])/30) for a in bpy.data.actions},'export_sampling_fps':60}
# The dense death floor keys need 60 Hz export samples; all clip durations remain unchanged.
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.co.x*=2;k.handle_left.x*=2;k.handle_right.x*=2;k.interpolation='LINEAR'
 act.frame_start*=2;act.frame_end*=2
scene.render.fps=60
for uv in list(body.data.uv_layers):
 if uv.name!='UVMap':body.data.uv_layers.remove(uv)
body.name=body.data.name='PlaneGuardian'
for ob in bpy.context.view_layer.objects:ob.select_set(ob in (body,rig))
bpy.context.view_layer.objects.active=rig;rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
bpy.ops.export_scene.gltf(filepath=str(E/'mm8_m592_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(E/'export_info.json').write_text(json.dumps(info,indent=2)+'\n');print('EXPORTED',info,flush=True)
