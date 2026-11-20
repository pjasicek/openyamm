"""Bake a portable color atlas and export the rig, skin and named clips to GLB."""
import bpy
import json
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')
scene=bpy.data.scenes['Brown ghost sprite studio'];bpy.context.window.scene=scene
scene.frame_set(1)
obj=next(o for o in scene.objects if o.type=='MESH')
rig=scene.objects['Ghost RIG']
for o in scene.objects:o.select_set(False)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
source_uv=obj.data.uv_layers[0].name
# Preserve the procedural surface coordinates while adding a unique export atlas.
for mat in obj.data.materials:
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=source_uv
    for link in list(links):
        if link.from_node.type=='TEX_COORD' and link.from_socket.name=='UV':
            target=link.to_socket;links.remove(link);links.new(uv.outputs['UV'],target)
atlas_uv=obj.data.uv_layers.new(name='Portable color atlas')
obj.data.uv_layers.active=atlas_uv;atlas_uv.active_render=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.002)
bpy.ops.object.mode_set(mode='OBJECT')
atlas=bpy.data.images.new('Brown ghost albedo',width=4096,height=4096,alpha=False)
for mat in obj.data.materials:
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=atlas
    node.name='Portable albedo atlas';mat.node_tree.nodes.active=node;node.select=True
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False
scene.render.bake.use_pass_color=True;scene.render.bake.margin=3
bpy.ops.object.bake(type='DIFFUSE')
(ROOT/'textures').mkdir(exist_ok=True)
atlas.filepath_raw=str(ROOT/'textures'/'brown_ghost_albedo.png');atlas.file_format='PNG';atlas.save();atlas.pack()
for mat in obj.data.materials:
    n,l=mat.node_tree.nodes,mat.node_tree.links
    uv=n.new('ShaderNodeUVMap');uv.uv_map='Portable color atlas'
    image=n['Portable albedo atlas'];l.new(uv.outputs['UV'],image.inputs['Vector'])
    p=n.get('Principled BSDF')
    l.new(image.outputs['Color'],p.inputs['Base Color'])
# The .blend retains editable procedural nodes and fine bump. GLB receives the atlas.
obj.select_set(True);rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'brown_ghost.glb'),export_format='GLB',use_selection=True,use_active_scene=True,
                          export_animations=True,export_animation_mode='NLA_TRACKS',
                          export_morph=True,export_morph_normal=False,export_morph_tangent=False,
                          export_bake_animation=True,export_force_sampling=True,export_apply=False)
scene['portable_export']='brown_ghost.glb includes skeleton, weights, seven animations and baked albedo.'
scene['materials']='Packed albedo atlas is active; original UV-driven procedural color nodes remain editable.'
references={im for im in bpy.data.images if im.name.startswith('m242')}
bpy.data.libraries.write(str(ROOT/'brown_ghost.blend'),{scene}|references,fake_user=True)
(ROOT/'review'/'export_status.txt').write_text('EXPORTED')
