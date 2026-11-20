from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for name,args in [('finish_hand_weights.py',[]),('source_fist.py',[]),('solve_fist.py',[str(p/'work/weighted_hands.blend'),'Attack','30','L']),('solve_fist.py',[str(p/'work/weighted_hands.blend'),'Attack','30','R']),('finish_hands.py',[]),('hand_review.py',[])]:
 path=p/'scripts'/name;sys.argv=[str(path),'--',*args];runpy.run_path(str(path),run_name='__main__')
