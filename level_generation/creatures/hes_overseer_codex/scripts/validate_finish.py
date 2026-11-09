"""Verify final exports against the accepted LOD0 and the loader contract."""
from pathlib import Path
import csv,hashlib,json,sys,subprocess,yaml
import numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from build_actor_lods import read_glb,accessor_bytes
from merge_head_material import accessor_array
report={'models':{},'loadouts':{},'accepted_lod0_preserved':True,'animation_samples_preserved':True}
for f in sorted((P/'export').glob('*.glb')):
 d,b=read_glb(f);nodes=d['nodes'];node=next(n for n in nodes if 'mesh'in n);base=d['meshes'][node['mesh']];extras=base.get('extras',{});chain=[node['mesh']]+extras.get('openyamm_lods',[])
 counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][mi]['primitives']) for mi in chain]
 assert all(a>c for a,c in zip(counts,counts[1:])),f
 for i,m in enumerate(d['meshes']):
  for key,most in [('openyamm_lods',3),('openyamm_shadow_lods',4)]:
   if key in m.get('extras',{}):
    v=m['extras'][key];assert 0<len(v)<=most and len(v)==len(set(v)) and all(0<=x<len(d['meshes']) and x!=i for x in v),(f,key,v)
  for p in m['primitives']:
   a=p['attributes'];pos=accessor_array(d,b,a['POSITION']);idx=accessor_array(d,b,p['indices']).reshape(-1,3)
   assert np.isfinite(pos).all() and idx.max()<len(pos)
   assert np.linalg.norm(np.cross(pos[idx[:,1]]-pos[idx[:,0]],pos[idx[:,2]]-pos[idx[:,0]]),axis=1).min()>1e-12,(f,m['name'],'degenerate')
   if 'WEIGHTS_0'in a:
    w=accessor_array(d,b,a['WEIGHTS_0']);assert np.isfinite(w).all() and np.max(abs(w.sum(1)-1))<1e-5
   if i in chain[1:] and 'TEXCOORD_0'in a:
    uv=accessor_array(d,b,a['TEXCOORD_0']);assert np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1,(f,'UV')
 for mat in d['materials']:
  assert not mat.get('extras',{}).get('openyamm_specular_mask') or 'metallicRoughnessTexture'in mat.get('pbrMetallicRoughness',{})
  assert 'emissiveTexture'not in mat
 body=f.stem in ['hes_overseer','hes_kreegan_winged'];source=P/('work/overseer_body_lod0.glb' if body else f'work/attachments/{f.name}')
 od,ob=read_glb(source);prims={od['materials'][p['material']]['name']:p for p in od['meshes'][0]['primitives']}
 for prim in base['primitives']:
  op=prims[d['materials'][prim['material']]['name']]
  for key in op['attributes']:assert accessor_bytes(d,b,prim['attributes'][key])==accessor_bytes(od,ob,op['attributes'][key]),(f,key)
  assert accessor_bytes(d,b,prim['indices'])==accessor_bytes(od,ob,op['indices'])
 assert nodes==od['nodes'],(f,'rig nodes')
 for s,os in zip(d.get('skins',[]),od.get('skins',[])):
  assert s['joints']==os['joints'] and accessor_bytes(d,b,s['inverseBindMatrices'])==accessor_bytes(od,ob,os['inverseBindMatrices'])
 assert len(d.get('animations',[]))==len(od.get('animations',[]))
 for a,oa in zip(d.get('animations',[]),od.get('animations',[])):
  assert a['name']==oa['name'] and a['channels']==oa['channels']
  for sm,om in zip(a['samplers'],oa['samplers']):
   for key in ['input','output']:assert accessor_bytes(d,b,sm[key])==accessor_bytes(od,ob,om[key])
 variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]
 assert variants==['ov_a','ov_b','ov_c','ov_krav','ov_ghulkat']
 winding=subprocess.run([sys.executable,str(ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),str(f)],text=True,capture_output=True,check=True)
 assert 'inverted closed parts: 0'in winding.stdout
 report['models'][f.name]={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'triangles':counts,'winding':winding.stdout.strip(),'variants':variants}
for row in yaml.safe_load((P/'integration/actors.yml').read_text()):
 d,b=read_glb(P/'export'/Path(row['model']).name);names={n['name'] for n in d['nodes']};clips={a['name'] for a in d['animations']}
 assert set(row['clips'].values())|{row['animation']['cast'],row['animation']['run']}<=clips
 assert set(row['animation']['sockets'].values())<=names
 parts=[Path(row['model']).name]+[Path(p['model']).name for p in row['attachments']]
 for p in row['attachments']:assert p['node']in names
 counts=[sum(report['models'][p]['triangles'][min(level,len(report['models'][p]['triangles'])-1)] for p in parts) for level in range(4)]
 assert counts[0]<=15000
 report['loadouts'][row['descriptor']]={'triangles':counts,'scale':row['scale'],'skin':row['skin']}
(P/'review/finish_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['loadouts'],indent=2))
