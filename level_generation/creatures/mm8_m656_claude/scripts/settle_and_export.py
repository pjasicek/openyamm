import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('equipment_floor.py')
run('g6_head_clearance.py',P/'work/master_settled.blend','Death','Fidget')
run('g6_contacts.py',P/'work/master_settled.blend','Death','Fidget')
run('jerk_probe.py',P/'work/master_settled.blend','Death','Fidget')
run('export_runtime.py')
run('g6_sword_mesh.py',P/'export/mm8_m656_lod0.glb')
