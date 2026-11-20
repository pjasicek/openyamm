import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['retarget_mixamo.py','--',str(P/'work/review1/reduction_master.blend'),str(P/'work/review1/run_retarget.blend'),'anim_library/mixamo/Jogging.fbx:ReviewRun']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
