import bpy,json,traceback,math
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01');audit=OUT/'upright_audit';final=bpy.data.scenes['Goblin - Upright Rig Review'];source=bpy.data.scenes['Goblin - Posture Alignment v2'];srcarm=source.objects['MM6_Goblin_Upright_Rig']
v=bpy.data.scenes.new('Goblin - Upright Export Verified');v.render.fps=24;bpy.context.window.scene=v;before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(OUT/'mm6_goblin_10577_rig_upright_v2.glb'));actions=[a for a in bpy.data.actions if a not in before];arm=next(o for o in v.objects if o.type=='ARMATURE');mesh=next(o for o in v.objects if o.type=='MESH')
for t in arm.animation_data.nla_tracks:t.mute=True
v.render.engine='CYCLES';v.cycles.samples=12;v.cycles.device='CPU';v.cycles.use_denoising=True;v.world=final.world;v.view_settings.view_transform='AgX';v.render.resolution_x=680;v.render.resolution_y=800;v.render.resolution_percentage=100;v.render.image_settings.file_format='PNG'
for o in final.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();v.collection.objects.link(cp)
  if cp.type=='CAMERA':v.camera=cp
report={'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'joints':len(arm.data.bones),'actions':[{'name':a.name,'frames':list(a.frame_range)} for a in actions],'max_joint_roundtrip_distance_m':0}
assert report['triangles']==10577 and report['joints']==28 and len(actions)==5
for a in actions:
 key=next(k for k in ['Idle_3','Walking','Running','Right_Hand_Sword_Slash','restpose'] if 'Goblin_Upright_'+k in a.name);original=bpy.data.actions['Goblin_Upright_'+key];srcarm.animation_data.action=original;srcarm.animation_data.action_slot=original.slots[0];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0]
 for i in range(12):
  t=i/11;f=original.frame_range[0]+t*(original.frame_range[1]-original.frame_range[0]);bpy.context.window.scene=source;source.frame_set(int(f),subframe=f-int(f));g=a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0]);bpy.context.window.scene=v;v.frame_set(int(g),subframe=g-int(g))
  for b in arm.pose.bones:
   distance=((arm.matrix_world@b.head)-(srcarm.matrix_world@srcarm.pose.bones[b.name].head)).length;report['max_joint_roundtrip_distance_m']=max(report['max_joint_roundtrip_distance_m'],distance)
assert report['max_joint_roundtrip_distance_m']<.00001, report
(audit/'export_verification.json').write_text(json.dumps(report,indent=2))
jobs=[('Idle_3','before',.25),('Idle_3','after',.25),('Walking','before',.25),('Walking','after',.25),('Right_Hand_Sword_Slash','after',.6)]
def step():
 try:
  bpy.context.window.scene=v
  if not jobs:
   bpy.context.window.scene=final;(audit/'verify_done.txt').write_text('complete');return None
  key,variant,t=jobs.pop(0)
  for pb in arm.pose.bones:pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
  a=bpy.data.actions['Goblin_Fixed_'+key] if variant=='before' else next(a for a in actions if 'Goblin_Upright_'+key in a.name);arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];f=a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0]);v.frame_set(int(f),subframe=f-int(f));v.render.filepath=str(audit/(key+'_'+variant+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(audit/'verify_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(report))
