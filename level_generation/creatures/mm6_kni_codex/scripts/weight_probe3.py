import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('armour_weights.py');run('finger_weights.py',['work/rig_v3.blend','work/rig_v4.blend']);run('apply_grip.py',['work/rig_v4.blend','work/rig_v6.blend']);run('clip_timing.py')
run('g4_weights.py',['work/rig_v6t.blend','probe3','Attack:10','Hit:6','Fidget:30'])
run('clay_export.py');run('g6_sword_mesh.py',['work/knight_clay.glb'])
