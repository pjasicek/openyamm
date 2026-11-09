import json,hashlib,shutil,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(P.parent/'claude_shared'),str(R/'tools')]
import region_variants as rv
from merge_head_material import accessor_array
rv.apply_variants(P/'export/boulder_lods.glb',P/'export/mm8_m588.glb',P/'textures/boulder_ramps.json',[('Boulder','openyamm_specular',.12)])
d,b=rv.read_glb(P/'export/mm8_m588.glb');node=next(n for n in d['nodes'] if n.get('name')=='Body');mesh=d['meshes'][node['mesh']]
levels=[node['mesh']]+mesh['extras']['openyamm_lods'];triangles=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in levels]
assert len(mesh['extras']['openyamm_shadow_lods'])==4 and len(d['skins'][0]['joints'])==34
assert all(a>b for a,b in zip(triangles,triangles[1:]))
for m in d['meshes']:
 assert len(m['primitives'])==1
 attrs=m['primitives'][0]['attributes'];weights=accessor_array(d,b,attrs['WEIGHTS_0']);assert np.max(abs(weights.sum(1)-1))<1e-6
 assert np.all((weights>.001).sum(1)==1)
durations={a['name']:max(float(accessor_array(d,b,s['input']).max()) for s in a['samplers']) for a in d['animations']}
assert len(durations)==7 and abs(durations['Hit']-.625)<1e-6
v=P/'review/viewer';shutil.copy2(P/'export/boulder_portable.glb',v/'boulder.glb');h=hashlib.sha256((v/'boulder.glb').read_bytes()).hexdigest()
m=json.loads((v/'manifest.json').read_text());m['revision']='boulder_textured_v2';m['default_model']='boulder_a';m['models']=[{'id':f'boulder_{t}','label':f'Malevolent Boulder {t.upper()} · {scale:.2f}×','scale':scale,'revision':m['revision'],'url':'boulder.glb?v='+h[:12],'sha256':h} for t,scale in zip('abc',[1,1.299988,1.699997])]
for name in durations:assert abs(m['clips'][name]['duration']-durations[name])<1e-5
(v/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
j=(v/'review.js').read_text().replace('model=gltf.scene;model.animations=', 'model=gltf.scene;model.scale.setScalar(info.scale);model.animations=').replace('body:[0,1,0,4.3]','body:[0,1.45,0,7.0]')
j=j.replace('m=>m.sha256===s.model_sha256','m=>m.id===s.model_id&&m.sha256===s.model_sha256').replace('m=>m.sha256===initialPose?.model_sha256','m=>m.id===initialPose?.model_id&&m.sha256===initialPose?.model_sha256')
(v/'review.js').write_text(j)
report={'triangles':triangles,'bones':34,'rigid_influences':1,'clips':durations,'runtime_sha256':hashlib.sha256((P/'export/mm8_m588.glb').read_bytes()).hexdigest(),'portable_sha256':h,'all_tiers_palette':588}
(P/'work/package_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
