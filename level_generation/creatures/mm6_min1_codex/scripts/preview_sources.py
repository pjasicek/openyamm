"""Preview owned axe sources before generating the body."""
from pathlib import Path
import sys,runpy,os,json
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(ROOT)
L=ROOT/'anim_library/humanoid_set/2Hand Axe.glb'
def run(name,args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
run('source_rest.py',[L]);run('grip_from_source.py',[L,'2HandAxeIdle:8'])
clips=['2HandAxeIdle','2HandAxeWalk','2HandAxeRunForward','2HandAxeAttack1','2HandAxeAttack6','2HandAxeGetHitF1','2HandAxeDeath1','2HandAxeIdleAlert1']
for view in ['front','left','three_quarter']:
 run('rpg_preview.py',[L,P/'review/g1'/view,view,4,*clips])
run('rom_extract.py',[f'{role}={L}:{clip}' for role,clip in zip(['Standing','Walking','Running','Attack1','Attack6','Hit','Death','Fidget'],clips)])
assert (P/'work/rom.json').exists()
