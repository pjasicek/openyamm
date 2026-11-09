import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(P/'scripts'))
groups={'Relax':['RelaxIdle','RelaxWalkForward','RelaxDrink1'],
        'Unarmed':['UnarmedCastDualAttack1','UnarmedCastDualAttack2','UnarmedCastDualBuff1','UnarmedDeath1','UnarmedGetHitF1']}
for group,clips in groups.items():
 for view in ['front','left','three_quarter']:
  sys.argv=['rpg_preview.py','--',f'anim_library/humanoid_set/{group}.glb',str(P/'review'/f'g1_{group}_{view}'),view,'5',*clips]
  runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['source_rest.py','--','anim_library/humanoid_set/Relax.glb']
runpy.run_path(str(P/'scripts/source_rest.py'),run_name='__main__')
