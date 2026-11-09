"""One written-ODM reimport for full crossing, town-side coverage, native landmarks and automap."""
from pathlib import Path
import bpy
from mathutils import Vector
project=Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
previous_name=bpy.context.window.scene.name
try:
    exec(compile((project/'build_minimap_blender.py').read_text(),str(project/'build_minimap_blender.py'),'exec'))
    scene.render.image_settings.file_format='PNG';scene.render.resolution_x=1440;scene.render.resolution_y=1080
    for name,target,position,scale in [
        ('landscape_bridge',(5376,256,1100),(8000,-4500,4400),8200),
        ('landscape_meadow',(-3200,5000,1300),(7000,-7000,13000),19000),
        ('landscape_town',(-11800,-1800,700),(-7000,-12500,13500),17000),
        ('landscape_challenge',(-2048,10752,1750),(1200,7100,5400),6100),
        ('landscape_camp',(20600,1950,1200),(23600,-2200,4800),5500),
        ('landscape_region',(0,0,1000),(36000,-52000,78000),64000)]:
        camera.location=Vector(position)/128
        camera.rotation_euler=(Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale/128
        for obj in billboards:
            obj.hide_render=False;direction=camera.location-obj.location;direction.z=0
            obj.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
        scene.render.filepath=str(project/'review'/('brackenford_native_'+name+'.png'))
        bpy.ops.render.render(write_still=True)
finally:
    if bpy.data.scenes.get(previous_name):bpy.context.window.scene=bpy.data.scenes[previous_name]
print('Landscape views and native automap saved.')
