import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for script,args in [('source_rest.py',['anim_library/humanoid_set/2Hand Crossbow.glb']),('proportions.py',['source','anim_library/humanoid_set/2Hand Crossbow.glb'])]:
    sys.argv=[script,'--',*args];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
