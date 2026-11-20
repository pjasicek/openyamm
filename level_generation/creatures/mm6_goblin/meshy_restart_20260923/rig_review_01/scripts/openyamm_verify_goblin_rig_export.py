import bpy,json,traceback,math
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01');frames=OUT/'preview_frames';frames.mkdir(exist_ok=True);original=bpy.data.scenes['Goblin - Meshy Rig Diagnosis'];origarm=next(o for o in original.objects if o.type=='ARMATURE');final=next(s for s in reversed(list(bpy.data.scenes)) if s.name.startswith('Goblin - Repaired Rig Review'))
v=bpy.data.scenes.new('Goblin - Repaired Export Verified');v.render.fps=24;bpy.context.window.scene=v;before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(OUT/'mm6_goblin_10577_rig_repaired.glb'));newactions=[a for a in bpy.data.actions if a not in before];arm=next(o for o in v.objects if o.type=='ARMATURE');mesh=max((o for o in v.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));
for o in v.objects:
 if o.type=='MESH' and o!=mesh:o.hide_render=True
for t in arm.animation_data.nla_tracks:t.mute=True
v.render.engine='CYCLES';v.cycles.samples=16;v.cycles.device='CPU';v.cycles.use_denoising=True;v.world=original.world;v.view_settings.view_transform='AgX';v.render.resolution_x=850;v.render.resolution_y=1000;v.render.resolution_percentage=100;v.render.image_settings.file_format='PNG'
for o in original.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();v.collection.objects.link(cp)
  if cp.type=='CAMERA':v.camera=cp
report={'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'bones':len(arm.data.bones),'actions':[{'name':a.name,'frame_range':list(a.frame_range)} for a in newactions]};assert report['triangles']==10577;assert len(newactions)==5;(OUT/'reimport_report.json').write_text(json.dumps(report,indent=2))
jobs=[('still','Idle_3',.25,'fixed'),('still','Right_Hand_Sword_Slash',.6,'fixed')]
for key in ['Walking','Right_Hand_Sword_Slash']:
 for i in range(12):
  for variant in ['original','fixed']:jobs.append(('loop',key,i/12,variant))

def step():
 try:
  if not jobs:
   bpy.context.window.scene=final;(OUT/'preview_done.txt').write_text('complete');return None
  mode,key,t,variant=jobs.pop(0);sc=original if variant=='original' else v;ar=origarm if variant=='original' else arm;actions=list(bpy.data.actions) if variant=='original' else newactions;a=next(a for a in actions if a.name==key) if variant=='original' else next(a for a in actions if ('Goblin_Fixed_'+key) in a.name)
  bpy.context.window.scene=sc;ar.data.pose_position='POSE';ar.animation_data.action=a;ar.animation_data.action_slot=a.slots[0]
  f=a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0]);sc.frame_set(int(f),subframe=f-int(f));sc.view_layers[0].material_override=None
  if mode=='still':sc.render.resolution_x=850;sc.render.resolution_y=1000;sc.cycles.samples=16;sc.render.filepath=str(OUT/('export_'+key+'.png'))
  else:sc.render.resolution_x=425;sc.render.resolution_y=500;sc.cycles.samples=6;sc.render.filepath=str(frames/(key+'_'+variant+'_'+str(round(t*12)).zfill(2)+'.png'))
  (OUT/'preview_progress.txt').write_text(mode+' '+key+' '+variant+' '+str(t));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'preview_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(report))
