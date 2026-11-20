"""Point the existing review UI at the actual textured export and validate all local dependencies."""
import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1];v=P/'review/viewer';asset=v/'hes_brood_mother.glb';h=hashlib.sha256(asset.read_bytes()).hexdigest()
m=json.loads((v/'manifest.json').read_text());revision='hes_brood_mother_textured_'+h[:12]
m.update(revision=revision,status='textured_runtime_ready_for_integrator',default_model='hbm')
m['models']=[{'id':'hbm','label':'Brood Mother — queen/cradle, three empty sockets','revision':revision,'url':'hes_brood_mother.glb?v='+h[:12],'sha256':h}]
(v/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(v/'README.md').write_text('''# Brood Mother review

The existing viewer loads `hes_brood_mother.glb`: viewer-only baked `hbm` ramps from the staged runtime model.
All six clips and durations are in the hash-bound manifest. The runtime keeps shared textures and region ramps.
No eggs are included. Browser playback/capture remains with the integrator under CREATURE_BUILDS rule 9.

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/hes_brood_mother_codex check
```

Inspect Standing, Fidget, Attack, Hit, Death and Dead at normal and half speed, then horn tips, shoulders,
fingers, belly/cradle separation, pads and face close-up. Offline textured views are in `../textured_final_*`.
D9 still needs its three sac actors moved onto the recorded sockets; see the project README.
''')
js=(v/'review.js').read_text()
for path in re.findall(r"from ['\"]([^'\"]+)['\"]",js):
 if path.startswith('.'):assert (v/path).resolve().exists(),path
for clip in m['clips'].values():
 for a in clip.get('anchors',[]):
  for path in a.get('source_images',[]):assert (v/path).resolve().exists()
assert isinstance(json.loads((v/'feedback/user_feedback.json').read_text())['findings'],list)
report={'viewer_sha256':h,'runtime_sha256':hashlib.sha256((P/'export/hes_brood_mother.glb').read_bytes()).hexdigest(),'local_dependencies':'pass','clips':list(m['clips']),'browser_run':False,'owner':'integrator'}
(P/'review/viewer_static_check.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
