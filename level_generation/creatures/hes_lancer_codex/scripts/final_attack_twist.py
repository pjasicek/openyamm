"""Unwrap the attack's half-twist through the hand's 180-degree roll crossing."""
import bpy,sys,os,math,json,runpy
from pathlib import Path
import numpy as np
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];S=P/'scripts';src=P/'work/forge_final_fit.blend'
bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];b=r.pose.bones['B_L_ForearmTwist'];frames=np.arange(a.frame_range[0],a.frame_range[1]+.001,.5);values=[]
for f in frames:
 bpy.context.scene.frame_set(int(f),subframe=float(f%1));q=b.rotation_quaternion.copy()
 if not values:axis=Vector((q.x,q.y,q.z)).normalized()
 values.append((2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi)
angles=np.unwrap(values,period=math.pi);assert np.max(np.abs(np.diff(angles)))<math.radians(15)
for f,angle in zip(frames,angles):
 b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion(axis,float(angle));b.keyframe_insert('rotation_quaternion',frame=float(f))
r.animation_data.action=None;out=P/'work/forge_twist_fit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));(P/'review/forge_twist_continuity.json').write_text(json.dumps({'role':'Forge_Attack','bone':b.name,'before_max_step_degrees':float(np.degrees(np.max(np.abs(np.diff(values))))),'after_max_step_degrees':float(np.degrees(np.max(np.abs(np.diff(angles))))),'sample_hz':60},indent=2)+'\n')
for name,args in [('gates.py',[out,'forge_twist_final','Forge_Attack']),('shell_stretch.py',[out,S/'armour_forge.json','forge_twist_final','Forge_Attack']),('shell_leak.py',[out,S/'armour_forge.json','forge_twist_final','Forge_Attack']),('armour_gate.py',[out,'forge_twist_final',S/'armour_forge.json','Forge_Attack']),('equipment_gate.py',[out,'forge_twist_final','Forge_Attack'])]:
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')

row=json.loads((P/'review/gates_forge_twist_final.json').read_text())['Forge_Attack']
for side in 'LR':
 for suffix,limit in [('arm_p99',2.05),('hand_max',4.5),('wrist_swing',60)]:assert row[side+'_'+suffix]['value']<=limit
 assert row[side+'_hand_in_body']['value']==0
for row in json.loads((P/'review/shell_stretch_forge_twist_final.json').read_text()).values():
 for p99,mx in row.values():assert p99<=1.1 and mx<=1.25
assert not any(json.loads((P/'review/shell_leak_forge_twist_final.json').read_text()).values())
for row in json.loads((P/'review/armour_gate_forge_twist_final.json').read_text()).values():
 for plate in row.values():
  for depth,*_ in plate.values():assert depth<=.30
for row in json.loads((P/'review/equipment_forge_twist_final.json').read_text()).values():
 for entry in row.values():assert not entry['head_intersection_frames'] and entry['floor_min_m']>=-.002
for stem in ('gates','shell_stretch','shell_leak','armour_gate','equipment'):
 target=P/'review'/f'{stem}_{"forge" if stem=="equipment" else "forge_review"}.json';data=json.loads(target.read_text());update=json.loads((P/'review'/f'{stem}_forge_twist_final.json').read_text());assert set(update)=={'Forge_Attack'} and len(data)==9;data.update(update);target.write_text(json.dumps(data,indent=2)+'\n')
import shutil
shutil.copy2(P/'work/forge_twist_fit.blend',P/'work/forge_final_fit.blend')

sys.stdout.flush();os._exit(0)
