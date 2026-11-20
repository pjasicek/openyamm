"""Preview candidate Thug mace attacks on the animation source mannequin."""
from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
repo=p.parents[2]
os.chdir(repo)
scripts=p/'scripts'
def run(name,args):
    sys.argv=[str(scripts/name),'--',*map(str,args)]
    runpy.run_path(str(scripts/name),run_name='__main__')
run('grip_from_source.py',[repo/'anim_library/humanoid_set/1Hand.glb','MaceAttackR1:0'])
for view in ['front','three_quarter','left']:
    run('rpg_preview.py',[repo/'anim_library/humanoid_set/1Hand.glb',p/'review'/('g1_mace_'+view),view,'7','MaceAttackR1','MaceAttackR2','MaceAttackR3'])
