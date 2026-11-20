"""Match native projected alpha area over a complete flight cycle, excluding transient FX."""
import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Standing'];bpy.data.objects['MouthFire'].hide_render=True
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.render.film_transparent=True;sc.render.resolution_x=512;sc.render.resolution_y=512;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('AreaCamera',bpy.data.cameras.new('AreaCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.2
out=P/'review/scale';out.mkdir(exist_ok=True)
for view,d in [('front',(0,-1,0)),('side',(1,0,0))]:
 target=Vector((0,0,.30));cam.location=target+Vector(d)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 for i in range(11):
  sc.frame_set(i*3);sc.render.filepath=str(out/f'{view}_{i:02d}.png');bpy.ops.render.render(write_still=True)
(out/'projection.json').write_text(json.dumps({'ortho_scale':1.2,'resolution':512,'source_scale_adult':5,'source_scale_small':4,'samples':11,'fps':24,'frames_per_sample':3})+'\n')
