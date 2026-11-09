import os, sys, runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.chdir(p)
sys.path.insert(0,str(p/'scripts'))
lib=Path('/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set')
def run(name,args):
 sys.argv=[name,'--']+[str(x) for x in args]
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('grip_from_source.py',[lib/'Armed.glb','ArmedIdle:0','ArmedWalk:6'])
for view in ('front','three_quarter','left'):
 run('rpg_preview.py',[lib/'1Hand.glb',p/'review'/('source_attacks_'+view),view,6,'SwordAttackR1','SwordAttackR4','SwordAttackR5','SwordAttackR6'])
run('rpg_preview.py',[lib/'Armed.glb',p/'review/source_roles','three_quarter',6,'ArmedIdle','ArmedWalk','ArmedGetHitF1','ArmedDeath1','ArmedBoost1'])
