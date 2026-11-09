"""Compare the reported attack frame and shoulder caps against the preserved revision."""
import bpy,sys,math,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'review/arm_pad_repair/poses';out.mkdir(parents=True,exist_ok=True)
for label,file in [('before',p/'review/arm_pad_repair/before/dragon_hunter_final.blend'),('after',p/'work/dragon_hunter_final.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(file));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
 common.workbench_clay(sc,True);sc.render.resolution_x=600;sc.render.resolution_y=600
 for name,times in [('Standing',[0]),('Running',[0,.18,.36,.55]),('Attack',[.15,.3,22/48,.65]),('Hit',[.23]),('Fidget',[.7,1.4,2.1]),('Death',[1,2.16])]:
  a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
  for t in times:
   f=t*120;sc.frame_set(int(f),subframe=f%1);c=rig.pose.bones['B_Spine2'].head.copy();c.z-=.10
   for view,angle in [('front',0),('back',180),('right',-90)]:
    rad=math.radians(angle);cam=common.ortho_camera('review',(c.x+math.sin(rad)*5,c.y-math.cos(rad)*5,c.z+.1),(0,0,0),.9);cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(out/f'{label}_{name}_{t:.3f}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
