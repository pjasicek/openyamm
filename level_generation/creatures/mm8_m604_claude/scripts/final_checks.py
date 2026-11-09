from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
os.environ['STEP']='0.5'
for n,args in [('export_parity.py',[]),('g4_weights.py',[p/'work/ready_final.blend','final_death',*[f'Death:{f/2}' for f in range(77)]]),('g5_hand_stretch.py',[p/'work/ready_final.blend','Death'])]:
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
