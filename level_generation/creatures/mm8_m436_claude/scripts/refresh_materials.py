from pathlib import Path
import runpy,hashlib,json,subprocess
p=Path(__file__).resolve().parents[1]
for n in ['compose_textures.py','finish_runtime.py','viewer_tiers.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
f=p/'review/viewer/manifest.json';d=json.loads(f.read_text());d['revision']='m436_civilian_v3'
for m in d['models']:
 name=m['url'].split('?')[0];h=hashlib.sha256((f.parent/name).read_bytes()).hexdigest();m.update(revision=d['revision'],url=name+'?sha256='+h,sha256=h)
f.write_text(json.dumps(d,indent=2)+'\n')
