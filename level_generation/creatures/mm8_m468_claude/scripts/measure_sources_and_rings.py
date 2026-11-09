from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/source_motion_limits.py'),run_name='__main__')
sys.argv=['fit_joints.py','--',str(p/'work/step1.blend'),'Body'];runpy.run_path(str(p/'scripts/fit_joints.py'),run_name='__main__')
