import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['ARM_SIDES']='L';os.environ['ARM_PHI']='90'
os.environ['ARM_INPUT']='work/rig_final_motion.blend';os.environ['ARM_OUTPUT']='work/rig_final_arms.blend';os.environ['ARM_CLIPS']='Attack'
runpy.run_path(str(P/'scripts/arm_planes.py'),run_name='__main__')
os.environ['BAKE_ONLY']='1';os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
sys.argv=['twist_bones.py','--',str(P/'work/rig_final_arms.blend'),str(P/'work/rig_final_motion.blend')]
runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/assemble.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/contact_probe.py'),run_name='__main__')
