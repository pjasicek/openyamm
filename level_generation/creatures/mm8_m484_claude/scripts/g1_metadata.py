from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1];R=P.parents[2];L=R/'anim_library/humanoid_set'
def run(name,args):
    sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
run('source_rest.py',[L/'2Hand Axe.glb'])
run('rom_extract.py',[f'{role}={L/name}:{clip}' for role,name,clip in [('Standing','2Hand Axe.glb','2HandAxeIdle'),('Walking','2Hand Axe.glb','2HandAxeWalk'),('Attack','1Hand.glb','MaceAttackR2'),('Hit','2Hand Axe.glb','2HandAxeGetHitF1')]])
