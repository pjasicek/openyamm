"""Verify export pose parity and measure the planted-foot stride and six-claw rake."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m592.blend'));sc=bpy.context.scene;sc.render.fps=30;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
def setpose(rig,a,t):
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*30;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
def coords(body):
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return c
source={};times={a.name:np.linspace(0,float(a.frame_range[1])/30,13).tolist() for a in bpy.data.actions}
for n,ts in times.items():
 for t in ts:setpose(rig,bpy.data.actions[n],t);source[n,t]=coords(body)
rest=np.array([tuple(v.co) for v in body.data.vertices]);measure={}
for n in ['Walking','Running']:
 a=bpy.data.actions[n];duration=float(a.frame_range[1])/30;ts=np.arange(0,duration+1e-7,1/120);feet={sd:[] for sd in 'LR'};ankles={sd:[] for sd in 'LR'}
 for t in ts:
  setpose(rig,a,t);c=coords(body)
  for sd,sign in [('L',1),('R',-1)]:
   ids=(rest[:,2]<.12)&(abs(rest[:,0])<.5)&(rest[:,0]*sign>0);feet[sd].append(c[ids,2].min());ankles[sd].append(tuple((rig.matrix_world@rig.pose.bones[f'B_{sd}_Foot'].matrix).translation))
 v={}
 for sd in 'LR':
  pts=np.array(ankles[sd]);soles=np.array(feet[sd]);low=soles<np.percentile(soles,25)+.008;vy=np.gradient(pts[:,1],ts);v[sd]=float(np.median(vy[low & (vy>0)]))
 speed=float(np.mean(list(v.values())));print('STRIDE_DETAIL',n,v,flush=True);assert speed>0
 measure[n]={'cycle_seconds':duration,'planted_foot_speed':v,'stride_length':speed*duration,'foot_trajectories':{sd:{'time':ts.tolist(),'sole':feet[sd],'ankle':ankles[sd]} for sd in 'LR'}}
F=json.loads((P/'work/claws_fit.json').read_text());local={}
for f in F['R']+F['L']:local[f['name']]=rig.data.bones[f['name']].matrix_local.inverted()@Vector(f['tip'])
rake=[]
for t in np.arange(.75,1.126,1/120):
 setpose(rig,bpy.data.actions['Attack'],t);tips=[tuple(rig.matrix_world@rig.pose.bones[n].matrix@v) for n,v in local.items()];rake.append({'time':float(t),'tips':tips,'reach':-float(np.mean([q[1] for q in tips]))})
peak=max(rake,key=lambda x:x['reach']);measure['Attack']={'peak_forward_reach':peak,'impact_seconds':.95,'samples':rake};print('MEASURE', {k:{a:b for a,b in measure[k].items() if a!='foot_trajectories'} for k in ['Walking','Running']}, peak,flush=True)
(P/'review/runtime_measurements.json').write_text(json.dumps(measure,indent=2)+'\n')
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m592_runtime_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['PlaneGuardian'];report={}
for n,ts in times.items():
 a=next(a for a in bpy.data.actions if a.name==n or a.name.startswith(n+'_'));errors=[]
 for t in ts:
  setpose(rig,a,t);after=coords(body);before=source[n,t];tree=kdtree.KDTree(len(before))
  for i,c in enumerate(before):tree.insert(Vector(c),i)
  tree.balance();errors.append(max(tree.find(Vector(c))[2] for c in after))
 report[n]={'samples':len(ts),'maximum_surface_error_mm':max(errors)*1000};assert max(errors)<.003,(n,max(errors))
(P/'review/export_parity.json').write_text(json.dumps(report,indent=2)+'\n');print('EXPORT_PARITY',report,flush=True)
