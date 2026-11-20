import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01/skirt_clearance');s=bpy.data.scenes['Goblin - Skirt Clearance v3'];bpy.context.window.scene=s;arm=s.objects['Goblin_SkirtClearance_Rig'];mesh=s.objects['Goblin_SkirtClearance_10577'];strips=json.loads((OUT/'strips.json').read_text());raw=json.loads((OUT/'clearance_solution.json').read_text());summary={}
for track in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(track)
for key,frames in raw.items():
 a=bpy.data.actions['Goblin_Skirt_'+key];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];n=len(frames);loop=key in ['Idle_3','Walking','Running'];values=[]
 for i,strip in enumerate(strips):
  angles=[f['degrees'][i] for f in frames]
  def at(j):return angles[j%(n-1)] if loop else angles[min(n-1,max(0,j))]
  peak=[max(at(j+d)-4*abs(d) for d in range(-4,5)) for j in range(n)]
  smooth=[max(at(j),sum(peak[(j+d)%(n-1)] if loop else peak[min(n-1,max(0,j+d))] for d in [-1,0,1])/3)+1.5 for j in range(n)]
  if loop:smooth[-1]=smooth[0]
  values.append(smooth)
 for j,fr in enumerate(frames):
  s.frame_set(fr['frame'])
  for i,strip in enumerate(strips):
   pb=arm.pose.bones[strip['name']];axis=pb.bone.matrix_local.to_quaternion().inverted()@Vector(strip['axis']);pb.rotation_quaternion=Quaternion(axis,math.radians(values[i][j]));pb.location=(0,0,0);pb.scale=(1,1,1)
   for prop in ['rotation_quaternion','location','scale']:pb.keyframe_insert(data_path=prop,frame=fr['frame'],group=pb.name)
 for layer in a.layers:
  for st in layer.strips:
   bag=st.channelbag(a.slots[0])
   if bag:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 summary[key]={'max_angle':max(max(x) for x in values),'raw_worst_clearance_m':min(min(f['clearances']) for f in frames),'frames':n}
 track=arm.animation_data.nla_tracks.new();track.name=key;st=track.strips.new(key,int(a.frame_range[0]),a);st.action_slot=a.slots[0];track.mute=True
(OUT/'bake_report.json').write_text(json.dumps(summary,indent=2));jobs=[('Walking',15,'walk_15'),('Walking',3,'walk_03'),('Running',5,'run_05'),('Idle_3',61,'idle'),('Right_Hand_Sword_Slash',23,'slash')]
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   a=bpy.data.actions['Goblin_Skirt_Walking'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_start=1;s.frame_end=26;s.frame_set(15);bpy.data.libraries.write(str(OUT/'skirt_working.blend'),{s},fake_user=True,compress=True);(OUT/'bake_done.txt').write_text('complete');return None
  key,f,name=jobs.pop(0);a=bpy.data.actions['Goblin_Skirt_'+key];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_set(f);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'bake_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(summary))
