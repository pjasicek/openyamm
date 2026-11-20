"""Offline CPU review of the returned props and their painted materials."""
import bpy, math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipment_meshy.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12
s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100;s.world.color=(.2,.2,.2)
s.view_settings.view_transform='Standard'
for o in list(s.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
for pos,power,size in [((-2,-3,3),400,3),((2,2,2),280,3)]:
 d=bpy.data.lights.new('PaintReview','AREA');d.energy=power;d.size=size;o=bpy.data.objects.new('PaintReview',d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.15))-o.location).to_track_quat('-Z','Y').to_euler()
c=bpy.data.cameras.new('PaintReviewCamera');cam=bpy.data.objects.new('PaintReviewCamera',c);s.collection.objects.link(cam);s.camera=cam;c.type='ORTHO'
for part in ['pulse_pistol','collar_rod','arc_maul']:
 obj=bpy.data.objects['OV_'+part]
 for o in s.objects:
  if o.type=='MESH':o.hide_render=o!=obj
 lo=Vector(tuple(min(v.co[i] for v in obj.data.vertices) for i in range(3)));hi=Vector(tuple(max(v.co[i] for v in obj.data.vertices) for i in range(3)));target=(lo+hi)/2
 c.ortho_scale=max(hi-lo)*1.22;cam.location=target+Vector((3,-4,2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(P/'review'/f'painted_{part}.png');bpy.ops.render.render(write_still=True)
