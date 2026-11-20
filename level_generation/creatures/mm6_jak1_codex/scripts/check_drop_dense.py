import os,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.environ['CLIPS']='Death';sys.argv=['g6_staff_mesh.py','--',str(P/'export/mm6_jak1_runtime_lod0.glb')];runpy.run_path(str(P/'scripts/g6_staff_mesh.py'),run_name='__main__');d=json.loads((P/'work/g6_staff_mesh.json').read_text());assert d['Death']['depth_m']<=.002,d;print('DENSE DROP PASS',d,flush=True)
