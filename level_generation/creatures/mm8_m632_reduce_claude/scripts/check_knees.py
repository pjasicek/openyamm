"""Knee bend curvature (copy of ../mm8_m412_claude/scripts/check_knees.py): skinned chord error of thigh/calf edges
across the knee, all clips, both knees, every colour LOD at 120 Hz; limits 8/16/24/40 mm per LOD as installed.
Usage: check_knees.py <out.json> <glb...>; prints the worst per LOD and PASS/FAIL (no assert)."""
import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,sample_grid
report={}
for path in sys.argv[2:]:
 g=Glb(path);results=[]
 for mesh in load_meshes(g):
  if 'shadow' in mesh.label or mesh.label.endswith('_B/colour0') or mesh.label.endswith('_C/colour0'):continue
  mask=(mesh.weight(['B_?_Thigh','B_?_Calf'])>.95)&(abs(mesh.rest[:,0])>.03)&(abs(mesh.rest[:,0])<.32)
  a,b=mesh.edges.T
  take=mask[a]&mask[b]&(np.minimum(mesh.rest[a,2],mesh.rest[b,2])<.72)&(np.maximum(mesh.rest[a,2],mesh.rest[b,2])>.44)&(mesh.rest[a,0]*mesh.rest[b,0]>0)
  a,b=a[take],b[take];mid=(mesh.vertices[a]+mesh.vertices[b])/2
  res={'mesh':mesh.label,'edges':len(a),'clips':{}}
  if not len(a):continue
  for name,clip,start,end in g.clips():
   worst=(0,0)
   for t,pose in zip(sample_grid(start,end,120),g.pose(clip,sample_grid(start,end,120))):
    mats=pose[mesh.skin_nodes]@mesh.bind
    posed=mesh.posed(pose)
    ideal=np.zeros_like(mid)
    for ends in [a,b]:
     for k in range(mesh.weights.shape[1]):
      m=mats[mesh.joints[ends,k]]
      ideal+=(np.einsum('nij,nj->ni',m[:,:3,:3],mid)+m[:,:3,3])*mesh.weights[ends,k,None]*.5
    errors=np.linalg.norm(ideal-(posed[a]+posed[b])/2,axis=1)
    maximum=float(errors.max()*1000)
    if maximum>worst[0]:
     worst=(maximum,float(t)); wi=int(errors.argmax()); worstedge=mesh.rest[[a[wi],b[wi]]].tolist()
   res['clips'][name]={'max_skinning_chord_error_mm':worst[0],'frame48':worst[1]*48,'edge_rest':worstedge}
  results.append(res)
 report[path]=results
 for result in results:
  level=int(result['mesh'][-1]); limit=[8,16,24,40][level]
  worst=max(result['clips'].items(),key=lambda kv:kv[1]['max_skinning_chord_error_mm'])
  print('KNEE',Path(path).name,result['mesh'],'edges',result['edges'],'worst %.2f mm'%worst[1]['max_skinning_chord_error_mm'],worst[0],'f48 %.0f'%worst[1]['frame48'],'limit',limit,'PASS' if worst[1]['max_skinning_chord_error_mm']<limit else 'FAIL')
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n')
