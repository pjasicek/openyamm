import bpy,sys,json,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
import build_actor_lods
def accessor_array(d,b,i):
 a=d['accessors'][i];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 return np.frombuffer(build_actor_lods.accessor_bytes(d,b,i),dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]).reshape(-1,n)
D,B=build_actor_lods.read_glb(P/'export/mm8_m576_prepared.glb')
node=next(n for n in D['nodes'] if n.get('name')=='Triton');names=[D['nodes'][i]['name'] for i in D['skins'][node['skin']]['joints']]
g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='contact_selector')
a=g['Glb'](P/'export/mm8_m576_prepared.glb');m=g['load_meshes'](a)[0]
# Preserve the whole gripping hand: far-LOD collapses bridge across the shaft between protected contact patches.
hand=m.weight(['B_L_Hand','B_L_Finger*'])>.3
protected=list(m.rest[hand]);print('PRESERVED GRIPPING HAND VERTICES',int(hand.sum()),flush=True)
for pr in D['meshes'][node['mesh']]['primitives']:
 at=pr['attributes'];v=accessor_array(D,B,at['POSITION']);j=accessor_array(D,B,at['JOINTS_0']);w=accessor_array(D,B,at['WEIGHTS_0'])
 # The entire plain grip section keeps its octagonal cross-section in every LOD.
 prop=np.array([n=='Trident' for n in names]);ids=np.flatnonzero((prop[j]*w).sum(1)>.9)
 if len(ids):
  bind_index=D['skins'][node['skin']]['joints'].index(next(i for i,n in enumerate(D['nodes']) if n.get('name')=='Trident'))
  skin=D['skins'][node['skin']];raw=build_actor_lods.accessor_bytes(D,B,skin['inverseBindMatrices']);bind=np.frombuffer(raw,dtype='<f4').reshape(-1,4,4)[bind_index].T
  q=(np.c_[v[ids],np.ones(len(ids))]@bind.T)[:,:3]
  ids=ids[(np.abs(q[:,0])<.03)&(q[:,1]>-.095)&(q[:,1]<.30)]
  protected.extend(v[ids][:,[0,2,1]]*np.array([1,-1,1]))
 for side in 'LR':
  mask=np.array([n.startswith((f'B_{side}_Foot',f'B_{side}_Toe')) for n in names]);ids=np.flatnonzero((mask[j]*w).sum(1)>.5)
  if not len(ids):continue
  # Protect the actual sole band; glTF Y-up becomes Blender Z-up.
  ids=ids[v[ids,1]<v[ids,1].min()+.006]
  protected.extend(v[ids][:,[0,2,1]]*np.array([1,-1,1]))
protected=np.unique(np.round(protected,6),axis=0)
(P/'work/lod_protected_points.json').write_text(json.dumps(protected.tolist(),indent=2)+'\n')
print('PROTECTED CONTACT POINTS',len(protected),flush=True)
build_actor_lods.generate(P/'export/mm8_m576_prepared.glb',P/'export/mm8_m576_lods_raw.glb','Triton',ratios=(.5,.24,.09),max_influences=4,protected_points=protected,material_ratios={
    'Triton_A':(.5,.42,.34), 'TritonTrident_A':(.5,.28,.16)})
