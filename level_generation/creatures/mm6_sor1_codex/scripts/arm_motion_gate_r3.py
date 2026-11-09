"""Both-arm wrist anatomy and angular acceleration at 48 Hz, on the actual played pose."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
args=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=str(p/args[0]));tag=args[1]
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
from arm_solver import swing_twist_deg
# A 10-degree alternating orientation error at 48 Hz exceeds the acceleration limit; uniform turns do not.
def rv(q):
 if q.w<0:q=-q
 v=Vector((q.x,q.y,q.z));return np.array(v)*((2*math.atan2(v.length,q.w)/v.length) if v.length>1e-8 else 2)
def acceleration(q):
 vel=np.array([rv(b@a.inverted()) for a,b in zip(q,q[1:])])*48
 return np.linalg.norm(np.diff(vel,axis=0),axis=1)*48*180/math.pi
assert max(acceleration([Quaternion((1,0,0),math.radians(10*(-1)**i)) for i in range(10)]))>20000
assert max(acceleration([Quaternion((1,0,0),math.radians(i*2)) for i in range(10)]))<1
report={}
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 quats={s+'_'+b:[] for s in 'LR' for b in ['UpperArm','Forearm','Hand']};wrists={s:[] for s in 'LR'}
 for t in np.arange(0,float(act.frame_range[1])/scene.render.fps+1e-6,1/48):
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=float(f%1))
  for key in quats:quats[key].append(rig.pose.bones['B_'+key].matrix.to_quaternion())
  for s in 'LR':
   F,H=[rig.pose.bones[f'B_{s}_{b}'] for b in ['Forearm','Hand']];Fr,Hr=[rig.data.bones[b.name].matrix_local for b in [F,H]]
   neutral=F.matrix.to_3x3()@Fr.to_3x3().inverted()@Hr.to_3x3();q=(neutral.inverted()@H.matrix.to_3x3()).to_quaternion()
   sw,tw=swing_twist_deg(q,Vector((0,1,0)));wrists[s].append([float(t),sw,tw])
 report[role]={'joints':{},'wrists':{}}
 for n,q in quats.items():
  acc=acceleration(q);step=np.array([np.linalg.norm(rv(b@a.inverted()))*180/math.pi for a,b in zip(q,q[1:])]);i=int(acc.argmax())
  report[role]['joints'][n]={'max_acceleration_deg_s2':float(acc[i]),'worst_time':(i+1)/48,'p99_acceleration_deg_s2':float(np.percentile(acc,99)),'max_step_deg':float(step.max()),'pass':float(acc.max())<=20000 and float(step.max())<=35}
 for s,x in wrists.items():
  a=np.array(x);report[role]['wrists'][s]={'swing_max_deg':float(a[:,1].max()),'roll_min_max_deg':[float(a[:,2].min()),float(a[:,2].max())],'worst_swing_time':float(a[a[:,1].argmax(),0]),'pass':bool(a[:,1].max()<=70 and abs(a[:,2]).max()<=45)}
 print('ARM_MOTION',role,json.dumps(report[role]),flush=True)
(p/'work'/f'arm_motion_{tag}.json').write_text(json.dumps({'sample_hz':48,'limits':{'wrist_swing_deg':70,'wrist_roll_deg':45,'max_step_deg':35,'max_acceleration_deg_s2':20000},'selftest':'alternating 10-degree error rejected; constant turn accepted','clips':report,'pass':all(x['pass'] for a in report.values() for group in a.values() for x in group.values())},indent=2))
