import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
for view in ['front','left','three_quarter']:
 sys.argv=['rpg_preview.py','--',str(root/'anim_library/humanoid_set/Unarmed.glb'),str(p/'review'/f'g1_candidates_{view}'),view,'5','UnarmedCastDualAttack1','UnarmedCastDualAttack3','UnarmedCastDualBuff1','UnarmedCastDualSummon1']
 runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
