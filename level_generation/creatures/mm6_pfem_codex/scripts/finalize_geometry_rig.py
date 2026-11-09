import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/prepare_rig_upload.py'),run_name='__main__')
sys.argv=['arm_rings.py','--',str(p/'work/step1.blend')]
runpy.run_path(str(p/'scripts/arm_rings.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/five_finger_cleanup.py'),run_name='__main__')
