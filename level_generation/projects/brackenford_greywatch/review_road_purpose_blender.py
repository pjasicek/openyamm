"""Written-map review of off-road cave/camps and retained castle/regional routes."""
from pathlib import Path
import bpy
from mathutils import Vector
p=Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch');previous=bpy.context.scene.name
try:
    exec(compile((p/'build_minimap_blender.py').read_text(),'build_minimap_blender.py','exec'))
    scene.render.image_settings.file_format='PNG';scene.render.resolution_x=1440;scene.render.resolution_y=1080
    for name,target,position,scale in [
        ('east',(18100,4400,1200),(27000,-5000,17000),19000),
        ('south',(12800,-15500,1400),(23000,-27000,22000),24500)]:
        camera.location=Vector(position)/128
        camera.rotation_euler=(Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale/128
        for obj in billboards:
            obj.hide_render=False;direction=camera.location-obj.location;direction.z=0
            obj.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
        scene.render.filepath=str(p/'review'/('brackenford_native_offroad_'+name+'.png'))
        bpy.ops.render.render(write_still=True)
finally:
    if bpy.data.scenes.get(previous):bpy.context.window.scene=bpy.data.scenes[previous]
print('Updated minimap and off-road wilderness views saved')
