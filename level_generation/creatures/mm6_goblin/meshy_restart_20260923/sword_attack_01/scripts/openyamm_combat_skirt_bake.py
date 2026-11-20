import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;arm=s.objects['Goblin_Combat_Rig'];mesh=s.objects['Goblin_Combat_Body'];strips=json.loads((OUT/'strips.json').read_text());raw=json.loads((OUT/'clearance_solution.json').read_text());summary={}
for track in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(track)
for key,frames in raw.items():
 a=bpy.data.actions['MM6_Goblin_'+key]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if fc.data_path.startswith('pose.bones["Skirt_'):bag.fcurves.remove(fc)
 arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];n=len(frames);loop=key in ['Idle','Walk','Run'];values=[]
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
(OUT/'skirt_bake_report.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
