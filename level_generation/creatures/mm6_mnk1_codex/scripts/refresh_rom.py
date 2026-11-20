import runpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
r=json.loads((p/'source/clip_selection.json').read_text())
sys.argv=['rom_extract.py','--']+[f'{role}={root}/anim_library/humanoid_set/{s}.glb:{c}' for role,(s,c) in r.items()]
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
sys.argv=['proportions.py','--','source',str(root/'anim_library/humanoid_set/Relax.glb')]
runpy.run_path(str(p/'scripts/proportions.py'),run_name='__main__')
