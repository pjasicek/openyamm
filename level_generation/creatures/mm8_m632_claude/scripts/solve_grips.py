import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for side,radius in [('R',.0125),('L',.014)]:
    os.environ['GRIP_SIDE']=side
    sys.argv=['grip_from_source.py','--','anim_library/humanoid_set/2Hand Crossbow.glb','2HandCrossbowAttack2:8']
    runpy.run_path(str(P/'scripts/grip_from_source.py'),run_name='__main__')
    os.environ['R_HANDLE']=str(radius);os.environ['GRIP_RENDER']=str(P/f'review/grip_{side}')
    sys.argv=['grip_solve.py','--',str(P/'work/rig_pilot.blend'),'Attack','8']
    runpy.run_path(str(P/'scripts/grip_solve.py'),run_name='__main__')
