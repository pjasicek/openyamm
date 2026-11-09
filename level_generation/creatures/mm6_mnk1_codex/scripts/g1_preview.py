import sys,runpy,json,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]; root=p.parents[2]
roles=json.loads((p/'source/clip_selection.json').read_text())
for setname in ['Relax','Unarmed']:
 clips=list(dict.fromkeys(c for s,c in roles.values() if s==setname))
 for view in ['front','left','three_quarter']:
  sys.argv=['rpg_preview.py','--',str(root/'anim_library/humanoid_set'/f'{setname}.glb'),str(p/'review'/f'g1_{setname}_{view}'),view,'4',*clips]
  runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['rom_extract.py','--']+[f'{r}={root}/anim_library/humanoid_set/{s}.glb:{c}' for r,(s,c) in roles.items()]
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
sys.argv=['source_rest.py','--',str(root/'anim_library/humanoid_set/Relax.glb')]
runpy.run_path(str(p/'scripts/source_rest.py'),run_name='__main__')
