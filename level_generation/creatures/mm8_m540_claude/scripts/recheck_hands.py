from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,args=()):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('build_rig.py')
run('hand_frame_check.py',[p/'work/rig_v1.blend'])
for side in ('R','L'):run('hand_xray.py',[p/'work/rig_v1.blend',side,p/'review'/('hand_'+side)])
