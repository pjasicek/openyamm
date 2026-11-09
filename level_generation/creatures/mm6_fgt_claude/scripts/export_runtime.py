"""Export the gated textured Thug and its authored Mace bone; preserve all action keys."""
import bpy,json,math,os
import numpy as np
from pathlib import Path
HERE=str(Path(__file__).resolve().parents[1]);T=os.path.join(HERE,'textures')
p=Path(HERE)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_revision2.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];mace=bpy.data.objects['Mace'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
hd=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',hd)
for face in me.polygons:
 if hd[face.index]:
  for li in face.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
for layer in list(me.uv_layers):
 if layer.name!='UVMap':me.uv_layers.remove(layer)
sm=mace.data
assert sm.uv_layers.get('UVMap'), 'Mace needs its own detailed atlas'
def material(name, base, normal, mr):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(f, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(T, f)); n.image.colorspace_settings.name = cs
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m



mats=[material('Thug_A','fgt_basecolor_1k.png','fgt_normal_1k.png','fgt_metal_rough_1k.png'),
 material('ThugHead_A','fgt_head_basecolor_1k.png','fgt_head_normal_1k.png','fgt_head_metal_rough_1k.png'),
 material('Mace_A','fgt_mace_basecolor_1k.png','fgt_mace_normal_1k.png','fgt_mace_metal_rough_1k.png')]
for mesh in (me,sm):
 mesh.materials.clear()
 for mat in mats:mesh.materials.append(mat)
me.polygons.foreach_set('material_index',hd.tolist())
for face in sm.polygons:face.material_index=2
for o in bpy.data.objects:o.select_set(o in (body,mace))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
body.name=body.data.name='Thug'
for at in list(body.data.attributes):
 if at.name in ('piece','finger','head','orig_co','mace_class'):body.data.attributes.remove(at)
keep={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
assert set(a.name for a in bpy.data.actions)==keep
bpy.context.scene.render.fps=30
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
out=p/'export/mm6_fgt_lod0.glb'
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
 export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/thug_final.blend'))
info={'glb':str(out),'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'head_faces':int(hd.sum()),
 'clips':{a.name:float((a.frame_range[1]-a.frame_range[0])/30) for a in bpy.data.actions}}
assert info['triangles']<12000
(p/'export/export_info.json').write_text(json.dumps(info,indent=2))
print('EXPORTED',info)
