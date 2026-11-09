from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(name,args):
 sys.argv=[str(p/'scripts'/name),'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
os.environ.update(FA='0.6',FA_RAMP='0.15,0.85',FRADIUS='0.016',R_HANDLE='0.012',GRIP_TILT='0')
run('twist_bones.py',[p/'work/rig_v2timed.blend',p/'work/rig_v2t.blend'])
run('weights_fix.py',[p/'work/rig_v2t.blend',p/'work/rig_v3.blend'])
run('finger_weights.py',[p/'work/rig_v3.blend',p/'work/rig_v4f.blend'])
run('grip_solve.py',[p/'work/rig_v4f.blend','GripRef','8'])
run('apply_grip.py',[p/'work/rig_v4f.blend',p/'work/rig_v5.blend'])
