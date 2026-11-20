import sys,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/floor'));from glb_pose import Glb
g=Glb(P/'work/hes_ashkite/r25_12_animated.glb');skin=g.json['skins'][0];names=[g.json['nodes'][j]['name'] for j in skin['joints']];ibm=g.accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
# Displace the C edge overlay 1 mm along its normal to avoid coplanar depth flicker.
for node in g.json['nodes']:
 if node.get('name')=='Static_Edges':
  for p in g.json['meshes'][node['mesh']]['primitives']:
   a=p['attributes'];v=g.accessor(a['POSITION']);n=g.accessor(a['NORMAL']);a['POSITION']=g.append_accessor(v+n*.001,'VEC3')
ramps=json.loads((P/'textures/ramps.json').read_text())['materials'][0]['ramps']
for mat in g.json['materials']:
 for variant,values in ramps.items():
  if mat.get('name','').startswith('Ashkite_'+variant[-1].upper()):mat['extras']['openyamm_region_ramps']=values
g.write(P/'export/hes_ashkite.glb')
for a in json.loads((P/'export/attachments.json').read_text()):
 h=Glb(P/'work/attachments_raw'/a['model']);M=ibm[names.index(a['node'])];done={}
 for mesh in h.json['meshes']:
  for p in mesh['primitives']:
   for key in ['POSITION','NORMAL']:
    old=p['attributes'][key]
    if old not in done:
     v=h.accessor(old)
     if key=='POSITION':v=(np.c_[v,np.ones(len(v))]@M.T)[:,:3]
     else:v=v@M[:3,:3].T;v/=np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1e-10)
     done[old]=h.append_accessor(v,'VEC3')
    p['attributes'][key]=done[old]
 h.write(P/'export'/a['model'])
print('Finalized runtime +',len(json.loads((P/'export/attachments.json').read_text())),'bone-local attachments')
