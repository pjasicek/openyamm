"""Unwrap the attack's half-twist through the hand's 180-degree roll crossing."""
import bpy,sys,os,math,json,runpy
from pathlib import Path
import numpy as np
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];S=P/'scripts';src=P/'work/forge_final_clearance.blend'
bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];b=r.pose.bones['B_L_ForearmTwist'];frames=np.arange(a.frame_range[0],a.frame_range[1]+.001,.5);values=[]
for f in frames:
 bpy.context.scene.frame_set(int(f),subframe=float(f%1));q=b.rotation_quaternion.copy()
 if not values:axis=Vector((q.x,q.y,q.z)).normalized()
 values.append((2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi)
angles=np.unwrap(values,period=math.pi);assert np.max(np.abs(np.diff(angles)))<math.radians(15)
for f,angle in zip(frames,angles):
 b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion(axis,float(angle));b.keyframe_insert('rotation_quaternion',frame=float(f))
r.animation_data.action=None;out=P/'work/forge_concept_twist.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));(P/'review/forge_twist_continuity_concept.json').write_text(json.dumps({'role':'Forge_Attack','bone':b.name,'before_max_step_degrees':float(np.degrees(np.max(np.abs(np.diff(values))))),'after_max_step_degrees':float(np.degrees(np.max(np.abs(np.diff(angles))))),'sample_hz':60},indent=2)+'\n')

for name,args in [('gates.py',[out,'forge_concept_twist','Forge_Attack']),('shell_stretch.py',[out,S/'armour_forge_concept.json','forge_concept_twist','Forge_Attack']),('shell_leak.py',[out,S/'armour_forge_concept.json','forge_concept_twist','Forge_Attack']),('armour_gate.py',[out,'forge_concept_twist',S/'armour_forge_concept.json','Forge_Attack']),('equipment_gate.py',[out,'forge_concept_twist','Forge_Attack'])]:
 os.environ['FSTEP']='.5';sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
# All other clips are untouched; finish_forge.py asserts the merged nine-role bundle before export.
for stem in ('gates','shell_stretch','shell_leak','armour_gate','equipment'):
 target=P/'review'/f'{stem}_forge_concept.json';data=json.loads(target.read_text());update=json.loads((P/'review'/f'{stem}_forge_concept_twist.json').read_text());assert set(update)=={'Forge_Attack'} and len(data)==9;data.update(update);target.write_text(json.dumps(data,indent=2)+'\n')
import shutil
shutil.copy2(out,P/'work/forge_final_clearance.blend')
sys.stdout.flush();os._exit(0)
