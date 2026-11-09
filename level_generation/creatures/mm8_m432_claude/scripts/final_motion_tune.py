import runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/axis_correction.py'),run_name='__main__')
shutil.copyfile(P/'work/rig_final_motion.blend',P/'work/rig_axis_gate_input.blend')
runpy.run_path(str(P/'scripts/fine_arm_pass.py'),run_name='__main__')
