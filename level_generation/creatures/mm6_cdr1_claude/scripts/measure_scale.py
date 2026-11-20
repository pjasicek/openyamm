import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Walking'];sc.render.engine='BLENDER_WORKBENCH';sc.render.film_transparent=True;sc.render.resolution_x=1024;sc.render.resolution_y=1024;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('MeasureCamera',bpy.data.cameras.new('MeasureCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.8;cam.location=(0,-6,.9);cam.rotation_euler=(Vector((0,0,.9))-cam.location).to_track_quat('-Z','Y').to_euler()
areas=[]
for f in [0,4.5,9,13.5,18,22.5]:
 sc.frame_set(int(f),subframe=f%1);file=P/'review/scale'/f'scale_{f:04.1f}.png';sc.render.filepath=str(file);bpy.ops.render.render(write_still=True);im=bpy.data.images.load(str(file));pix=np.array(im.pixels[:]).reshape(1024,1024,4);areas.append(float((pix[:,:,3]>.5).sum())*(3.8/1024)**2);bpy.data.images.remove(im)
(P/'review/scale/model_area.json').write_text(json.dumps({'model_area_m2':areas,'mean':float(np.mean(areas))},indent=2));print('AREAS',areas)
