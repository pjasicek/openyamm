"""Dense floor checks, source/export pose parity, loop continuity and stance velocity."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];FPS=24
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m516.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];dur=json.loads((P/'work/animation_audit.json').read_text());refs={};report={}
def co():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[ev.matrix_world@x.co for x in me.vertices];ev.to_mesh_clear();return v
def at(t):
 f=t*FPS+1;sc.frame_set(int(f),subframe=f%1)
for role,meta in dur.items():
 rig.animation_data.action=bpy.data.actions[role];refs[role]=[];low=10.;first=last=None
 for i in range(round(meta['duration']*48)+1):
  at(i/48);v=co();a=np.array(v);low=min(low,float(a[:,2].min()));first=a.copy() if first is None else first;last=a
 for frac in [0,.2,.4,.6,.8,1]:at(frac*meta['duration']);refs[role].append((frac,co()))
 delta=float(np.linalg.norm(last-first,axis=1).max());assert low>-.008,(role,low)
 if role!='Death':assert delta<.0001,(role,'seam',delta)
 report[role]={'minimum_z_m':low,'samples':i+1,'loop_or_return_error_m':delta};print(role,report[role],flush=True)
for role in ['Walking','Running']:
 meta=dur[role];errors=[];rows=meta['foot_trajectory'];step=1/FPS;speed=meta['stride_length']/meta['duration']
 for a,b in zip(rows[:-1],rows[1:]):
  for side in 'LR':
   if a[side]['stance'] and b[side]['stance'] and b[side]['phase']>a[side]['phase']:
    velocity=(np.array(b[side]['ankle'])-a[side]['ankle'])/step;errors.append(float(np.linalg.norm(velocity-np.array([0,speed,0]))))
 assert max(errors)<.005,(role,max(errors));report[role]['stance_velocity_error_m_s']=max(errors)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m516_lod0.glb'));sc=bpy.context.scene;sc.render.fps=FPS;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH')
for role,frames in refs.items():
 action=next(a for a in bpy.data.actions if a.name==role or a.name.endswith('|'+role));rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];err=0.
 for frac,expected in frames:
  lo,hi=action.frame_range;f=lo+frac*(hi-lo);sc.frame_set(int(f),subframe=f%1);actual=co();tree=KDTree(len(actual))
  for i,v in enumerate(actual):tree.insert(v,i)
  tree.balance();err=max(err,max(tree.find(v)[2] for v in expected))
 assert err<.0001,(role,err);report[role]['export_surface_error_m']=err
(P/'review/checks/export_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('EXPORT PARITY PASS')
