"""Verify the prepared viewer without opening a browser."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model
manifest=json.loads((V/'manifest.json').read_text());ids={m['id'] for m in manifest['models']};assert ids=={'lancer_a','lancer_b','lancer_c','forgemaster'}
roles={'Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'};counts={}
for info in manifest['models']:
 path=V/info['url'].split('?',1)[0];assert hashlib.sha256(path.read_bytes()).hexdigest()==info['sha256']
 model=Model(Glb(path));expected=roles|({'Cast'} if info['id']=='forgemaster' else set());assert set(info['clips'])==expected and set(model.clips)==expected
 for role,clip in info['clips'].items():assert abs(float(model.clip_times(role)[-1])-clip['duration'])<1e-5
 counts[info['id']]=len(expected)
imports=json.loads(re.search(r'<script type="importmap">(.*?)</script>',(V/'index.html').read_text(),re.S)[1])['imports']
assert all((V/url).resolve().exists() for url in imports.values())
subprocess.run(['node','--input-type=module','--check'],input=(V/'review.js').read_text(),text=True,check=True,capture_output=True)
result={'models':len(ids),'clips_per_model':counts,'hashes':True,'durations':True,'imports_exist':True,'javascript_syntax':True,'browser_opened':False}
(P/'review/viewer_static_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
