"""Transfer only the verified Attack channels into the existing measured LODs."""
import hashlib,json,sys,shutil
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];W=P/'work';A=W/'before_strike_20261024'
sys.path.insert(0,str(P.parent/'claude_shared/floor'));from glb_pose import Glb
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=Glb(A/'export/hes_forgemaster_lod0.glb');new=Glb(P/'export/hes_forgemaster_lod0.glb')
for key in ('nodes','skins','materials','textures','samplers'):assert old.json.get(key)==new.json.get(key),key
assert len(old.json['meshes'])==len(new.json['meshes'])
for ma,mb in zip(old.json['meshes'],new.json['meshes']):
 assert len(ma['primitives'])==len(mb['primitives'])
 for a,b in zip(ma['primitives'],mb['primitives']):
  assert a['attributes'].keys()==b['attributes'].keys()
  for key in a['attributes']:assert np.array_equal(old.accessor(a['attributes'][key]),new.accessor(b['attributes'][key])),key
  assert np.array_equal(old.accessor(a['indices']),new.accessor(b['indices']))
def images(g):
 for image in g.json['images']:
  v=g.json['bufferViews'][image['bufferView']];yield bytes(g.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
assert list(images(old))==list(images(new))
def channels(g):return {(a['name'],g.json['nodes'][c['target']['node']]['name'],c['target']['path']):a['samplers'][c['sampler']] for a in g.json['animations'] for c in a['channels']}
a,b=channels(old),channels(new);assert a.keys()==b.keys();changed=[k for k in a if any(not np.array_equal(old.accessor(a[k][x]),new.accessor(b[k][x])) for x in ('input','output'))]
assert changed and all(k[0]=='Forge_Attack' for k in changed),changed
paths=[W/'hes_forgemaster_near.glb',W/'hes_forgemaster_far.glb',W/'lodrep_hes_forgemaster/r45_25.glb'];outputs=[]
for path in paths:
 archive=A/path.relative_to(P)
 if not archive.exists():archive.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,archive)
 g=Glb(path);cs=channels(g)
 for key in changed:
  sampler=cs[key]
  for name in ('input','output'):
   assert np.array_equal(g.accessor(sampler[name]),old.accessor(a[key][name])),(path,key,name)
   sampler[name]=g.append_accessor(new.accessor(b[key][name]),new.json['accessors'][b[key][name]]['type'])
 outputs.append((path,g))
for path,g in outputs:g.write(path)
record={'geometry_weights_uvs_materials_images_nodes_and_other_animations_identical':True,'changed_channels':[list(k) for k in changed],'old_near_sha256':hashfile(A/'work/hes_forgemaster_near.glb'),'new_near_sha256':hashfile(W/'hes_forgemaster_near.glb'),'raw_before_sha256':hashfile(A/'export/hes_forgemaster_lod0.glb'),'raw_after_sha256':hashfile(P/'export/hes_forgemaster_lod0.glb'),'standing_and_lod_audit_unchanged':True}
(P/'review/forge_slam_lod_equivalence.json').write_text(json.dumps(record,indent=2)+'\n')
path=W/'lodrep_hes_forgemaster/result.json';j=json.loads(path.read_text());assert j['source_sha256']==record['old_near_sha256'];j.setdefault('geometry_audit_source_sha256',j['source_sha256']);j['source_sha256']=record['new_near_sha256'];j.setdefault('animation_only_updates',[]).append('review/forge_slam_lod_equivalence.json');path.write_text(json.dumps(j,indent=2)+'\n')
print('SLAM_LOD_EQUIVALENCE',len(changed),'Attack channels; geometry, materials and all other clips identical')
