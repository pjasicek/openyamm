"""Carry the validated atlas/UV layout across animation-only exports, with topology assertions."""
from pathlib import Path
import sys,copy,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
for kind in ['body','spear','buckler']:
 for level in range(4):
  name=f'mm6_natm_{kind}_lod{level}.glb';doc,buf=read_glb(P/'export'/name);old,data=read_glb(P/'work/shared_atlas_cache'/name);pr=doc['meshes'][0]['primitives'][0];op=old['meshes'][0]['primitives'][0]
  positions=accessor_array(doc,buf,pr['attributes']['POSITION']);old_positions=accessor_array(old,data,op['attributes']['POSITION']);delta=np.linalg.norm(positions-old_positions,axis=1)
  if delta.max()>1e-6:
   assert kind=='body' and delta.max()<.025,(kind,level,float(delta.max()))
   skin=doc['skins'][0];names=[doc['nodes'][j]['name']for j in skin['joints']];hand=np.zeros(len(positions))
   for key in pr['attributes']:
    if key.startswith('JOINTS_'):
     joints=accessor_array(doc,buf,pr['attributes'][key]);weights=accessor_array(doc,buf,pr['attributes']['WEIGHTS_'+key[7:]]);take=np.array([n.startswith(('B_L_Hand','B_L_Finger')) or (level==3 and n=='Feather_B_Pelvis')for n in names]);hand+=(take[joints]*weights).sum(1)
   assert np.all(hand[delta>1e-6]>.15),'Only the recorded coarse hand and belt feather repairs may move vertices'
  assert np.array_equal(accessor_array(doc,buf,pr['indices']),accessor_array(old,data,op['indices']))
  idx=op['attributes']['TEXCOORD_0'];pr['attributes']['TEXCOORD_0']=append_accessor(doc,buf,accessor_array(old,data,idx),old['accessors'][idx],34962)
  for key in ['images','textures','materials','samplers']:doc[key]=copy.deepcopy(old[key])
  pr['material']=op['material'];pr['extensions']=copy.deepcopy(op.get('extensions',{}))
  for im in doc['images']:
   view=old['bufferViews'][im['bufferView']];offset=view.get('byteOffset',0);packed=data[offset:offset+view['byteLength']];buf.extend(b'\0'*(-len(buf)%4));im['bufferView']=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(packed)});buf.extend(packed)
  doc,buf=compact(doc,buf);write_glb(P/'export'/name,doc,buf)
print('REUSED_SHARED_ATLAS',flush=True)
