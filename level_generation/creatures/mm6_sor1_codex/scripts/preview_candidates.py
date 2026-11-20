import sys,runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
root=p.parents[2]
sets={'Unarmed':['UnarmedDeath1'], 'Relax':['RelaxDrink1']}
for group, clips in sets.items():
 for view in ('front','left','three_quarter'):
  out=p/'review'/'source_candidates'/f'{group}_{view}'
  sys.argv=['rpg_preview.py','--',str(root/'anim_library/humanoid_set'/f'{group}.glb'),str(out),view,'4',*clips]
  runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
