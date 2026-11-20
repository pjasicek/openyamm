from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
def run(n,args):
 f=P/'scripts'/n;sys.argv=[str(f),'--',*map(str,args)];runpy.run_path(str(f),run_name='__main__')
run('joint_xray.py',[P/'work/step1.blend','Body',P/'work/joints_final.json',P/'review/joints',P/'work/meshy_joints.json'])
run('hand_frame_check.py',[P/'work/rig_v1.blend'])
for s in ['L','R']:run('hand_xray.py',[P/'work/rig_v1.blend',s,P/f'review/hand_{s}'])
