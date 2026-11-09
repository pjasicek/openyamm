from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for n,a in [('finger_joints.py',[p/'work/rig_v1.blend']),('build_rig.py',[]),('hand_xray.py',[p/'work/rig_v1.blend','R',p/'review/thumb_base'])]:
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in a]];runpy.run_path(str(s),run_name='__main__')
runpy.run_path(str(p/'scripts/build_motion.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/refine_grip.py'),run_name='__main__')
