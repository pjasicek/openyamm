from pathlib import Path
import runpy,sys,os,json
p=Path(__file__).resolve().parents[1]
def run(n,args):
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
acts=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
os.environ['STEP']='0.5'
run('measure_runtime.py',[])
run('sole_probe.py',[p/'work/ready_final.blend',*acts])
run('jerk_probe.py',[p/'work/ready_final.blend',*acts])
picks=[f'{n}:{f}' for n,end in [('Standing',90),('Walking',24),('Running',22),('Attack',52),('Hit',24),('Death',38),('Fidget',78)] for f in [0,end*.25,end*.5,end*.75,end]]
picks += [f'Attack:{f/2}' for f in range(52,69)]
run('g4_weights.py',[p/'work/ready_final.blend','final',*picks])
run('g5_hand_stretch.py',[p/'work/ready_final.blend',*acts])
run('g6_sword_surface.py',[p/'export/mm8_m604.blend',*acts])

run('loop_probe.py',[])
