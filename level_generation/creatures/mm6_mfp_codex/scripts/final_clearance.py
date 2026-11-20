"""Unwrap helper roll before distributing it; fit hidden legs against final timed clips."""
import bpy,sys,json,math,os,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from gates_summary import summarize
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_polished.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];name='B_R_UpperArmTwist';base='B_R_UpperArm';ub=r.data.bones[base];axis=(ub.matrix_local.inverted()@r.data.bones['B_R_Forearm'].head_local).normalized();frames=np.linspace(0,a.frame_range[1],math.ceil(a.frame_range[1]*120/30)+1);raw=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));q=r.pose.bones[base].matrix_basis.to_quaternion();raw.append((2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi)
angles=np.unwrap(raw);print('TWIST_UNWRAP',np.degrees([min(raw),max(raw),angles[0],angles[-1],angles.min(),angles.max()]).tolist(),flush=True)
for l in a.layers:
 for st in l.strips:
  for bag in st.channelbags:
   for fc in list(bag.fcurves):
    if fc.data_path==f'pose.bones["{name}"].rotation_quaternion':bag.fcurves.remove(fc)
prev=None
for f,angle in zip(frames,angles):
 q=Quaternion(axis,-.5*angle)
 if prev and q.dot(prev)<0:q=-q
 prev=q;p=r.pose.bones[name];p.rotation_quaternion=q;p.keyframe_insert('rotation_quaternion',frame=float(f))
for l in a.layers:
 for st in l.strips:
  for bag in st.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_polished.blend'))
runpy.run_path(str(P/'scripts/propagate_polished.py'),run_name='__main__')
sel=json.loads((P/'review/reduction_soft/selection.json').read_text());results={}
for level,row in sel.items():
 path=P/row['blend'];report=P/f'review/final_fit_lod{level}.json';os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(report),GATE_RENDER='0',FIT_CLOTH='1',FIT_MAX_M='.03')
 for iteration in range(3):
  runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');d=json.loads(report.read_text());print('FINAL_FIT',level,iteration,summarize(d),flush=True)
  if max(x['cloth_mm']for x in d['clips'].values())<=1.2:break
 results[level]=summarize(d)
os.environ['FIT_CLOTH']='0';(P/'review/final_fit_summary.json').write_text(json.dumps(results,indent=2))
