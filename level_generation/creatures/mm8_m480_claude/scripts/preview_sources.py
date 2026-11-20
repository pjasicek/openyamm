from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];lib=p.parents[2]/'anim_library/humanoid_set';scripts=p/'scripts'
for file,clips in [('1Hand',['SwordAttackR1','SwordAttackR5','SwordAttackR6']),('Armed',['ArmedWalk','ArmedGetHitF1']),('Relax',['RelaxIdle','RelaxDrink1']),('Unarmed',['UnarmedDeath1'])]:
 for view in ['left','three_quarter']:
  sys.argv=[str(scripts/'rpg_preview.py'),'--',str(lib/f'{file}.glb'),str(p/'review/motion'/f'{file}_{view}'),view,'7',*clips]
  runpy.run_path(str(scripts/'rpg_preview.py'),run_name='__main__')
