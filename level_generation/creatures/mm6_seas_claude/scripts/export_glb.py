"""Export the sea serpent master (skin material 'Seas' + foam collar 'Foam', all clips) to export/mm6_seas_lod0.glb.
Tiers are added afterwards by claude_shared/region_variants.py (region mask + ramps)."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
mesh = bpy.data.objects['Seas']; rig = bpy.data.objects['Seas_Rig']
mat = bpy.data.materials.new('Seas'); mat.use_nodes = True; mat.use_backface_culling = False; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(file, cs):
    img = bpy.data.images.load(os.path.join(T, file)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


nt.links.new(tex('seas_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('seas_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('seas_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
foam = bpy.data.materials.new('Foam'); foam.use_nodes = True; foam.use_backface_culling = False; fnt = foam.node_tree
fbsdf = next(n for n in fnt.nodes if n.type == 'BSDF_PRINCIPLED')
fimg = bpy.data.images.load(os.path.join(T, 'foam.png')); ftex = fnt.nodes.new('ShaderNodeTexImage'); ftex.image = fimg
fnt.links.new(ftex.outputs['Color'], fbsdf.inputs['Base Color'])
fbsdf.inputs['Roughness'].default_value = 0.9
# glTF exports MASK when the alpha passes through a Math 'Round' (or Greater Than) node before the BSDF
cut = fnt.nodes.new('ShaderNodeMath'); cut.operation = 'ROUND'
fnt.links.new(ftex.outputs['Alpha'], cut.inputs[0]); fnt.links.new(cut.outputs[0], fbsdf.inputs['Alpha'])
for i, m in enumerate((mat, foam)):          # assign in place: clearing the slots resets every face to slot 0
    mesh.data.materials[i] = m
# The foam collar becomes its own skinned mesh node 'Foam': build_actor_lods.py reduces and shadows only 'Seas' (its
# merged shadow requires opaque materials), and the thin cut-out ring needs no LODs or shadow.
bpy.context.view_layer.objects.active = mesh
for o in bpy.context.view_layer.objects:
    o.select_set(o is mesh)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
mesh.active_material_index = 1; bpy.ops.object.material_slot_select(); bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
foam_obj = next(o for o in bpy.context.selected_objects if o is not mesh)
foam_obj.name = foam_obj.data.name = 'Foam'
foam_obj.data.materials.clear(); foam_obj.data.materials.append(foam)
mesh.data.materials.pop(index=1)
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (mesh, foam_obj, rig))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', 'mm6_seas_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
