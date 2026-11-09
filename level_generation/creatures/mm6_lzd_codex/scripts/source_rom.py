import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P)
L=ROOT/'anim_library/humanoid_set/2Hand Bow.glb'
sys.argv=['source_rest.py','--',str(L)];runpy.run_path(str(P/'scripts/source_rest.py'),run_name='__main__')
sys.argv=['rom_extract.py','--',*[role+'='+str(L)+':'+clip for role,clip in [('Standing','2HandBowIdle'),('Walking','2HandBowWalk'),('Attack','2HandBowAttack1'),('Hit','2HandBowGetHitF1'),('Death','2HandBowDeath1')]]]
runpy.run_path(str(P/'scripts/rom_extract.py'),run_name='__main__')
