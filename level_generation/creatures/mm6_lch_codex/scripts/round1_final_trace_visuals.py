import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
refs=['Standing=anim_library/humanoid_set/Relax.glb:RelaxIdle', 'Walking=anim_library/humanoid_set/Relax.glb:RelaxWalkForward', 'Fidget=anim_library/humanoid_set/Relax.glb:RelaxDrink1', 'Attack=anim_library/humanoid_set/Unarmed.glb:UnarmedCastDualAttack2', 'Cast=anim_library/humanoid_set/Unarmed.glb:UnarmedCastDualAttack1', 'Hit=anim_library/humanoid_set/Unarmed.glb:UnarmedGetHitF1', 'Death=anim_library/humanoid_set/Unarmed.glb:UnarmedDeath1']
sys.argv=['trace_export.py','--',str(P/'export/mm6_lch.glb'),*refs]
runpy.run_path(str(P/'scripts/trace_export.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_render_packaged.py'),run_name='__main__')
