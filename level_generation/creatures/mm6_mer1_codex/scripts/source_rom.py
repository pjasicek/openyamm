import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_clips.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;out={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];v=[]
 for f in range(int(a.frame_range[0]),int(a.frame_range[1])+1):
  sc.frame_set(f);row={'frame':f,'pelvis_z':r.pose.bones['B_Pelvis'].head.z}
  for s in ['L','R']:
   u,e,w=[r.pose.bones[f'B_{s}_{b}'].head for b in ['UpperArm','Forearm','Hand']]
   row[s+'_elbow']=math.degrees((e-u).angle(w-e));row[s+'_wrist']=math.degrees(r.pose.bones[f'B_{s}_Hand'].rotation_quaternion.angle)
  v.append(row)
 out[name]={'duration':(a.frame_range[1]-a.frame_range[0])/sc.render.fps,'frames':v,'extremes':{k:{'min':min(v,key=lambda x:x[k]),'max':max(v,key=lambda x:x[k])}for k in ['L_elbow','R_elbow','L_wrist','R_wrist']}}
assert len(out)==7 and all(len(x['frames'])>1 for x in out.values())
(P/'work/source_rom.json').write_text(json.dumps(out,indent=2))
print('ROM source ranges saved')
