from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1];B=P/'work/master_settled.blend';roles=['Standing','Walking','Running','Attack','Hit','Fidget','Death']
for name in ['g5_hand_stretch.py','jerk_probe.py','g6_head_clearance.py']:
 sys.argv=[name,'--',str(B),*roles];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
