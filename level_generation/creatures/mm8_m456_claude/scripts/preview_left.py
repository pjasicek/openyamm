from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]; repo=p.parents[2]
sys.argv=['grip_from_source.py','--',str(repo/'anim_library/humanoid_set/1Hand.glb'),'SwordAttackL1:5']
runpy.run_path(str(p/'scripts/grip_from_source.py'),run_name='__main__')
for view in ['front','left','three_quarter']:
 sys.argv=['rpg_preview.py','--',str(repo/'anim_library/humanoid_set/1Hand.glb'),str(p/'review/g1_left'/view),view,'9','SwordAttackL1','SwordAttackL2','SwordAttackL3']
 runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
