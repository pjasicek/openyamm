import bpy,json,math,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];names=[f'B_{s}_{n}' for s in 'LR' for n in ['UpperArm','Forearm','Hand']]
def measure(r,a):
 r.animation_data_create();r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;end=float(a.frame_range[1])/sc.render.fps;times=sorted(set(list(np.arange(0,end+.000001,1/48))+[end]));previous=None;velocities=[];mids=[]
 for t in times:
  f=t*sc.render.fps;sc.frame_set(int(f),subframe=f%1);q={n:(r.matrix_world@r.pose.bones[n].matrix).to_quaternion() for n in names}
  if previous is not None:
   v=[]
   for n in names:
    d=q[n]@previous[n].inverted()
    if d.w<0:d.negate()
    axis,angle=d.to_axis_angle();v.append(np.array(axis)*math.degrees(angle)/(t-last))
   velocities.append(v);mids.append((t+last)/2)
  previous=q;last=t
 acceleration=np.linalg.norm(np.diff(np.array(velocities),axis=0)/np.diff(mids)[:,None,None],axis=2)
 return {n:float(acceleration[:,i].max()) for i,n in enumerate(names)}
bpy.ops.wm.open_mainfile(filepath=str(p/'work/retarget_raw.blend'));r=bpy.data.objects['Rig'];source={a.name:measure(r,a) for a in bpy.data.actions if a.name in ['Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death']}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_mep_runtime_lod0.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');result={}
for a in bpy.data.actions:
 role=a.name.split('|')[-1];values=measure(r,a);ref=source.get(role,{});limits={n:max(20000.,ref.get(n,0)*1.1) for n in names};result[role]={'max_degrees_per_second_squared':values,'source':ref,'limits':limits,'pass':all(values[n]<=limits[n] for n in names)}
(p/'review/acceleration_gate.json').write_text(json.dumps(result,indent=2));print('ACCELERATION',json.dumps(result),flush=True)
assert all(row['pass'] for row in result.values())
