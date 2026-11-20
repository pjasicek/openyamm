"""Run the shared gates on Running; collect requested source/height/contact diagnostics."""
import sys,json,time,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
original=g.Glb.clips;g.Glb.clips=lambda self:[c for c in original(self)if c[0]=='Running']
config=json.loads((P/'gates.json').read_text());g.validate_config(config);diagnostics={}
for label,path in [('baseline',P/'work/round8_before/export/mm6_dwa1.glb'),('final',P/'export/mm6_dwa1.glb')]:
 out=P/'review/round8'/label;out.mkdir(exist_ok=True);r=g.Report(config);start=time.perf_counter()
 g.run(path,config,P,out,r);status=r.write(out,time.perf_counter()-start,None);print('SHARED',label,status,flush=True)
 glb=g.Glb(path);_,a,t0,t1=glb.clips()[0];times=g.sample_grid(t0,t1,48);poses=glb.pose(a,times)
 _,st,s0,s1=next(c for c in original(glb)if c[0]=='Standing');stand=glb.pose(st,g.sample_grid(s0,s1,48))[:,glb.names['B_Pelvis'],2,3].mean()
 d={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sample_hz':48,'standing_mean_pelvis_m':float(stand),'bones':{},'feet':{}}
 for n in ['B_Pelvis','B_Head']:
  z=poses[:,glb.names[n],2,3];v=np.diff(z)/np.diff(times);acc=np.diff(v)/((np.diff(times)[1:]+np.diff(times)[:-1])/2)
  other=glb.pose(a,t0+(times-t0+(t1-t0)/2)%(t1-t0))[:,glb.names[n],2,3]
  d['bones'][n]={'min_mean_max_m':[float(z.min()),float(np.trapezoid(z,times)/(t1-t0)),float(z.max())],'min_mean_pct_standing':[float(z.min()/stand*100),float(np.trapezoid(z,times)/(t1-t0)/stand*100)],'max_vertical_acceleration_m_s2':float(abs(acc).max()),'max_vertical_step_m':float(abs(np.diff(z)).max()),'max_half_cycle_height_difference_m':float(abs(z-other).max())}
 mesh=next(m for m in g.load_meshes(glb)if m.label.endswith('/colour0'));g.configure_mesh(mesh,config,g.Report(config));low=[]
 for pose in poses:
  points=mesh.posed(pose);low.append([float(points[mesh.feet[sd][0],2].min())for sd in 'LR'])
 low=np.array(low);d['feet']['min_max_lowest_sole_m']=[float(low.min()),float(low.min(1).max())]
 for j,sd in enumerate('LR'):
  contact=low[:,j]<=.01
  d['feet'][sd]={'contact_pct':float(np.trapezoid(contact.astype(float),times)/(t1-t0)*100),'peak_swing_m':float(low[:,j].max())}
 both=low.min(1)>.01;d['feet']['double_flight_pct']=float(np.trapezoid(both.astype(float),times)/(t1-t0)*100);d['feet']['samples']=[{'t':float(t),'L_low_m':float(v[0]),'R_low_m':float(v[1])}for t,v in zip(times,low)]
 diagnostics[label]=d
(P/'review/round8/height_contact.json').write_text(json.dumps(diagnostics,indent=2));print('HEIGHT/CONTACT',json.dumps({k:{n:v for n,v in d.items()if n!='feet'}for k,d in diagnostics.items()}),flush=True)

# Requested stance/sliding diagnostic on the final runtime geometry. No gate predicates overridden.
f=json.loads((P/'review/round8/fitting.json').read_text());stride=f['runtime_run_stride_m'];plant={}
for sd,start in [('L',.10),('R',.60)]:
 ts=np.linspace(start,start+.35,85)*.8;ps=glb.pose(a,ts);points=np.array([mesh.posed(po)[mesh.feet[sd][0]]for po in ps]);points[:,:,1]-=stride*ts[:,None]/.8
 errors=[]
 for j in range(len(ts)-1):
  k=int(np.argmin(points[j,:,2]+points[j+1,:,2]));errors.append(float(np.linalg.norm(points[j+1,k,:2]-points[j,k,:2])))
 flat=(ts/.8-start>=.35*.18)&(ts/.8-start<=.35*.63);selected=points[flat];drift=np.linalg.norm(selected[:,:,:2]-selected[0,:,:2],axis=2).max()
 plant[sd]={'stance_fraction':.35,'samples':len(ts),'max_contact_point_step_mm':max(errors)*1000,'max_flat_stance_vertex_drift_mm':float(drift)*1000,'contact_point_travel_mm':sum(errors)*1000}
source=json.loads((P/'review/round8/source_probe.json').read_text())['anim_library/mixamo/Standard Run.fbx']['samples'];z=np.array([r['Hips'][2]for r in source])*f['source_leg_scale'];source_acc=float(abs(np.diff(z,n=2)/(.8/96)**2).max())
final=diagnostics['final'];jitter={n:{'max_acceleration_m_s2':d['max_vertical_acceleration_m_s2'],'source_acceleration_limit_m_s2':source_acc,'half_cycle_difference_m':d['max_half_cycle_height_difference_m'],'pass':bool(d['max_vertical_acceleration_m_s2']<source_acc and d['max_half_cycle_height_difference_m']<.001)}for n,d in final['bones'].items()}
(P/'review/round8/stance_jitter.json').write_text(json.dumps({'runtime_sha256':final['sha256'],'stance':plant,'jitter':jitter,'limits_basis':'Pelvis/head vertical acceleration must not exceed native source retimed to the unchanged 0.8 s duration and leg scale; symmetric half-cycle vertical motion within 1 mm. Shared runner independently checks arm angular acceleration.'},indent=2));print('STANCE/JITTER',plant,jitter,flush=True)
