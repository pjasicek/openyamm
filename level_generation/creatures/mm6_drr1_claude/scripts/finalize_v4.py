"""Wyrm revision 04 master (retopology + retexture): work/uv_final.blend with the composed textures ->
mm6_drr1_claude/export/mm6_wyrm.blend, export/mm6_wyrm_lod0.glb and export/mm6_wyrm_remains.glb.
Material setup and the charred remnant follow mm6_drr1_claude/scripts/finish_materials.py and finalize.py."""
import os
import bpy
import numpy as np
from pathlib import Path

P = Path(__file__).resolve().parents[1]; T = P / 'textures'
HERE = P.parent / 'mm6_drr1_retopo_claude'
bpy.ops.wm.open_mainfile(filepath=str(HERE / 'work' / os.environ.get('REA_UVBLEND', 'uv_final_v5.blend')))
mesh = bpy.data.objects['Wyrm']; rig = bpy.data.objects['Wyrm_Rig']; sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name.startswith('Wyrm_Remains'):
        bpy.data.objects.remove(o, do_unlink=True)


def material(mat, prefix, normal_strength):
    mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])

    def tex(file, space):
        im = bpy.data.images.load(str(T / file)); im.colorspace_settings.name = space; im.pack()
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = im; return n
    bc = tex(f'{prefix}_basecolor_graded.png', 'sRGB'); nt.links.new(bc.outputs['Color'], bs.inputs['Base Color'])
    nm = tex(f'{prefix}_normal_1k.png', 'Non-Color'); normal = nt.nodes.new('ShaderNodeNormalMap')
    normal.inputs['Strength'].default_value = normal_strength
    nt.links.new(nm.outputs['Color'], normal.inputs['Color']); nt.links.new(normal.outputs['Normal'], bs.inputs['Normal'])
    mr = tex(f'{prefix}_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bs.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bs.inputs['Metallic'])
    mat['openyamm_specular'] = 1.0; mat['openyamm_specular_mask'] = True


assert [m.name for m in mesh.data.materials] == ['Wyrm', 'WyrmHead'], [m.name for m in mesh.data.materials]
material(mesh.data.materials[0], 'wyrm', 1.0)
material(mesh.data.materials[1], 'wyrm_head', .6)
if 'part' in mesh.data.attributes:
    mesh.data.attributes.remove(mesh.data.attributes['part'])

# charred remnant from the Dead pose (finalize.py)
rig.animation_data.action = bpy.data.actions['Dead']; sc.frame_set(1); bpy.context.view_layer.update()
remesh = bpy.data.meshes.new_from_object(mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()))
remains = bpy.data.objects.new('Wyrm_Remains', remesh); sc.collection.objects.link(remains)
co = np.array([v.co[:] for v in remesh.vertices]); center = (co.min(0) + co.max(0)) / 2
names = {g.index: g.name for g in mesh.vertex_groups}
core = [v.index for v in mesh.data.vertices
        if sum(g.weight for g in v.groups if names[g.group] in ['Spine1', 'Spine2', 'Spine3']) > .7]
body_floor = float(np.percentile(co[core, 2], 20))
for v in remesh.vertices:
    v.co.x = (v.co.x - center[0]) * .62; v.co.y = (v.co.y - center[1]) * .4
    v.co.z = max(0, v.co.z - body_floor) * .72 + .001
bpy.ops.object.select_all(action='DESELECT'); remains.select_set(True); bpy.context.view_layer.objects.active = remains
m = remains.modifiers.new('CharredRemnant', 'DECIMATE'); m.ratio = 1050 / len(remesh.polygons)
m.use_collapse_triangulate = True; bpy.ops.object.modifier_apply(modifier=m.name)
mat = bpy.data.materials.new('CharredRemains'); mat.use_nodes = True
bs = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value = (.008, .012, .006, 1); bs.inputs['Roughness'].default_value = .98
bs.inputs['Specular IOR Level'].default_value = .5; mat['openyamm_specular'] = .05
remains.data.materials.clear(); remains.data.materials.append(mat)
for f in remains.data.polygons:
    f.material_index = 0
bpy.ops.export_scene.gltf(filepath=str(P / 'export/mm6_wyrm_remains.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_skins=False, export_animations=False, export_extras=True)
remains.hide_set(True); remains.hide_render = True
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(1)
for a in bpy.data.actions:
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = 'LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'export/mm6_wyrm.blend'))
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o in (mesh, rig) or o.name.startswith('Socket_'):
        o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(P / 'export/mm6_wyrm_lod0.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
                          export_force_sampling=True, export_frame_step=1, export_skins=True,
                          export_all_influences=True, export_attributes=False, export_morph=False,
                          export_image_format='AUTO', export_reset_pose_bones=True, export_anim_slide_to_zero=True,
                          export_extras=True)
print('FINAL', len(mesh.data.polygons), 'remains', len(remains.data.polygons))
