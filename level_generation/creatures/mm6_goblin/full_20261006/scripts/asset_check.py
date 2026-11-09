import sys,json,hashlib,math,io,subprocess
from pathlib import Path
from PIL import Image
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');R=O.parent;sys.path.insert(0,str(R/'blender_rebuild_20260928/authoring'));from check_glb import Glb
expected={'Standing':.125,'Walk':.750,'Attack':.750,'Hit':.750,'Death':.625,'Corpse':.125,'Fidget':.750};reports=[]
for pid in [745,746,747]:
 p=O/f'delivery/mm6_goblin_{pid}.glb';g=Glb(p);j=g.json;tris=verts=influences=0
 assert len(j['skins'])==1 and len(j['skins'][0]['joints'])==64
 assert not any('camera' in n or 'KHR_lights_punctual' in n.get('extensions',{}) for n in j['nodes'])
 for m in j['meshes']:
  for pr in m['primitives']:
   at=pr['attributes'];v=g.accessor(at['POSITION']);uv=g.accessor(at['TEXCOORD_0']) if 'TEXCOORD_0' in at else [];norm=g.accessor(at['NORMAL']);indices=g.accessor(pr['indices']);w=g.accessor(at['WEIGHTS_0']);joints=g.accessor(at['JOINTS_0'])
   assert 'TANGENT' in at if uv else not any('Texture' in key for key in j['materials'][pr['material']].get('pbrMetallicRoughness',{}));assert 'JOINTS_1' not in at;assert all(math.isfinite(q) for row in v for q in row);assert all(-1e-6<=q<=1.000001 for row in uv for q in row);assert all(abs(sum(q*q for q in n)-1)<.001 for n in norm);assert all(abs(sum(x)-1)<1e-4 for x in w);assert all(q<64 for row in joints for q in row);assert len(indices)%3==0 and max(q[0] for q in indices)<len(v)
   tris+=len(indices)//3;verts+=len(v);influences=max(influences,max(sum(q>1e-6 for q in row) for row in w))
 assert tris==14313 and influences<=4
 clips={}
 for a in j['animations']:
  times=[q[0] for s in a['samplers'] for q in g.accessor(s['input'])];assert abs(min(times))<1e-7;assert all(s.get('interpolation','LINEAR') in ['LINEAR','STEP'] for s in a['samplers']);clips[a['name']]=max(times);assert abs(clips[a['name']]-expected[a['name']])<1e-6
 assert clips.keys()==expected.keys()
 images=[]
 for im in j['images']:
  bv=j['bufferViews'][im['bufferView']];data=g.binary[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']];assert data.startswith(b'\x89PNG\r\n\x1a\n');i=Image.open(io.BytesIO(data));i.load();images.append({'name':im.get('name'),'format':i.format,'size':i.size})
 assert len(images)==4
 for mat in j['materials']:
  if any(role in mat['name'].lower() for role in ['skin','leather','teeth','eyes']):assert mat.get('pbrMetallicRoughness',{}).get('metallicFactor',1)==0
 cmd=['/tmp/openyamm_goblin_consumer_check',str(p)];r=subprocess.run(cmd,text=True,capture_output=True);assert r.returncode==0,(pid,r.stderr);print(r.stdout,flush=True)
 reports.append({'path':str(p.relative_to(O)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'triangles':tris,'split_vertices':verts,'joints':64,'maximum_influences':influences,'clips_seconds':clips,'images':images,'native_consumer_stdout':r.stdout,'native_consumer_121_samples_per_clip':'pass'})
(O/'delivery/asset_validation.json').write_text(json.dumps({'assets':reports,'bind_motion_comparison':'../review/export_reimport_checks.json','uv_validation':'uv_validation.json','scope':'Actual GLBs: skin, tangents, texture decoding, clip timing and native OpenYAMM loader/evaluator. No runtime installation or GPU rendering.'},indent=2)+'\n')
