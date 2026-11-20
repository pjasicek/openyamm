import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('posture_blade.py');run('render_final.py');run('glb_hand_closeups.py',['review/viewer/mm6_kni_a.glb','review/final_hand','Standing:0','Attack:0.719'])
