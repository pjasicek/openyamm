import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['arm_rings.py','--',str(p/'work/step1.blend')]
runpy.run_path(str(p/'scripts/arm_rings.py'),run_name='__main__')
sys.argv=['joint_xray.py','--',str(p/'work/step1.blend'),'Body',str(p/'work/joints_final.json'),str(p/'review/joints'),str(p/'work/meshy_joints.json')]
runpy.run_path(str(p/'scripts/joint_xray.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/build_rig.py'),run_name='__main__')
sys.argv=['fit_fingers.py','--',str(p/'work/rig_v1.blend')]
runpy.run_path(str(p/'scripts/fit_fingers.py'),run_name='__main__')
