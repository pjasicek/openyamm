"""Written-ODM outer-road views and automap from one MCP import."""
from pathlib import Path
import bpy
from mathutils import Vector
project=Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
previous=bpy.context.scene.name
try:
    exec(compile((project/'build_minimap_blender.py').read_text(),'build_minimap_blender.py','exec'))
    scene.render.image_settings.file_format='PNG';scene.render.resolution_x=1440;scene.render.resolution_y=1080
    for name,target,position,scale in [
        ('west',(-28000,-800,1500),(-21000,-8500,14000),16000),
        ('north',(-17500,28200,1800),(-8500,21000,15000),16000),
        ('region',(0,0,1000),(36000,-52000,78000),76000)]:
        camera.location=Vector(position)/128
        camera.rotation_euler=(Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale/128
        for obj in billboards:
            obj.hide_render=False;direction=camera.location-obj.location;direction.z=0
            obj.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
        scene.render.filepath=str(project/'review'/('brackenford_native_transition_'+name+'.png'))
        bpy.ops.render.render(write_still=True)
finally:
    if bpy.data.scenes.get(previous):bpy.context.window.scene=bpy.data.scenes[previous]
print('Native transition review and automap saved')
