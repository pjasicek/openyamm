import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['weights_body.py','--',str(p/'work/rig_twist.blend'),str(p/'work/rig_weighted_final.blend')]
runpy.run_path(str(p/'scripts/weights_body.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/prepare_surface_cost.py'),run_name='__main__')
