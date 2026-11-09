import json,sys,copy
from pathlib import Path
import numpy as np
P=Path('level_generation/creatures/hes_bulwark_codex');sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model
g=Glb(P/'export/hes_bulwark.glb');d=g.json
assert len(d['skins'])==1
cable=next(i for i,n in enumerate(d['nodes']) if n.get('name')=='Bulwark_Cables')
report={'sample_hz':60,'lods':{},'factor_only_emission':all('emissiveTexture' not in m for m in d['materials'])}
assert report['factor_only_emission']
for level in range(4):
 h=copy.deepcopy(g)
 counts={}
 for n in h.json['nodes']:
  if 'mesh' not in n:continue
  base=h.json['meshes'][n['mesh']]; chain=[n['mesh']]+base['extras']['openyamm_lods']; n['mesh']=chain[level]
  mesh=h.json['meshes'][n['mesh']];mesh['name']=n['name']
  counts[n['name']]=sum(len(h.accessor(p['indices']))//3 for p in mesh['primitives'])
 m=Model(h);result={'triangles':counts,'clips':{}}
 for p in m.primitives:
  assert np.isfinite(p['positions']).all()
  if p['skinned']:
   assert np.allclose(p['weights'].sum(1),1)
   assert (p['weights']>1e-6).sum(1).max()<=(2 if p['node']==cable else 1)
 for clip in m.clips:
  duration=m.clip_times(clip)[-1];minimum=1e9;plug_error=0;poses=[]
  for t in np.linspace(0,duration,round(duration*60)+1):
   world=m.world(m.sample(clip,t));coupled=clip.startswith('Coupled_')
   assert (abs(np.linalg.det(world[cable,:3,:3]))>.5)==coupled
   posed=m.skinned_positions(world);poses.append(posed)
   for p,(co,tris) in zip(m.primitives,posed):
    if p['node']==cable and not coupled:continue
    assert np.isfinite(co).all();minimum=min(minimum,float(co[:,1].min()))
    if p['node']==cable:
     root=m.joints.index(next(i for i,n in enumerate(d['nodes']) if n.get('name')=='B_Root'))
     mask=((p['joints']==root)*p['weights']).sum(1)>.999999
     plug_error=max(plug_error,float(np.linalg.norm(co[mask]-p['positions'][mask],axis=1).max(initial=0)))
  row={'duration_s':duration,'minimum_y_m':minimum,'root_plug_drift_m':plug_error}
  assert minimum>=-.015,(level,clip,minimum)
  assert plug_error<1e-4,(level,clip,plug_error)
  if clip.removeprefix('Coupled_') in ('Standing','Fidget','Walking','Running','Dead'):
   row['loop_error_m']=max(float(np.linalg.norm(a[0]-b[0],axis=1).max()) for a,b in zip(poses[0],poses[-1]));assert row['loop_error_m']<1e-4
  result['clips'][clip]=row
 for prefix in ('','Coupled_'):
  a=m.skinned_positions(m.world(m.sample(prefix+'Death',m.clip_times(prefix+'Death')[-1])));b=m.skinned_positions(m.world(m.sample(prefix+'Dead',0)))
  assert max(float(np.linalg.norm(x[0]-y[0],axis=1).max()) for x,y in zip(a,b))<1e-4
 report['lods'][str(level)]=result
 print('PASS LOD',level,counts,flush=True)
m=Model(g);co=np.concatenate([v for p,(v,_) in zip(m.primitives,m.skinned_positions(m.world(m.sample('Standing',0)))) if p['node']!=cable])
height=float(co[:,1].max()-co[:,1].min());report['standing_height_m']=height;report['scale']=384/height
foot=co[co[:,1]<1.5];report['foot_chassis_radius_m']=float(np.linalg.norm(foot[:,[0,2]],axis=1).max());report['radius_world']=int(np.ceil(report['foot_chassis_radius_m']*report['scale']))
(P/'review/final_gates.json').write_text(json.dumps(report,indent=2)+'\n')
print('BINDING',report['scale'],report['radius_world'],flush=True)
