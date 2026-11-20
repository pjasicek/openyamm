import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P.parents[2]/'anim_library/humanoid_set/Relax.glb'
sys.argv=['retarget.py','--',str(P/'work/rig_v6.blend'),str(P/'work/rig_v6_run.blend'),str(S)+':RelaxRunForward:Running']
runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
