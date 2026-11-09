"""Select authored layers for the shared runner and record nearest-surface diagnostics using its evaluator."""
import sys,json,copy
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,Surface,sample_grid
g=Glb(P/'export/mm6_lzd.glb');cfg=json.loads((P/'gates.json').read_text());cfg['cloth']+= [{'name': 'outer layers above tunic hem', 'surface': 'tunic_geometry', 'samples': 'outer_layers', 'containment': False, 'opening': {'node': 'B_Pelvis', 'point': [0.033137687655378945, 0.040742756649829404, 0.002528836343617062], 'axis': [0.3442595900498712, -0.9388746161341994, 2.1868718442381011e-07]}}, {'name': 'outer layers over lower garments', 'surface': 'lower_garments', 'samples': 'outer_layers', 'containment': False}]
cfg.setdefault('lod_regions',{});rows=[];yaw=[]
for m in load_meshes(g):
 level=int(m.label[-1]);data=json.loads((P/f'work/round5/lod{level}_pieces.json').read_text())
 original=np.array(data['positions']);labels=np.array(data['pieces'])
 # Export splits UV/material vertices but preserves bind positions.
 distance=np.linalg.norm(m.rest[:,None,:]-original[None,:,:],axis=2)
 nearest=distance.argmin(1);assert distance[np.arange(len(nearest)),nearest].max()<1e-5
 piece=labels[nearest];kind=m.label.split('/')[-1]
 inner=np.isin(piece,[2,10,15]);outer=np.isin(piece,[16,17,12,23])
 cfg['cloth'][0]['surface']='flap_geometry'
 cfg['lod_regions'].setdefault(kind,{})['flap_geometry']={'vertices':np.flatnonzero(piece==15).tolist()}
 cfg['lod_regions'].setdefault(kind,{}).update(tunic_geometry={'vertices':np.flatnonzero(piece==2).tolist()},lower_garments={'vertices':np.flatnonzero(np.isin(piece,[10,15])).tolist()},outer_layers={'vertices':np.flatnonzero(outer).tolist()})
 if 'shadow'in kind:continue
 groups=[('shoulders',np.isin(piece,[16,17]),piece==2),('belt',np.isin(piece,[12,23]),np.isin(piece,[2,10,15]))]
 for name,om,im in groups:
  if not om.any():continue
  surface=Surface(m,im);tri=m.faces[np.all(om[m.faces],axis=1)]
  assert len(tri)
  # Same triangle vertices/midpoints/centroids used by the shared grip surface diagnostic.
  bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3])
  for clip,a,start,end in g.clips():
   best={'distance_m':1e9}
   for t,pose in zip(sample_grid(start,end,48),g.pose(a,sample_grid(start,end,48))):
    points=m.posed(pose);surface.build(points,pose)
    query=np.einsum('sk,tkj->tsj',bary,points[tri]).reshape(-1,3)
    hits=[surface.tree.find_nearest(Vector(p))for p in query];ds=np.array([h[3]for h in hits]);i=int(ds.argmin())
    if ds[i]<best['distance_m']:best={'distance_m':float(ds[i]),'time_s':float(t),'sample':i,'point':query[i].tolist(),'nearest':list(hits[i][0])}
   rows.append({'lod':kind,'clip':clip,'layers':name,**best})
for clip,a,start,end in g.clips():
 if clip not in ['Standing','Walking','Running']:continue
 ts=sample_grid(start,end,192);pose=g.pose(a,ts);values={}
 for name in ['B_Pelvis','B_Spine2']:
  i=g.names[name];d=pose[:,i,:3,:3]@np.linalg.inv(g.rest[i,:3,:3]);values[name]=np.degrees(np.unwrap(np.arctan2(d[:,1,0],d[:,0,0])))
 yaw.append({'clip':clip,'pelvis_max_abs_deg':float(abs(values['B_Pelvis']).max()),'shoulder_max_abs_deg':float(abs(values['B_Spine2']).max()),'counterrotation_max_abs_deg':float(abs(values['B_Pelvis']-values['B_Spine2']).max()),'samples':[{'time_s':float(t),'pelvis_deg':float(p),'shoulders_deg':float(s)}for t,p,s in zip(ts,values['B_Pelvis'],values['B_Spine2'])]})
(P/'gates.layers.json').write_text(json.dumps(cfg,indent=2))
primary=copy.deepcopy(cfg);primary['cloth']=primary['cloth'][:1]
for regions in primary['lod_regions'].values():
 regions.pop('tunic_geometry',None);regions.pop('lower_garments',None);regions.pop('outer_layers',None)
(P/'gates.json').write_text(json.dumps(primary,indent=2))
(P/'review/round5/layer_distances.json').write_text(json.dumps({'body_sha256':g.sha256,'method':'Shared runner Glb/Mesh/Surface evaluator and BVH; 48 Hz triangle vertex/edge/centre nearest distances. Diagnostic only; shared cloth runner certifies penetration.','rows':rows},indent=2))
(P/'review/round5/forward_orientation.json').write_text(json.dumps(yaw,indent=2))
print('LAYER_MINIMA',[(n,min(r['distance_m']for r in rows if r['layers']==n))for n in ['shoulders','belt']])

from run_gates import Report,bone_gates
report=Report(cfg)
for name,a,start,end in g.clips():
 times=sample_grid(start,end,48);bone_gates(g,g.pose(a,times),times,name,cfg,report,cfg['props'])
print('BONE_FAILURES',[(r['clip'],r['gate'],r['region'],r['worst'],r['time_s'])for r in report.rows.values()if r['status']=='FAIL'],flush=True)
