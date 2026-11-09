"""Packed editable master and portable textured GLB of eight verified motions and their native cast alias."""
from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1];T=p/'textures';E=p/'export';E.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
assert max(sum(e.weight>0 for e in v.groups) for v in body.data.vertices)<=8
# Native attack and spellcasting share the same charge/release sequence; the runtime needs a separate role index.
old=bpy.data.actions.get('Cast')
if old:bpy.data.actions.remove(old)
cast=bpy.data.actions['Attack'].copy();cast.name='Cast';cast.use_fake_user=True
keep={'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'}
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
assert {a.name for a in bpy.data.actions}==keep
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
hd=[x.value for x in body.data.attributes['head'].data]
for f in body.data.polygons:
 if hd[f.index]:
  for li in f.loop_indices:body.data.uv_layers['UVMap'].data[li].uv=body.data.uv_layers['HeadUV'].data[li].uv
def material(name,prefix,size):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(kind,space):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/(f'{prefix}_{kind}.png' if size=='native' else f'{prefix}_{kind}_{size}.png')),check_existing=True);node.image.colorspace_settings.name=space;return node
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color'])
 n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 return m
body.data.materials.clear()
for name,prefix in [('Cleric_A','m460'),('ClericHead_A','m460_head')]:body.data.materials.append(material(name,prefix,'1k'))
for f in body.data.polygons:f.material_index=int(hd[f.index])
staff.data.materials.clear();staff.data.materials.append(material('ClericStaff_A','m460_staff','native'))
for f in staff.data.polygons:f.material_index=0
for ob in [body,staff]:
 ob.data.uv_layers.active=ob.data.uv_layers['UVMap']
 for uv in ob.data.uv_layers:uv.active_render=uv.name=='UVMap'
 ob.hide_render=False;ob.hide_set(False)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(E/'mm8_m460.blend'))
st=bpy.data.actions['Standing'];rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();P=np.array([tuple(body.matrix_world@v.co) for v in mesh.vertices]);ev.to_mesh_clear();height=float(np.ptp(P[:,2]))
info={'standing_visible_height_m':height,'native_visible_height_world':188.0,'runtime_scale':188.0/height,'body_triangles':len(body.data.polygons),'staff_triangles':len(staff.data.polygons),'clips':{a.name:float((a.frame_range[1]-a.frame_range[0])/30) for a in bpy.data.actions}}
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
copies=[]
for ob in [body,staff]:
 cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);copies.append(cp)
 for uv in list(cp.data.uv_layers):
  if uv.name!='UVMap':cp.data.uv_layers.remove(uv)
for ob in bpy.context.view_layer.objects:ob.select_set(ob in copies)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();combined=copies[0];combined.name=combined.data.name='Cleric'
for ob in bpy.context.view_layer.objects:ob.select_set(ob in [combined,rig])
bpy.context.view_layer.objects.active=rig;rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];scene.frame_set(0)
bpy.ops.export_scene.gltf(filepath=str(E/'mm8_m460_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',
 export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(E/'export_info.json').write_text(json.dumps(info,indent=2)+'\n');print('EXPORTED',info,flush=True)
