import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
R=P.parents[2]
sys.argv=['retarget_mixamo.py','--',str(P/'work/rig_fingers.blend'),str(P/'work/round3_sources.blend'),str(R/'anim_library/mixamo/Standard Run.fbx')+':RunNormal']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
