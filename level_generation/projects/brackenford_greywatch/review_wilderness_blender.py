"""One native reimport through Blender MCP for the automap and wilderness composition views."""
from pathlib import Path
import bpy
from mathutils import Vector

project=Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
previous_name=bpy.context.window.scene.name
try:
    exec(compile((project/'build_minimap_blender.py').read_text(),str(project/'build_minimap_blender.py'),'exec'))
    scene.render.image_settings.file_format='PNG'
    scene.render.resolution_x=1440;scene.render.resolution_y=1080
    for name,target,position,scale in [
        ('wilderness_region',(0,0,1000),(36000,-52000,78000),64000),
        ('wilderness_north',(-11000,18700,1300),(-19000,8000,13000),22000),
        ('wilderness_southeast',(15500,-17700,1900),(24500,-26500,13000),21000),
        ('wilderness_pond',(-512,17920,512),(2000,13000,5500),7500),
        ('wilderness_bridge',(5376,256,640),(8000,-3800,3000),6600),
        ('wilderness_den',(15360,-16640,1700),(18500,-21500,4300),6900)]:
        camera.location=Vector(position)/128
        camera.rotation_euler=(Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale/128
        for obj in billboards:
            obj.hide_render=False
            direction=camera.location-obj.location;direction.z=0
            obj.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
        scene.render.filepath=str(project/'review'/('brackenford_native_'+name+'.png'))
        bpy.ops.render.render(write_still=True)
finally:
    previous_scene=bpy.data.scenes.get(previous_name)
    if previous_scene:bpy.context.window.scene=previous_scene
print('Wilderness views and native automap saved.')
