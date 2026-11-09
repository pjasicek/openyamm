"""Validate the selected runtime export and bind the three existing peasant descriptors."""
import json,sys,struct,io,shutil,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(Path('tools').resolve()))
from build_actor_lods import read_glb,accessor_bytes
d,b=read_glb(E/'mm6_fmp.glb');s,sb=read_glb(E/'mm6_fmp_runtime_lod0.glb');info=json.loads((E/'export_info.json').read_text())
assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==90
assert {a['name'] for a in d['animations']}==set(info['clips']) and 'Attack' not in info['clips']
assert all('Finger' not in n.get('name','') and not n.get('name','').startswith('Socket_') for n in d['nodes'])
assert len(d['materials'])==3 and all(not m.get('doubleSided',False) for m in d['materials'])
assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['fmp_a','fmp_b','fmp_c']
node=next(n for n in d['nodes'] if n.get('name')=='PeasantF2');base=d['meshes'][node['mesh']];lods=[node['mesh'],*base['extras']['openyamm_lods']];tri=[];weights=0
for mi in lods:
 mesh=d['meshes'][mi];assert len(mesh['primitives'])==1
 p=mesh['primitives'][0];tri.append(d['accessors'][p['indices']]['count']//3);at=p['attributes'];w=[]
 for n in ['WEIGHTS_0','WEIGHTS_1']:
  if n in at:w.append(np.frombuffer(accessor_bytes(d,b,at[n]),np.float32).reshape(-1,4))
 w=np.concatenate(w,axis=1);assert np.isfinite(w).all() and np.abs(w.sum(1)-1).max()<.0001
 weights=max(weights,int((w>1e-6).sum(1).max()));assert weights<=8
assert tri==[9902,4948,1779,592],tri
for a in d['animations']:
 original=next(x for x in s['animations'] if x['name']==a['name']);assert a['channels']==original['channels']
 for x,y in zip(a['samplers'],original['samplers']):
  for k in ['input','output']:assert accessor_bytes(d,b,x[k])==accessor_bytes(s,sb,y[k])
images=[]
for im in d['images']:
 v=d['bufferViews'][im['bufferView']];o=v.get('byteOffset',0);size=Image.open(io.BytesIO(b[o:o+v['byteLength']])).size;images.append(size);assert size==(2080,1024),size
report={'triangles':tri,'shadow_lods':base['extras']['openyamm_shadow_lods'],'materials':len(d['materials']),'images':images,'bones':90,'max_influences':weights,'animations_preserved':True,'sha256':hashlib.sha256((E/'mm6_fmp.glb').read_bytes()).hexdigest()}
(P/'work/runtime_asset_audit.json').write_text(json.dumps(report,indent=2));print(report)
dest=Path('assets_dev/worlds/mm6/models');shutil.copy2(E/'mm6_fmp.glb',dest/'mm6_fmp.glb')
assert (dest/'mm6_fmp.glb').read_bytes()==(E/'mm6_fmp.glb').read_bytes()
f=dest/'actors.yml';current=f.read_text()
text='\n# MM6 PeasantF2 A/B/C (fmp, IDs 598-600): Wimp AI; no attack clip or weapon.\n'
for tier in 'ABC':
 text+=f'''- descriptor: PeasantF2 {tier}
  model: worlds/mm6/models/mm6_fmp.glb
  scale: {info['scale']:.12f}
  yaw_offset: -1.570796327
  skin: fmp_{tier.lower()}
  animation:
    cast: Standing
    run: Run
    stride_length: {info['walk_stride_m']:.12f}
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 60
      max_pitch_degrees: 35
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Standing
    attack_ranged: Standing
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget

'''
if 'descriptor: PeasantF2 ' in current:
 assert text.strip() in current
else:f.write_text((current+text).rstrip()+'\n')
