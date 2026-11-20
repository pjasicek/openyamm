"""Validate exported runtime contracts, retained source anatomy and bindings."""
from pathlib import Path
from collections import Counter
import json,sys,numpy as np,yaml,hashlib,subprocess,io
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,accessor_array
E=P/'export';report={}
source,sb=read_glb(P/'source/hes_kreegan.glb');body,bb=read_glb(E/'hes_harrower.glb')
native={a['name'] for a in source['animations']};assert native<={a['name'] for a in body['animations']}
assert len(body['animations'])==30
names={n.get('name') for n in body['nodes']};assert {n.get('name') for n in source['nodes'] if 'mesh' not in n}<=names
# Original compatibility clips remain byte-identical in their sampler data and target native bones.
original_clips={a['name']:a for a in body['animations']}
for original in source['animations']:
 exported=original_clips[original['name']]
 assert len(original['samplers'])==len(exported['samplers'])
 for a,b in zip(original['samplers'],exported['samplers']):
  assert a.get('interpolation','LINEAR')==b.get('interpolation','LINEAR')
  for key in ('input','output'):
   assert np.array_equal(accessor_array(source,sb,a[key]),accessor_array(body,bb,b[key])),(original['name'],key)
 def targets(d,a):
  return [(c['sampler'],d['nodes'][c['target']['node']]['name'].replace('HKR','HHW'),c['target']['path']) for c in a['channels']]
 assert targets(source,original)==targets(body,exported)
for node in source['nodes']:
 if 'mesh' in node:continue
 match=next(n for n in body['nodes'] if n.get('name')==node.get('name'))
 for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
  assert np.allclose(node.get(key,default),match.get(key,default),atol=1e-6),node.get('name')
# Blender's coordinate round-trip changes positions by at most two micrometres; compare actual topology
# through nearest source positions instead of rounded coordinates (which can straddle a rounding boundary).
from scipy.spatial import cKDTree
def original_triangles(d,b):
 node=next(n for n in d['nodes'] if 'skin' in n and 'mesh' in n);parts=[]
 for pr in d['meshes'][node['mesh']]['primitives']:
  name=d['materials'][pr['material']]['name']
  if name.startswith('HHW_') and not name.startswith('HHW_Skin'):continue
  pos=accessor_array(d,b,pr['attributes']['POSITION']);ix=accessor_array(d,b,pr['indices']).reshape(-1,3);parts.append(pos[ix])
 return np.concatenate(parts)
a=original_triangles(source,sb);b=original_triangles(body,bb);assert a.shape==b.shape==(9408,3,3)
points,indices=np.unique(a.reshape(-1,3),axis=0,return_inverse=True)
distance,mapped=cKDTree(points).query(b.reshape(-1,3))
assert distance.max()<2e-6,distance.max()
assert Counter(map(tuple,np.sort(indices.reshape(-1,3),axis=1)))==Counter(map(tuple,np.sort(mapped.reshape(-1,3),axis=1))),'Shared-body topology changed'
report['source_geometry_roundtrip_max_m']=float(distance.max())
# Compare native skin weights by position and bone name, allowing the extra UV seam splits made by Blender.
def native_weights(d,b,native_names):
 node=next(n for n in d['nodes'] if 'skin' in n and 'mesh' in n);sk=d['skins'][node['skin']]
 joint_names=[d['nodes'][j]['name'] for j in sk['joints']];positions=[];weights=[]
 for pr in d['meshes'][node['mesh']]['primitives']:
  name=d['materials'][pr['material']]['name']
  if name.startswith('HHW_') and not name.startswith('HHW_Skin'):continue
  pos=accessor_array(d,b,pr['attributes']['POSITION']);j=accessor_array(d,b,pr['attributes']['JOINTS_0']);w=accessor_array(d,b,pr['attributes']['WEIGHTS_0'])
  dense=np.zeros((len(pos),len(native_names)))
  for col in range(j.shape[1]):
   for ident in np.unique(j[:,col]):
    hit=j[:,col]==ident;bone=joint_names[ident]
    if bone in native_names:dense[hit,native_names.index(bone)]+=w[hit,col]
    else:assert np.max(w[hit,col])<1e-7,(name,bone)
  positions.append(pos);weights.append(dense)
 return np.concatenate(positions),np.concatenate(weights)
