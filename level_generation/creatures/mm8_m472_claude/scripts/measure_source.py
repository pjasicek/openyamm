from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
s=p/'scripts/rom_extract.py'
sys.argv=[str(s),'--','Walking=anim_library/humanoid_set/Armed.glb:ArmedWalk','Running=anim_library/humanoid_set/Unarmed.glb:UnarmedRunForward','Attack=anim_library/humanoid_set/Unarmed.glb:UnarmedCastDualAttack2','Hit=anim_library/humanoid_set/Unarmed.glb:UnarmedGetHitF1','Death=anim_library/humanoid_set/Unarmed.glb:UnarmedDeath1']
runpy.run_path(str(s),run_name='__main__')
