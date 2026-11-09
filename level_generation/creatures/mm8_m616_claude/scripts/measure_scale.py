"""Front-flight alpha area calibration, without an added hover translation."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['BoneDragon_Rig'];mesh=bpy.data.objects['BoneDragon']
rig.animation_data.action=bpy.data.actions['Fly']
scene.render.engine='BLENDER_WORKBENCH';scene.render.film_transparent=True
scene.render.resolution_x=scene.render.resolution_y=1024;scene.render.resolution_percentage=100
cam=bpy.data.objects.new('ScaleCamera',bpy.data.cameras.new('ScaleCamera'));scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=1.4
center=Vector((0,0,.40));cam.location=center+Vector((0,-3,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
areas=[];bounds=[]
(P/'review/scale').mkdir(exist_ok=True)
for frame in range(0,24,3):
 scene.frame_set(frame);scene.render.filepath=str(P/f'review/scale/front_{frame:02}.png');bpy.ops.render.render(write_still=True)
 image=bpy.data.images.load(scene.render.filepath);pixels=np.array(image.pixels[:]).reshape(1024,1024,4);areas.append(float((pixels[:,:,3]>.5).sum())*(1.4/1024)**2);bpy.data.images.remove(image)
 co=np.array([tuple(v.co) for v in mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]);bounds.append([co.min(0).tolist(),co.max(0).tolist()])
(P/'work/model_flight_area.json').write_text(json.dumps(dict(front_area_m2=areas,bounds=bounds),indent=2)+'\n')
