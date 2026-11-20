"""Validate final geometry, UVs, skin, roles, palette masks and unchanged native inputs."""
from pathlib import Path
import json,hashlib,numpy as np,sys
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
f=P/'export/mm8_m488.glb';d,b=read_glb(f);counts=[]
for mesh in d['meshes']:
 counts.append(sum(d['accessors'][x['indices']]['count']//3 for x in mesh['primitives']))
 assert len(mesh['primitives'])==1
 for prim in mesh['primitives']:
  a=prim['attributes'];ix=accessor_array(d,b,prim['indices']).reshape(-1,3);pos=accessor_array(d,b,a['POSITION']);assert ix.min()>=0 and ix.max()<len(pos)
  for key,val in a.items():assert np.isfinite(accessor_array(d,b,val)).all()
  weights=accessor_array(d,b,a['WEIGHTS_0']);assert np.max(abs(weights.sum(1)-1))<1e-5 and 'WEIGHTS_1' not in a
  area=np.linalg.norm(np.cross(pos[ix[:,1]]-pos[ix[:,0]],pos[ix[:,2]]-pos[ix[:,0]]),axis=1)/2;assert area.min()>1e-10
  if 'TEXCOORD_0' in a:
   uv=accessor_array(d,b,a['TEXCOORD_0']);du=uv[ix[:,1]]-uv[ix[:,0]];dv=uv[ix[:,2]]-uv[ix[:,0]];assert (abs(du[:,0]*dv[:,1]-du[:,1]*dv[:,0])>1e-10).all()
assert counts==[9486,4740,2369,1183]*2 and len(d['skins'][0]['joints'])==108 and len(d['images'])==4
expected=json.loads((P/'export/info.json').read_text())['clips'];assert {a['name'] for a in d['animations']}==set(expected)
for a in d['animations']:
 end=max(accessor_array(d,b,s['input']).max() for s in a['samplers']);assert abs(end-expected[a['name']])<1e-5
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m488_a','m488_b','m488_c']
for m in d['materials']:
 if 'pbrMetallicRoughness' not in m or 'metallicRoughnessTexture' not in m['pbrMetallicRoughness']:continue
 assert m['extras']['openyamm_specular_mask'] and m['pbrMetallicRoughness']['metallicFactor']==0
 im,_=image_of(d,b,m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']);assert np.array(im)[...,2].max()==0
source=json.loads((P/'reference/native_inventory.json').read_text())['sources']
for item in source.values():assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
report={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'triangles_by_mesh':counts,'bones':108,'max_influences':4,'uv_degenerate_faces':0,'clips':expected,'images':4,'original_sprites_unchanged':len(source)}
(P/'review/static_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
