import sys, runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
src=Path('anim_library/humanoid_set').resolve()
for view in ('front','left','three_quarter'):
    sys.argv=['rpg_preview.py','--',str(src/'Unarmed.glb'),str(p/'review/g1/hit'/view),view,'5','UnarmedGetHitF1']
    runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
sys.argv=['rom_extract.py','--',f'Standing={src}/Relax.glb:RelaxIdle',f'Walking={src}/Relax.glb:RelaxWalkForward',f'Death={src}/Relax.glb:RelaxLaydownLayDown',f'Hit={src}/Unarmed.glb:UnarmedGetHitF1']
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
