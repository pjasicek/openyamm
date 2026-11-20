"""The native tiers share one palette; their zero-coverage mask leaves the same base in the viewer."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
P=Path(__file__).resolve().parents[1]
assert not any(hi for lo,hi in Image.open(P/'textures/m616_region_mask.png').getextrema())
source=P/'export/mm8_m616_runtime_lod0.glb'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
path=P/'review/viewer/manifest.json';manifest=json.loads(path.read_text())
for model in manifest['models']:
 name='mm8_'+model['id']+'.glb'
 shutil.copyfile(source,P/'review/viewer'/name)
 model.update(sha256=digest,url=name+'?v='+digest[:12])
manifest['model_sha256']=digest
path.write_text(json.dumps(manifest,indent=2)+'\n')
print('VIEWER 3 shared-palette tiers',digest)
