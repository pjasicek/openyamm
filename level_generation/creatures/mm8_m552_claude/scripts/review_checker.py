"""Inspect the final UV density and deformation with Blender's generated colour grid."""
from pathlib import Path
import bpy
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
mesh=bpy.data.objects['Thunderbird'];rig=bpy.data.objects['Thunderbird_Rig'];scene=bpy.context.scene
material=bpy.data.materials.new('UV checker');material.use_nodes=True
node=material.node_tree.nodes.new('ShaderNodeTexImage')
node.image=bpy.data.images.new('UV grid',width=2048,height=2048)
node.image.generated_type='COLOR_GRID';material.node_tree.nodes.active=node
material.node_tree.links.new(node.outputs['Color'],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
mesh.data.materials.clear();mesh.data.materials.append(material)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='TEXTURE'
scene.display.shading.light='STUDIO';scene.world=bpy.data.worlds.new('ReviewWorld');scene.world.color=(.1,.1,.1)
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(camera)
scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=1.3
for name,time in [('Fly',.25),('Attack',.875)]:
    rig.animation_data.action=bpy.data.actions[name];scene.frame_set(int(time*24),subframe=time*24-int(time*24))
    center=Vector((0,0,.14));camera.location=center+Vector((1.8,-1.2,.65))*3
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(P/'review'/('uv_checker_'+name+'.png'));bpy.ops.render.render(write_still=True)