native_names=[source['nodes'][j]['name'] for j in source['skins'][0]['joints']]
sp,sw=native_weights(source,sb,native_names);bp,bw=native_weights(body,bb,native_names)
neighbors=cKDTree(sp).query_ball_point(bp,2e-6);max_weight_error=0
for i,near in enumerate(neighbors):
 assert near
 error=np.max(np.abs(sw[near]-bw[i]),axis=1).min();assert error<2e-6,(i,error)
 max_weight_error=max(max_weight_error,float(error))
report['source_weight_roundtrip_max']=max_weight_error
report['rig']={'native_bones':len(native_names),'total_bones':len(body['skins'][0]['joints']),'native_clip_sampler_data':'exactly preserved'}

for path in sorted(E.glob('*.glb')):
 d,b=read_glb(path);assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['hhw_a','hhw_b','hhw_c','hhw_boss'];assert all('emissiveTexture' not in m for m in d['materials']);assert all('bufferView' in im for im in d.get('images',[]))
 for m in d['materials']:
  emission=m.get('emissiveFactor',[0,0,0]);strength=m.get('extensions',{}).get('KHR_materials_emissive_strength',{}).get('emissiveStrength',1)
  assert all(np.isfinite(x) and 0<=x<=1 for x in emission) and 0<=strength<=16,(path.name,m['name'])
  if m['name'].startswith(('HHW_Cloth_','HHW_Mantle_')):
   image=d['images'][d['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']];view=d['bufferViews'][image['bufferView']];off=view.get('byteOffset',0)
   rgba=Image.open(io.BytesIO(b[off:off+view['byteLength']])).convert('RGBA');alpha=rgba.getchannel('A').getextrema()
   assert alpha[0]<128 and alpha[1]>128,(path.name,m['name'],'cloth alpha lost',alpha)
 # Mirror the loader contract, including every mesh rather than just visible nodes.
 for mi,mesh in enumerate(d['meshes']):
  for key,maximum in (('openyamm_lods',3),('openyamm_shadow_lods',4)):
   chain=mesh.get('extras',{}).get(key)
   if chain is not None:
    assert 0<len(chain)<=maximum,(path.name,mi,key,chain)
    assert len(set(chain))==len(chain) and all(0<=i<len(d['meshes']) and i!=mi for i in chain),(path.name,mi,key,chain)
 chains=[]
 for n in d['nodes']:
  if 'mesh' not in n:continue
  base=n['mesh'];chain=[base,*d['meshes'][base].get('extras',{}).get('openyamm_lods',[])]
  counts=[sum(d['accessors'][pr['indices']]['count']//3 for pr in d['meshes'][i]['primitives']) for i in chain];assert all(x>y for x,y in zip(counts,counts[1:])),(path.name,counts);chains.append(counts)
 report[path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':chains,'bytes':path.stat().st_size}
rows=yaml.safe_load((P/'integration/actors.yml').read_text());assert len(rows)==4
for row in rows:
 refs=list(row['clips'].values())+[row['animation']['run'],*row['animation']['script_clips'].values()];assert set(refs)<={a['name'] for a in body['animations']}
 total=report['hes_harrower.glb']['triangles'][0][0]
 for item in row['attachments']:
  assert item['node'] in names;total+=report[Path(item['model']).name]['triangles'][0][0]
 assert total<=15000,(row['descriptor'],total);report[row['descriptor']]={'assembled_lod0_triangles':total}
command=[sys.executable,str(ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),*[str(x) for x in sorted(E.glob('*.glb'))]]
r=subprocess.run(command,text=True,capture_output=True);(P/'review/winding.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout[-2000:]
report['shared_body']={'retained_triangles':9408,'tail_and_harness':True,'original_clips':sorted(native),'source_sha256':hashlib.sha256((P/'source/hes_kreegan.glb').read_bytes()).hexdigest()}
(P/'review/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if isinstance(v,dict) and 'assembled_lod0_triangles' in v}))
