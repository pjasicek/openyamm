"""Every half-frame: skin/cloth strain, finite geometry, soles and held-death parity."""
from pathlib import Path
import bpy,json
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/globals().get('INPUT_BLEND','motion_fitted.blend')))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;sc=bpy.context.scene
rest=np.array([v.co[:] for v in me.vertices]);region=np.array([v.value for v in me.attributes['region'].data]);edges=np.array([e.vertices[:] for e in me.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
gn=[g.name for g in body.vertex_groups];aw=[];hw=[]
for v in me.vertices:
 aw.append(sum(g.weight for g in v.groups if any(n in gn[g.group] for n in ['UpperArm','Forearm'])))
 hw.append(sum(g.weight for g in v.groups if any(n in gn[g.group] for n in ['Hand','Finger'])))
masks={'arms':(region==0)&(np.array(aw)>.3),'hands':(region==0)&(np.array(hw)>.3),'vest':region==2,'trousers':region==1}
em={n:m[edges[:,0]]&m[edges[:,1]]&(length>.0005) for n,m in masks.items()}
out={};poses={}
for name in ['Standing','Walking','Fidget','Hit','Death','Dead']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 sample_positions=[]
 r={'floor_min_m':1.,'floor_max_m':-1.,'stretch':{n:{'p99':0.,'max':0.} for n in masks}}
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();pos=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();assert np.isfinite(pos).all()
  sample_positions.append(pos.copy())
  ratio=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1)/np.maximum(length,1e-6)
  for n,e in em.items():
   q=r['stretch'][n];q['p99']=max(q['p99'],float(np.quantile(ratio[e],.99)));q['max']=max(q['max'],float(ratio[e].max()))
  floor=float(pos[:,2].min());r['floor_min_m']=min(r['floor_min_m'],floor);r['floor_max_m']=max(r['floor_max_m'],floor)
 r['motion_span_m']=float(np.max(np.linalg.norm(np.ptp(np.array(sample_positions),axis=0),axis=1)))
 r['height_end_m']=float(pos[:,2].max())
 if name=='Walking':assert r['motion_span_m']>.2,r
 if name=='Standing':assert r['height_end_m']>1.4,r
 poses[name]=pos;out[name]=r;print('DEFORM',name,r,flush=True)
out['dead_matches_death_mm']=float(np.max(np.linalg.norm(poses['Dead']-poses['Death'],axis=1))*1000)
(P/'work/deformation.json').write_text(json.dumps(out,indent=2)+'\n')
assert all(r['stretch']['arms']['p99']<2 for n,r in out.items() if isinstance(r,dict))
assert all(r['stretch']['hands']['max']<4.5 for n,r in out.items() if isinstance(r,dict))
assert all(r['floor_min_m']>-.02 for n,r in out.items() if isinstance(r,dict))
assert out['dead_matches_death_mm']<.1,out['dead_matches_death_mm']
