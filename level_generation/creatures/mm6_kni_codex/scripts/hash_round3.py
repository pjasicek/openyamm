"""Hash the delivered round-3 package; leave prior rounds and their receipts untouched."""
from pathlib import Path
import hashlib,json,re,ast
P=Path(__file__).resolve().parents[1];R=P/'review/round3'
files=set()
for pattern in ['export/*.glb','textures/round3/*.png','scripts/*round3*','review/round3/*','review/viewer/*.glb','review/clips_*.jpg','work/round3/rebaked_l*.blend','work/round3/geometry_body_l*.glb']:
 files.update(p for p in P.glob(pattern)if p.is_file())
files.update(P/n for n in ['README.md','HANDOFF.md','creature_3d_progress.json','integration/actors.yml','review/viewer/manifest.json'])
files.discard(R/'files.json')
records={str(p.relative_to(P)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in sorted(files)}
(R/'files.json').write_text(json.dumps(records,indent=2)+'\n')
for f in [P/'README.md',P/'HANDOFF.md',R/'README.md']:
 for link in re.findall(r'\]\(([^)]+)\)',f.read_text()):
  link=link.split('#')[0]
  if link and not link.startswith(('http:','https:')):assert(f.parent/link).exists(),(f,link)
for f in P.glob('scripts/*round3.py'):ast.parse(f.read_text(),filename=str(f))
progress=json.loads((P/'creature_3d_progress.json').read_text());baseline=json.loads((P/'work/round3/baseline_creature_3d_progress.json').read_text())
assert progress['meshy']==baseline['meshy']
audit=json.loads((R/'export_validation.json').read_text())
for n in ['mm6_kni','mm6_kni_sword','viewer_a','viewer_b','viewer_c']:
 assert records[audit[n]['file']]['sha256']==audit[n]['sha256']
assert records['integration/actors.yml']['sha256']==audit['actors_yml']['sha256']
print(json.dumps({'files_hashed':len(records),'local_links':'PASS','round3_python_syntax':'PASS','credit_receipts':'unchanged','export_audit_hashes':'match','actors_unchanged':True}))
