import runpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('posture.py');run('final_gates.py');run('make_lods.py');run('render_final.py');run('glb_hand_closeups.py',[P/'review/viewer/mm6_jak1_a.glb',P/'review/final_hand','Standing:0','Attack:0.677083','Cast:0.733333','Death:1.3'])
