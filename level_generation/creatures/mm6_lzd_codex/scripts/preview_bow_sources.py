import bpy,sys,runpy,json,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
L=ROOT/'anim_library/humanoid_set'
for view in ['front','left','three_quarter']:
 sys.argv=['rpg_preview.py','--',str(L/'2Hand Bow.glb'),str(P/'review/g1'/view),view,'4','2HandBowIdle','2HandBowWalk','2HandBowAimingPull','2HandBowAimingFire','2HandBowAttack1','2HandBowGetHitF1','2HandBowDeath1']
 runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
