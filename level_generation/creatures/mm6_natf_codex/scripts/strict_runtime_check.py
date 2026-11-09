import sys,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from build_actor_lods import read_glb,accessor_bytes
report={}
for name in ['mm6_natf','mm6_natf_blade','mm6_natf_shield']:
 path=P/f'export/{name}.glb';doc,data=read_glb(path);worst=0;primitives=0
 for mesh in doc['meshes']:
  for pr in mesh['primitives']:
   sums=[]
   for key,index in pr['attributes'].items():
    if key.startswith('WEIGHTS_'):
     ac=doc['accessors'][index];dtype={5126:np.float32,5123:np.uint16,5121:np.uint8}[ac['componentType']];a=np.frombuffer(accessor_bytes(doc,data,index),dtype).reshape(-1,4).astype(float)
     if ac.get('normalized'):a/=np.iinfo(dtype).max
     sums.append(a.sum(1))
   if sums:primitives+=1;worst=max(worst,float(np.abs(sum(sums)-1).max()))
 assert worst<=1e-4,(name,worst)
 report[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'skinned_primitives_checked':primitives,'weight_sum_max_error':worst,'clips':[a['name']for a in doc.get('animations',[])],'skin_joint_counts':[len(s['joints'])for s in doc.get('skins',[])]}
(P/'review/final/runtime_integrity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
