"""Actual exported soles, leg angles, stance travel and connected tunic edge stretch at 48 Hz."""
import bpy,sys,json,hashlib,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;me=body.data
rest=np.array([tuple(body.matrix_world@v.co)for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);patch={}
for sd in 'LR':
 ids=np.where((rest[:,2]<.001)&((rest[:,0]>0)==(sd=='L')))[0];assert len(ids)>12;y=rest[ids,1]
 patch[sd]={'all':ids,'heel':ids[y>=np.quantile(y,.7)],'toe':ids[y<=np.quantile(y,.3)]}
E=np.array([tuple(e.vertices)for e in me.edges]);E=E[(pv[E[:,0]]==2)&(pv[E[:,1]]==2)];rl=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1);E=E[rl>1e-5];rl=rl[rl>1e-5];report={};cloth={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];duration=float(a.frame_range[1])/scene.render.fps;rows=[];p99=0;mx=0;worst=None
 for t in sorted(set([*np.arange(0,duration-1e-6,1/48),duration])):
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co)for v in mesh.vertices]);ev.to_mesh_clear()
  ratios=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)/rl;p99=max(p99,float(np.percentile(ratios,99)))
  if ratios.max()>mx:mx=float(ratios.max());worst={'seconds':float(t),'edge':E[np.argmax(ratios)].tolist()}
  if name not in ['Walking','Running']:continue
  row={'seconds':float(t),'pelvis_z':float((rig.matrix_world@rig.pose.bones['B_Pelvis'].matrix).translation.z)}
  for sd,ids in patch.items():
   sole=co[ids['all']];_,_,v=np.linalg.svd(sole-sole.mean(0));tilt=math.degrees(math.acos(np.clip(abs(v[-1,2]),0,1)))
   H,K,A=[(rig.matrix_world@rig.pose.bones[f'B_{sd}_{j}'].matrix).translation for j in ['Thigh','Calf','Foot']];u=(K-H).normalized();v=(A-K).normalized();knee=math.degrees(math.acos(np.clip(u.dot(v),-1,1)))
   row[sd]={'lowest_m':float(sole[:,2].min()),'heel_m':float(co[ids['heel'],2].mean()),'toe_m':float(co[ids['toe'],2].mean()),'tilt_deg':tilt,'center_y':float(sole[:,1].mean()),'knee_deg':knee}
  rows.append(row)
 cloth[name]={'p99_edge_stretch':p99,'max_edge_stretch':mx,'worst':worst,'pass':p99<2 and mx<2.5}
 print('FLAP',name,cloth[name],flush=True)
 if not rows:continue
 low=np.array([min(r['L']['lowest_m'],r['R']['lowest_m'])for r in rows]);feet={}
 for sd in 'LR':
  peak=max(rows,key=lambda r:r[sd]['lowest_m']);stride=.89*(1.55 if name=='Running'else 1);stance=.48 if name=='Running'else .56;off=.75 if name=='Running'else .28
  mid=min(rows,key=lambda r:abs(((r['seconds']/duration+off+(0 if sd=='L'else .5))%1)-(stance+(1-stance)*.5)))
  speeds=[]
  for x,y in zip(rows,rows[1:]):
   phases=[(r['seconds']/duration+off+(0 if sd=='L'else .5))%1 for r in [x,y]]
   if all(.14*stance<q<.82*stance for q in phases):speeds.append((y[sd]['center_y']-x[sd]['center_y'])/(y['seconds']-x['seconds']))
  feet[sd]={'peak_lowest_sole_m':peak[sd]['lowest_m'],'peak_heel_m':max(r[sd]['heel_m']for r in rows),'peak_toe_m':max(r[sd]['toe_m']for r in rows),'knee_at_peak_lift_deg':peak[sd]['knee_deg'],'mid_swing_knee_deg':mid[sd]['knee_deg'],'stance_travel_speed_m_s':speeds,'expected_stance_speed_m_s':stride/duration,'stance_max_speed_error_m_s':max(abs(x-stride/duration)for x in speeds)}
 report[name]={'sample_hz':48,'samples':len(rows),'lowest_sole_min_max_m':[float(low.min()),float(low.max())],'contact_percent':float((low<=.01).mean()*100),'feet':feet,'trace':rows}
 print('GAIT',name,json.dumps({k:v for k,v in report[name].items()if k!='trace'}),flush=True)
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest()
(P/'review/round3/flap_stretch_gate.json').write_text(json.dumps({'runtime_sha256':h,'sample_hz':48,'surface':'entire connected tunic piece 2, including front and back panels','clips':cloth,'pass':all(x['pass']for x in cloth.values())},indent=2)+'\n')

for name,r in report.items():
 ok=r['lowest_sole_min_max_m'][0]>=-.002 and r['lowest_sole_min_max_m'][1]<(.04 if name=='Running'else .01) and r['contact_percent']>=80
 for sd,foot in r['feet'].items():
  ok &= foot['stance_max_speed_error_m_s']<.005
  if name=='Walking':ok &= .08<foot['peak_heel_m']<.12 and .08<foot['peak_toe_m']<.12 and 40<foot['mid_swing_knee_deg']<60
  stance=.48 if name=='Running'else .56;off=.75 if name=='Running'else .28
  flat=[x[sd] for x in r['trace'] if .14*stance<(x['seconds']/.8+off+(0 if sd=='L'else .5))%1<.82*stance]
  foot['flat_stance_max_tilt_deg']=max(x['tilt_deg']for x in flat)
  foot['flat_stance_heel_toe_min_max_m']=[min(min(x['heel_m'],x['toe_m'])for x in flat),max(max(x['heel_m'],x['toe_m'])for x in flat)]
  ok &= foot['flat_stance_max_tilt_deg']<3 and foot['flat_stance_heel_toe_min_max_m'][0]>=-.002 and foot['flat_stance_heel_toe_min_max_m'][1]<.01
 r['pass']=bool(ok)
out={'runtime_sha256':h,'export_sampling_hz':120,'sample_hz':48,'stride_length':.89,'runtime_run_multiplier':1.55,'clips':report,'pass':all(r['pass']for r in report.values())}
(P/'review/round3/locomotion_gate.json').write_text(json.dumps(out,indent=2)+'\n')
assert out['pass'],'Locomotion gate failed'
assert all(x['pass']for x in cloth.values()),'Tunic stretch gate failed'
