from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
sys.argv=['source_rest.py','--',str(repo/'anim_library/humanoid_set/1Hand.glb')]
runpy.run_path(str(p/'scripts/source_rest.py'),run_name='__main__')
sys.argv=['fit_joints.py','--',str(p/'work/step1.blend'),'Body']
runpy.run_path(str(p/'scripts/fit_joints.py'),run_name='__main__')
