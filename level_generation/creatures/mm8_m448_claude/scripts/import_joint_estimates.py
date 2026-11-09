from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
sys.argv=['meshy_joints','--',str(p/'meshy/rig_v1/result_rigged_character_glb_url.glb'),str(p/'work/step1.blend')]
runpy.run_path(str(p/'scripts/meshy_joints.py'),run_name='__main__')
