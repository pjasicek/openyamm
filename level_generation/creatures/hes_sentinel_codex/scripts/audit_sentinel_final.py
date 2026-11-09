"""Final Sentinel contract: all textured LODs, all clips, tier sharing, emission and floor contact."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path.insert(0,str(R/'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb,Model
path=P/'export/hes_sentinel.glb';g=Glb(path);d=g.json
node=next(n for n in d['nodes'] if n.get('name')=='Sentinel');base=node['mesh'];chain=d['meshes'][base]['extras']['openyamm_lods'];assert len(chain)==3
variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']];assert variants==['sentinel_a','sentinel_b','sentinel_c']
counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in [base]+chain]
assert counts[0]==9867 and all(a>b for a,b in zip(counts,counts[1:]))
for mi in [base]+chain:
 for p in d['meshes'][mi]['primitives']:
  mappings=p['extensions']['KHR_materials_variants']['mappings'];assert sorted(v for m in mappings for v in m['variants'])==[0,1,2]
  mats=[d['materials'][m['material']] for m in mappings]
  textures=lambda mat:(mat['pbrMetallicRoughness'].get('baseColorTexture'),mat['pbrMetallicRoughness'].get('metallicRoughnessTexture'),mat.get('normalTexture'),mat.get('extras',{}).get('openyamm_region_mask'))
  assert all(textures(m)==textures(mats[0]) for m in mats)
  for mat in mats:
   assert 'emissiveTexture' not in mat
   if mat['name'].startswith('Sentinel_Energy'):assert mat['extras']['openyamm_bloom'] and max(mat['emissiveFactor'])>0
   else:assert all(len(x['colors'])==16 for x in mat['extras']['openyamm_region_ramps'])
report={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':counts,'variants':variants,'tier_maps_shared':True,'factor_only_emission':True,'lods':{}}
for level,mi in enumerate([base]+chain):
 dg=copy.deepcopy(g);next(n for n in dg.json['nodes'] if n.get('name')=='Sentinel')['mesh']=mi;dg.json['meshes'][mi]['name']='Sentinel'
 model=Model(dg);names={n.get('name'):i for i,n in enumerate(dg.json['nodes'])};root=model.joints.index(names['B_Root'])
 assert set(model.clips)=={'Standing','Attack','Hit','Death','Dead'}
 rest=model.skinned_positions(model.world(model.sample('Standing',0)));fixed=[]
 for p in model.primitives:
  assert np.allclose(p['weights'].sum(1),1,atol=1e-5)
  assert ((p['weights']>1e-6).sum(1)<=2).all()
  fixed.append(((p['joints']==root)&(p['weights']>.9999)).any(1))
 clips={}
 for clip in model.clips:
  duration=max(model.clip_times(clip));low=[];drift=0
  start=model.world(model.sample(clip,0));movement=0
  for t in np.linspace(0,duration,round(duration*60)+1):
   w=model.world(model.sample(clip,float(t)));movement=max(movement,float(np.abs(w-start).max()))
   posed=model.skinned_positions(w);low.append(min(float(v[:,1].min()) for v,_ in posed)*130)
   for (v,_),(r,_),mask in zip(posed,rest,fixed):
    if mask.any():drift=max(drift,float(np.abs(v[mask]-r[mask]).max()))
  assert min(low)>=-2.5 and max(low)<=2.5,(level,clip,min(low),max(low))
  assert drift<1e-5 and (movement>.025 if clip!='Dead' else movement<1e-6)
  clips[clip]={'duration':duration,'floor_min_at_scale_130':min(low),'floor_max_at_scale_130':max(low),'base_drift_m':drift}
 for first,last,seconds in [('Standing','Standing',6),('Attack','Attack',.5),('Hit','Hit',.4),('Dead','Death',1.2)]:
  a=model.skinned_positions(model.world(model.sample(first,0)));b=model.skinned_positions(model.world(model.sample(last,seconds)))
  assert all(np.allclose(x[0],y[0],atol=1e-6) for x,y in zip(a,b))
 report['lods'][str(level)]=clips
for script in [R/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py',R/'level_generation/creatures/hes_turrets_claude/scripts/check_key_times.py']:
 subprocess.run([sys.executable,str(script),str(path)],check=True)
(P/'review/sentinel_final_gates.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL SENTINEL GATES PASS',counts,flush=True)
