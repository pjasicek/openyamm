from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1]
for view in ['front','left']:
 sys.argv=['rpg_preview.py','--',str(P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb'),str(P/'review/g1_twohand'/view),view,'6',*[f'2HandAxeAttack{i}' for i in range(1,7)]];runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
