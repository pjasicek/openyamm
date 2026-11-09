import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['weights_body.py','--',str(p/'work/rig_fingers.blend'),str(p/'work/rig_fingers.blend')]
runpy.run_path(str(p/'scripts/weights_body.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/posture_timing.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/fit_diagonal_grip.py'),run_name='__main__')
