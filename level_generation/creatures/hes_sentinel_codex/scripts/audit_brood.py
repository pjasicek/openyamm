"""Verify final one-bone clips, LODs, regions and floor contact using the shared pose evaluator."""
import copy,json,sys,hashlib,subprocess
from pathlib import Path
import numpy as np
P=Path('level_generation/creatures/hes_sentinel_codex').resolve();R=P.parents[2]
sys.path.insert(0,str(R/'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb,Model
report={}
for n in ['egg_cluster','brood_sac','ganglion']:
 path=P/'export'/('hes_'+n+'.glb');g=Glb(path);d=g.json
 assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==1
 assert set(a['name'] for a in d['animations'])=={'Standing','Hit','Death','Dead'}
 for mat in d['materials']:
  assert 'emissiveTexture' not in mat
  if mat.get('extras',{}).get('openyamm_region_mask'):
   assert all(len(x['colors'])==16 for x in mat['extras']['openyamm_region_ramps'])
 node=next(x for x in d['nodes'] if x.get('name')=='BroodBody');base=node['mesh'];chain=d['meshes'][base]['extras']['openyamm_lods']
 assert len(chain)==3
 counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in [base]+chain]
 assert counts[0]<=15000 and all(a>b for a,b in zip(counts,counts[1:]))
 entry={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':counts,'clips':{},'lod_floor':{}}
 for level,mi in enumerate([base]+chain):
  dg=copy.deepcopy(g);nd=next(x for x in dg.json['nodes'] if x.get('name')=='BroodBody');nd['mesh']=mi;dg.json['meshes'][mi]['name']='BroodBody'
  m=Model(dg);floors={}
  for clip in m.clips:
   duration=max(m.clip_times(clip));times=np.linspace(0,duration,round(duration*60)+1)
   values=[m.lowest(clip,float(t))*100 for t in times]
   assert all(np.isfinite(values));assert min(values)>=-2.5 and max(values)<=2.5,(n,level,clip,min(values),max(values))
   floors[clip]={'min_world_units':min(values),'max_world_units':max(values),'samples':len(values)}
   if level==0:entry['clips'][clip]={'duration':duration,'samples':len(times)}
  end=m.skinned_positions(m.world(m.sample('Death',max(m.clip_times('Death')))))
  dead=m.skinned_positions(m.world(m.sample('Dead',0)))
  assert all(np.allclose(a[0],b[0],atol=1e-6) for a,b in zip(end,dead)),n
  entry['lod_floor'][str(level)]=floors
 report[n]=entry
 subprocess.run([sys.executable,str(R/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),str(path)],check=True)
 subprocess.run([sys.executable,str(R/'level_generation/creatures/hes_turrets_claude/scripts/check_key_times.py'),str(path)],check=True)
Path(sys.argv[1] if len(sys.argv)>1 else P/'review/final_gates.json').write_text(json.dumps(report,indent=2)+'\n')
print('FINAL BROOD GATES PASS')
