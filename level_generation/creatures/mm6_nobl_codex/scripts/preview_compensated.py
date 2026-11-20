import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('prepare_clips.py');run('clip_timing.py')
os.environ['TWIST_POSE_ONLY']='1';run('twist_bones.py',[p/'work/rig_v6t.blend',p/'work/rig_v6t.blend']);del os.environ['TWIST_POSE_ONLY']
run('g4_weights.py',[p/'work/rig_v6t.blend','compensated',*[f'Attack:{i}' for i in range(37)],*[f'Running:{i}' for i in range(25)]])
run('clip_sheet.py',[p/'work/rig_v6t.blend',p/'review/compensated','three_quarter','6','Attack','Running'])
