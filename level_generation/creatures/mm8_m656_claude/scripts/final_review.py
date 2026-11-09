import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('g4_weights.py',P/'work/master_settled.blend','delivered','Standing:0','Walking:12','Running:8','Attack:26','Fidget:14','Death:77')
run('g6_head_clearance.py',P/'work/master_settled.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget')
run('g6_sword_mesh.py',P/'export/mm8_m656_prepared.glb')
run('lod_visual.py')
