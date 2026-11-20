"""Close shoulder views of the corrected authoring scene in the existing seven authored clips."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/dragon_hunter_final.blend'))
body=bpy.data.objects['DragonHunter'];me=body.data;rig=bpy.data.objects['Rig'];sc=bpy.context.scene
common.workbench_clay(sc,True);sc.render.resolution_x=640;sc.render.resolution_y=640
out=p/'review/shoulder_repair/poses';out.mkdir(parents=True,exist_ok=True)
for name,frames in [('Standing',[0]),('Running',[5,11,16]),('Attack',[4,10,16]),('Hit',[7]),('Fidget',[22,43,64]),('Walking',[8,22]),('Death',[30,65])]:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f in frames:
  sc.frame_set(f*4);c=rig.pose.bones['B_Spine2'].head.copy();c.z-=.02
  for view,a in [('rear_left',125),('rear_right',-125),('front_left',60)]:
   rad=math.radians(a);cam=common.ortho_camera('review',(c.x+math.sin(rad)*5,c.y-math.cos(rad)*5,c.z+.08),(0,0,0),.65);cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(out/f'{name}_{f}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
