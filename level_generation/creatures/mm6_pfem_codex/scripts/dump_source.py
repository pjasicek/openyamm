import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parent
sys.argv=['source_rest.py','--','anim_library/humanoid_set/Relax.glb']
runpy.run_path(str(p/'source_rest.py'),run_name='__main__')
sys.argv=['proportions.py','--','source','anim_library/humanoid_set/Relax.glb']
runpy.run_path(str(p/'proportions.py'),run_name='__main__')
