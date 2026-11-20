from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
acts=['Standing','Walking','Hit','Fidget','Death']
for view in ['front','left','three_quarter']:
 run('clip_sheet.py',p/'work/weighted_v1.blend',p/('review/motion_v1_'+view),view,5,*acts)
run('g4_weights.py',p/'work/weighted_v1.blend','motion_v1','Standing:0','Walking:8','Walking:25','Hit:4','Hit:10','Fidget:30','Death:20')
run('g5_hand_stretch.py',p/'work/weighted_v1.blend',*acts)
