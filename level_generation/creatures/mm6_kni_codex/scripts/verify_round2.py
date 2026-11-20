"""Semantic preservation and all-LOD export audit for the reduction handoff."""
import sys,numpy as np,hashlib,json,copy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2';R=P/'review/round2';sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,TEXTURE_SLOTS,slot
report={}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def image_bytes(d,b,i):
 v=d['bufferViews'][d['images'][i]['bufferView']];s=v.get('byteOffset',0);return bytes(b[s:s+v['byteLength']])
def clips(d,b,o,ob):
 assert d['nodes']==o['nodes'];assert len(d['animations'])==len(o['animations'])==8
 assert d['skins'][0]['joints']==o['skins'][0]['joints']
 assert np.array_equal(accessor_array(d,b,d['skins'][0]['inverseBindMatrices']),accessor_array(o,ob,o['skins'][0]['inverseBindMatrices']))
 for a,aa in zip(d['animations'],o['animations']):
  assert a['name']==aa['name'] and a['channels']==aa['channels'] and len(a['samplers'])==len(aa['samplers'])
  for s,ss in zip(a['samplers'],aa['samplers']):
   assert s.get('interpolation')==ss.get('interpolation')
   for k in ['input','output']:assert np.array_equal(accessor_array(d,b,s[k]),accessor_array(o,ob,ss[k]))
for name,expected in [('mm6_kni',[11100,5980,2314,697]*2),('mm6_kni_sword',[1985,1131,451,180])]:
 path=P/f'export/{name}.glb';d,b=read_glb(path);o,ob=read_glb(W/f'baseline_{name}.glb')
 assert d['nodes']==o['nodes'] and d['materials']==o['materials'];assert len(d['images'])==len(o['images'])
 assert all(image_bytes(d,b,i)==image_bytes(o,ob,i)for i in range(len(d['images'])))
 if 'skins'in d:clips(d,b,o,ob)
 maxerr=0;counts=[]
 for m in d['meshes']:
  count=0
  for q in m['primitives']:
   a={k:accessor_array(d,b,v)for k,v in q['attributes'].items()};ix=accessor_array(d,b,q['indices']).ravel();assert ix.max()<len(a['POSITION']) and ix.size%3==0;count+=len(ix)//3
   assert all(np.isfinite(v).all()for v in a.values());assert np.allclose(np.linalg.norm(a['NORMAL'],axis=1),1,atol=1e-5)
   if 'WEIGHTS_0'in a:
    err=float(np.max(abs(sum(v.sum(axis=1)for k,v in a.items()if k.startswith('WEIGHTS_'))-1)));assert err<1e-4;maxerr=max(maxerr,err)
    assert len([k for k in a if k.startswith('WEIGHTS_')])<=2
  counts.append(count)
 assert counts==expected
 if name=='mm6_kni_sword':
  assert not d.get('skins') and not d.get('animations');q=d['meshes'][0]['primitives'][0];pos=accessor_array(d,b,q['attributes']['POSITION']);tip_error=float(np.max(abs(pos[np.argmax(pos[:,1])]-[.18,.85,0])));assert tip_error<1e-6
  assert len(d['images'])==3 and len(d['materials'])==1
 else:tip_error=None
 report[name]={'file':str(path.relative_to(P)),'sha256':digest(path),'bytes':path.stat().st_size,'triangles':counts,'weight_max_error':maxerr,'tip_error_m':tip_error,'nodes_materials_images_exact':True,'animations_and_inverse_binds_exact':name=='mm6_kni'}
for tier in 'abc':
 path=P/f'review/viewer/mm6_kni_{tier}.glb';d,b=read_glb(path);o,ob=read_glb(W/f'baseline_mm6_kni_{tier}.glb');clips(d,b,o,ob)
 old=o['materials'][o['meshes'][0]['primitives'][0]['material']];new=d['materials'][d['meshes'][0]['primitives'][0]['material']];old=copy.deepcopy(old);new=copy.deepcopy(new)
 for route in TEXTURE_SLOTS:
  a,c=slot(old,route),slot(new,route);assert (a is None)==(c is None)
  if a is not None:
   assert image_bytes(o,ob,o['textures'][a['index']]['source'])==image_bytes(d,b,d['textures'][c['index']]['source']);a['index']=c['index']=0
 assert old==new
 report['viewer_'+tier]={'file':str(path.relative_to(P)),'sha256':digest(path),'bytes':path.stat().st_size,'triangles':sum(d['accessors'][q['indices']]['count']//3 for q in d['meshes'][0]['primitives']),'clips_and_tier_materials_exact':True}
baseline=json.loads((R/'baseline.json').read_text());assert digest(P/'integration/actors.yml')==baseline['integration/actors.yml']['sha256'];report['actors_yml']={'changed':False,'sha256':digest(P/'integration/actors.yml')}
res=subprocess.run([sys.executable,str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],text=True,capture_output=True);(R/'check_bindings.txt').write_text(res.stdout+res.stderr);assert res.returncode==0 and 'BAD' not in res.stdout+res.stderr;report['check_bindings']='PASS: no BAD line'
(R/'export_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
