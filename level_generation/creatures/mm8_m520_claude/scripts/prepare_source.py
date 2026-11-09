from pathlib import Path
import runpy, sys
p=Path(__file__).resolve().parents[1]
source=p.parents[2]/'anim_library/humanoid_set/Unarmed.glb'
for name,args in [('source_rest.py',[str(source)]),('proportions.py',['source',str(source)])]:
 s=p/'scripts'/name
 sys.argv=[str(s),'--',*args]
 runpy.run_path(str(s),run_name='__main__')
