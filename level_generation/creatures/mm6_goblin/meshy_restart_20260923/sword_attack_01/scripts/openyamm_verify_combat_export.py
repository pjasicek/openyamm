import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');src=bpy.data.scenes['Goblin - Sword and Native Attack'];sr=src.objects['Goblin_Combat_Rig'];sm=src.objects['Goblin_Combat_Body'];s=bpy.data.scenes.new('Goblin - Combat Export Verified');s.render.fps=48;bpy.context.window.scene=s;before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(OUT/'mm6_goblin_corsair_attack.glb'));actions=[a for a in bpy.data.actions if a not in before];r=next(o for o in s.objects if o.type=='ARMATURE');m=max((o for o in s.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
for tr in r.animation_data.nla_tracks:tr.mute=True
report={'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH'),'bones':len(r.data.bones),'clips':[{'name':a.name,'frame_range':list(a.frame_range),'seconds':(a.frame_range[1]-a.frame_range[0])/48} for a in actions]};assert report['triangles']==12073 and report['bones']==61 and len(actions)==5
kd=KDTree(len(sm.data.vertices))
for v in sm.data.vertices:kd.insert(sm.matrix_world@v.co,v.index)
kd.balance();mapping=[];resterr=0
for v in m.data.vertices:
 _,idx,d=kd.find(m.matrix_world@v.co);mapping.append(idx);resterr=max(resterr,d)
report['max_rest_vertex_distance_m']=resterr;assert resterr<.00001;worstbone=0;worstskin=0;perclip={};weighted=set()
for o in s.objects:
 if o.type=='MESH':
  for v in o.data.vertices:
   for g in v.groups:
    if g.weight>.000001:weighted.add(o.vertex_groups[g.group].name)
for a in actions:
 key=next(k for k in ['Idle','Walk','Run','Attack','GripRest'] if a.name.startswith('MM6_Goblin_'+k));orig=bpy.data.actions['MM6_Goblin_'+key];sr.animation_data.action=orig;sr.animation_data.action_slot=orig.slots[0];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];cliperr=0
 for i in range(9):
  t=i/8;f=round(orig.frame_range[0]+t*(orig.frame_range[1]-orig.frame_range[0]));bpy.context.window.scene=src;src.frame_set(int(f),subframe=f-int(f));joints={p.name:sr.matrix_world@p.head for p in sr.pose.bones};ev=sm.evaluated_get(bpy.context.evaluated_depsgraph_get());points=[ev.matrix_world@v.co for v in ev.data.vertices];g=round(a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0]));bpy.context.window.scene=s;s.frame_set(int(g),subframe=g-int(g));ev=m.evaluated_get(bpy.context.evaluated_depsgraph_get())
  for p in r.pose.bones:
   if p.name in weighted:worstbone=max(worstbone,((r.matrix_world@p.head)-joints[p.name]).length)
  for j,v in enumerate(ev.data.vertices):cliperr=max(cliperr,((ev.matrix_world@v.co)-points[mapping[j]]).length)
 perclip[key]=cliperr;worstskin=max(worstskin,cliperr)
report['maximum_weighted_joint_roundtrip_error_m']=worstbone;report['maximum_skin_roundtrip_error_m']=worstskin;report['skin_errors_by_clip_m']=perclip;(OUT/'export_verification.json').write_text(json.dumps(report,indent=2));assert worstbone<.00003 and worstskin<.00005, report
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=src.world;s.view_settings.view_transform='AgX';s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
for o in src.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
jobs=[(7,'export_windup'),(25,'export_followthrough')]
def step():
 try:
  if not jobs:
   bpy.context.window.scene=src;a=bpy.data.actions['MM6_Goblin_Attack'];sr.animation_data.action=a;sr.animation_data.action_slot=a.slots[0];src.frame_start=1;src.frame_end=37;src.frame_set(7);(OUT/'export_review_done.txt').write_text('complete');return None
  bpy.context.window.scene=s;f,name=jobs.pop(0);a=next(a for a in actions if 'MM6_Goblin_Attack' in a.name);r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(f);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'export_review_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(report))
