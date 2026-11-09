from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
for file,clips in [('Armed',['ArmedKnockdown1']),('Unarmed',['UnarmedDeath1','UnarmedKnockdown1'])]:
 for view in ('front','left'):
  sys.argv=[str(p/'scripts/rpg_preview.py'),'--',str(p.parents[2]/f'anim_library/humanoid_set/{file}.glb'),str(p/f'review/g1_death_{file}_{view}'),view,'9',*clips]
  runpy.run_path(sys.argv[0],run_name='__main__')
