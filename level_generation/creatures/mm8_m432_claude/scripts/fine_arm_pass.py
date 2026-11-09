import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['ARM_INPUT']='work/rig_axis_gate_input.blend';os.environ['ARM_OUTPUT']='work/rig_fine_arms.blend';os.environ['ARM_CLIPS']='Attack';os.environ['ARM_SIDES']='RLR';os.environ['ARM_PHI']='60';os.environ['ARM_PHI_STEP']='5';os.environ['ARM_FINE']='1'
runpy.run_path(str(P/'scripts/smooth_arm_fit.py'),run_name='__main__')
os.environ['BAKE_ONLY']='1';os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
sys.argv=['twist_bones.py','--',str(P/'work/rig_fine_arms.blend'),str(P/'work/rig_final_motion.blend')]
runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__');runpy.run_path(str(P/'scripts/assemble.py'),run_name='__main__');runpy.run_path(str(P/'scripts/fit_fasteners.py'),run_name='__main__');os.environ['REDUCE_INPUT']='work/rig_hardware.blend';runpy.run_path(str(P/'scripts/prepare_texturing.py'),run_name='__main__')
