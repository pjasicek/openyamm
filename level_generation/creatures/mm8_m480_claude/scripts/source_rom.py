from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];R=p.parents[2];lib=R/'anim_library/humanoid_set'
s=p/'scripts/rom_extract.py'
roles=[('Standing','Relax.glb','RelaxIdle'),('Walking','Armed.glb','ArmedWalk'),('Attack','1Hand.glb','SwordAttackR6'),('Hit','Armed.glb','ArmedGetHitF1'),('Death','Unarmed.glb','UnarmedDeath1'),('Fidget','Relax.glb','RelaxDrink1')]
sys.argv=[str(s),'--']+[f'{role}={lib/file}:{clip}' for role,file,clip in roles]+[f'Running={R}/anim_library/mixamo/Running (5).fbx:*']
runpy.run_path(str(s),run_name='__main__')
