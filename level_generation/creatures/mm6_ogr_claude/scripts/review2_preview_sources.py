"""Preview library-only replacements on the source mannequin before retargeting."""
from pathlib import Path
import runpy,sys,bpy
p=Path(__file__).resolve().parents[1];repo=p.parents[2];scripts=p/'scripts'
for file,clips in [('Armed',['ArmedIdle','ArmedIdleAlert1','ArmedDeath1','ArmedRunForward']),('Relax',['RelaxIdle','RelaxRunForward','RelaxLaydownLayDown','RelaxDrink1']),('Unarmed',['UnarmedRunForward','UnarmedRunForward2','UnarmedDeath1'])]:
 for view in ['left','three_quarter']:
  out=p/'revision_02/motion'/f'{file}_{view}'
  sys.argv=[str(scripts/'rpg_preview.py'),'--',str(repo/'anim_library/humanoid_set'/f'{file}.glb'),str(out),view,'7',*clips]
  runpy.run_path(str(scripts/'rpg_preview.py'),run_name='__main__')
print('REVIEW2_SOURCE_PREVIEWS complete')
