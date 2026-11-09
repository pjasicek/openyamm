from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1];R=P.parents[2]
for view in ['front','left','three_quarter']:
    for name,clips in [('1Hand',['MaceAttackR1','MaceAttackR2','MaceAttackR3']),('2Hand Axe',['2HandAxeIdle','2HandAxeWalk','2HandAxeGetHitF1'])]:
        sys.argv=['rpg_preview.py','--',str(R/'anim_library/humanoid_set'/f'{name}.glb'),str(P/'review/g1'/name/view),view,'6',*clips]
        runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
