import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(P/'scripts'))
clips=['2HandBowIdle','2HandBowWalk','2HandBowAimingPull','2HandBowAimingFire','2HandBowAttack1','2HandBowGetHitF1','2HandBowDeath1','2HandBowBoost1']
for view in ['front','left','three_quarter']:
 sys.argv=['rpg_preview.py','--','anim_library/humanoid_set/2Hand Bow.glb',str(P/'review'/f'g1_{view}'),view,'4',*clips]
 runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['source_rest.py','--','anim_library/humanoid_set/2Hand Bow.glb']
runpy.run_path(str(P/'scripts/source_rest.py'),run_name='__main__')
