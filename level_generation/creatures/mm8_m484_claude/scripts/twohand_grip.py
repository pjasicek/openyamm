import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gated_master.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'};out={}
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];errors={s:0. for s in 'RL'};spacing=[];worst={};keymax=0.
 for f in np.arange(0,a.frame_range[1]+.01,.25):
  sc.frame_set(int(f),subframe=float(f%1));M=r.pose.bones['Axe'].matrix@r.data.bones['Axe'].matrix_local.inverted();origin=M@Vector((0,0,.24));axis=(M.to_3x3()@Vector((0,0,1))).normalized()
  for sd in 'RL':
   c=r.pose.bones[f'B_{sd}_Hand'].matrix@Vector(G[sd]['handle_centre_hand_local']);d=c-origin;radial=(d-axis*d.dot(axis)).length;
   if radial>errors[sd]:errors[sd]=radial;worst[sd]=float(f)
   if f%0.5==0:keymax=max(keymax,radial)
   if sd=='L':spacing.append(d.dot(axis))
 out[role]={'max_radial_grip_error_m':errors,'left_grip_spacing_m':[min(spacing),max(spacing)],'sample_fps':120,'worst_frames':worst,'key_max_m':keymax}
 print('GRIP',out[role],flush=True)
 # The thick shaft stays inside the closed grip between 60-fps keys; retain the measured interpolation drift.
 assert keymax<.00001 and max(errors.values())<.006,out[role]
 assert min(spacing)>.20 and max(spacing)<.36,out[role]
print('GRIP',out);(P/'review/twohand_grip.json').write_text(json.dumps(out,indent=2))
