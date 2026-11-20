"""Normalize and inspect this selected Smart Topology return without changing its original."""
import os,sys,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.chdir(p);sys.path.insert(0,str(p/'scripts'));sys.dont_write_bytecode=True
sys.argv=['examine_parts.py','--','meshy/body_geometry_v1/model_urls_glb.glb','st_v1']
runpy.run_path(str(p/'scripts/examine_parts.py'),run_name='__main__')
r=json.loads((p/'work/st_v1_parts.json').read_text())
assert r and sum(x['tris'] for x in r)>1000
print('BODY_TOTAL',sum(x['verts'] for x in r),'verts',sum(x['tris'] for x in r),'triangles',len(r),'parts')
