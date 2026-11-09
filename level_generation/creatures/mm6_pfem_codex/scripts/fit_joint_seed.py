import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['meshy_joints.py','--',str(p/'source/rig_seed_owned.glb'),str(p/'work/step1.blend')]
runpy.run_path(str(p/'scripts/meshy_joints.py'),run_name='__main__')
sys.argv=['arm_rings.py','--',str(p/'work/step1.blend')]
runpy.run_path(str(p/'scripts/arm_rings.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/dump_source.py'),run_name='__main__')
