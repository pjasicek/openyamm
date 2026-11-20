import sys,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
sets={'Relax':['RelaxIdle','RelaxWalkForward','RelaxRunForward','RelaxLaydownLayDown'],'2Hand Staff':['StaffAttack1','StaffAttack6','StaffCastLAttack3']}
for name,clips in sets.items():
 for view in ['front','left','three_quarter']:
  sys.argv=['rpg_preview.py','--',str(root/'anim_library/humanoid_set'/f'{name}.glb'),str(p/'review'/f'g1_{name}_{view}'),view,'3',*clips]
  runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['source_rest.py','--',str(root/'anim_library/humanoid_set/Relax.glb')]
runpy.run_path(str(p/'scripts/source_rest.py'),run_name='__main__')
