"""Limit the cast carry's wrist swing while preserving its grip, arm pose and library gesture."""
import bpy,sys,os,math,runpy,json
from pathlib import Path
import numpy as np
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
src=P/'work/forge_final_fit.blend';bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];a=bpy.data.actions['Forge_Cast'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];hand=r.data.bones['B_R_Hand'];fore=r.data.bones['B_R_Forearm'];axis=(hand.matrix_local.to_3x3().inverted()@(hand.head_local-fore.head_local)).normalized();keys=[]
for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
 bpy.context.scene.frame_set(int(f),subframe=float(f%1));b=r.pose.bones[hand.name];q=b.matrix_basis.to_quaternion();swing,twist=armik.split_swing_twist(q,axis)
 if swing.w<0:swing=-swing
 q=Quaternion(swing.axis,min(swing.angle,math.radians(59)))@Quaternion(axis,twist);keys.append((float(f),q))
previous=None
for f,q in keys:
 if previous is not None and q.dot(previous)<0:q=-q
 previous=q.copy();b=r.pose.bones[hand.name];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(src))
for name,args in [('gates.py',[src,'forge_cast_final','Forge_Cast']),('shell_stretch.py',[src,S/'armour_forge.json','forge_cast_final','Forge_Cast']),('shell_leak.py',[src,S/'armour_forge.json','forge_cast_final','Forge_Cast']),('armour_gate.py',[src,'forge_cast_final',S/'armour_forge.json','Forge_Cast']),('equipment_gate.py',[src,'forge_cast_final','Forge_Cast'])]:
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
for stem in ('gates','shell_stretch','shell_leak','armour_gate','equipment'):
 target=P/'review'/f'{stem}_{"forge" if stem=="equipment" else "forge_review"}.json';data=json.loads(target.read_text());update=json.loads((P/'review'/f'{stem}_forge_cast_final.json').read_text());assert set(update)=={'Forge_Cast'} and len(data)==9;data.update(update);target.write_text(json.dumps(data,indent=2)+'\n')
sys.stdout.flush();os._exit(0)
