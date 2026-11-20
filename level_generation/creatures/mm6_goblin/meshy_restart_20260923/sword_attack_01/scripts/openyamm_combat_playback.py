import bpy,json,traceback,math
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];frames=OUT/'playback';frames.mkdir(exist_ok=True);s.render.resolution_x=480;s.render.resolution_y=540;s.cycles.samples=8;s.camera.data.ortho_scale=2.65;jobs=[]
for view,angle in [('front',0),('quarter',.65)]:
 for f in range(1,20):jobs.append(('MM6_Goblin_Attack',f,'attack_'+view+'_%02d'%f,angle))
for f in [1,7,13,20]:jobs.append(('MM6_Goblin_Walk',f,'walk_%02d'%f,0))
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   a=bpy.data.actions['MM6_Goblin_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_start=1;s.frame_end=19;s.frame_set(4);(OUT/'playback_done.txt').write_text('complete');return None
  key,f,name,angle=jobs.pop(0);a=bpy.data.actions[key];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(f);s.camera.location=(5*math.sin(angle),-5*math.cos(angle),.98);s.camera.rotation_euler=(Vector((0,0,.98))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(frames/(name+'.png'));(OUT/'playback_progress.txt').write_text(name);bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'playback_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Rendering front/oblique attack playback and armed locomotion poses')
