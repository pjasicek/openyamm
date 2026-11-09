import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for v in ['front','left','three_quarter']:
 sys.argv=['rpg_preview.py','--',str(P.parents[2]/'anim_library/humanoid_set/Unarmed.glb'),str(P/f'review/g1/death_alternative/{v}'),v,'6','UnarmedDeath1'];runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
