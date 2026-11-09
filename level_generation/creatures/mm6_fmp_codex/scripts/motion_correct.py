"""Fit the library stride to a long dress; author restrained native hit/fidget and floor placement."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
import numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_base.blend'))
s=bpy.context.scene;s.render.fps=30;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
def use(a):
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
def snapshot(a):
 use(a);rows=[]
 for f in range(int(a.frame_range[1])+1):
  s.frame_set(f);rows.append({b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones})
 return rows
base=snapshot(bpy.data.actions['Standing']);stand=base[0]
def write(name,rows):
 old=bpy.data.actions.get(name)
 if old:rig.animation_data.action=None;bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;use(a)
 for f,row in enumerate(rows):
  for n,(loc,q) in row.items():
   b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.location=loc;b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 return a
for name,amount in [('Walking',.50),('Run',.68)]:
 rows=snapshot(bpy.data.actions[name])
 for row in rows:
  for n,(loc,q) in list(row.items()):
   if any(t in n for t in ('Thigh','Calf','Foot','Toe')):row[n]=(loc,stand[n][1].slerp(q,amount))
 write(name,rows)
# A small backward recoil, open hands coming forward, followed by recovery to the idle pose.
for name in ('Hit','Fidget'):
 rows=[]
 for f in range(24):
  t=f/23;env=math.sin(math.pi*t)**2;row={n:(loc.copy(),q.copy()) for n,(loc,q) in base[0].items()}
  changes={'B_Spine':(-6*env,0,0),'B_Spine1':(-5*env,0,0),'B_Head':(2*env,0,5*env)} if name=='Hit' else {'B_Spine1':(0,0,2*math.sin(2*math.pi*t)*env),'B_Head':(0,0,-4*math.sin(2*math.pi*t)*env)}
  for n,angles in changes.items():
   loc,q=row[n];R=rig.data.bones[n].matrix_local.to_3x3()
   for axis,deg in zip((Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))),angles):q=q@Quaternion(R.inverted()@axis,math.radians(deg))
   row[n]=(loc,q)
  if name=='Hit':
   for side in ('L','R'):
    n=f'B_{side}_UpperArm';loc,q=row[n];axis=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0));row[n]=(loc,q@Quaternion(axis,math.radians(-12*env)))
  rows.append(row)
 write(name,rows)
# Use evaluated visible anatomy for floor placement; the separately simulated skirt is excluded.
pieces=np.array([v.value for v in body.data.attributes['piece'].data]);ids=np.where(~np.isin(pieces,[1,7]))[0];stats={}
for name in ('Standing','Walking','Run','Hit','Fidget','Death'):
 a=bpy.data.actions[name];rows=snapshot(a);lifts=[]
 for f,row in enumerate(rows):
  s.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();floor=min((ev.matrix_world@m.vertices[int(i)].co).z for i in ids);ev.to_mesh_clear();lifts.append(.008-floor)
 # Limit floor correction to the static foot mismatch for Run, preserving its airborne phase.
 if name=='Run':lifts=[min(lifts)]*len(lifts)
 for row,lift in zip(rows,lifts):
  loc,q=row['B_Pelvis'];axis=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()@Vector((0,0,lift));row['B_Pelvis']=(loc+axis,q)
 write(name,rows);stats[name]={'floor_lift_min':min(lifts),'floor_lift_max':max(lifts),'frames':len(rows)}
(p/'review/motion_corrections.json').write_text(json.dumps(stats,indent=2));print('FLOOR',stats)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_corrected.blend'))
