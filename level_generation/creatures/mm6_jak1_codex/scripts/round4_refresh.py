import sys,json,copy,hashlib,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];R=P/'review/round4';sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb
for script in ['round4_package.py','viewer_tiers.py','verify_exports.py']:
 subprocess.run([sys.executable,'-B',str(P/'scripts'/script)],check=True)
for key,path in [('accepted',R/'before/export/mm6_jak1_combined.glb'),('reduced',P/'export/mm6_jak1_combined.glb')]:
 d,b=read_glb(path)
 for level in range(4):
  doc=copy.deepcopy(d);next(n for n in doc['nodes']if n.get('name')=='Jackalman')['mesh']=level
  write_glb(P/f'work/round4/{key}_lod{level}.glb',doc,bytearray(b))
f=P/'review/viewer/manifest.json';m=json.loads(f.read_text());m['revision']='mm6_jak1_codex_review_round4_staff'
for row in m['models']:
 h=hashlib.sha256((P/f"review/viewer/mm6_{row['id']}.glb").read_bytes()).hexdigest();row.update(sha256=h,url=f"mm6_{row['id']}.glb?v={h[:12]}",revision=m['revision'])
m['model_sha256']=m['models'][0]['sha256'];f.write_text(json.dumps(m,indent=2))
