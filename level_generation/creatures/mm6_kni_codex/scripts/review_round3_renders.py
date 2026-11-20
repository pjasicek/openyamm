import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name,args in [('render_final.py',[]),('glb_hand_closeups.py',[P/'review/viewer/mm6_kni_a.glb',P/'review/round3/hand','Standing:0','Attack:0.71875','Death:0.291667'])]:
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
