import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
run('floor_soles.py');run('clay_export.py');run('prepare_trace_reference.py')
run('g6_head_clearance.py',['work/production_body.blend',*roles]);run('g6_skirt_poke.py',['work/production_body.blend',*roles]);run('g6_sword_mesh.py',['work/knight_clay.glb'])
run('trace_export.py',['work/knight_clay.glb',*[f'{r}={P}/work/source_motion_reference.glb:{r}' for r in roles]])
