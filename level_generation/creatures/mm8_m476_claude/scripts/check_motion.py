from pathlib import Path
import runpy,sys,bpy,os
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
blend=p/'work/rig_v5.blend';actions=['Standing','Walking','Running','Attack','Hit','Fidget','Death']
run('g5_hand_stretch.py',blend,*actions)
os.environ['STEP']='0.5';run('sole_probe.py',blend,*actions)
run('g4_weights.py',blend,'v1',*[f'{a}:{f}' for a,n in [('Standing',60),('Walking',24),('Running',24),('Attack',24),('Hit',15),('Fidget',60),('Death',39)] for f in range(0,n+1,3)])
for view in ['front','left']:
 run('clip_sheet.py',blend,p/'review'/('motion_v2_'+view),view,'5',*actions)
run('inspect_club.py')
