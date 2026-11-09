from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1];L=P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb'
for view in ['front','left','three_quarter']:
 sys.argv=['rpg_preview.py','--',str(L),str(P/'review/g1_attacks'/view),view,'6','2HandAxeAttack2','2HandAxeAttack3','2HandAxeAttack4','2HandAxeAttack5'];runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
