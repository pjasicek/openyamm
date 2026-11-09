import sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]; R=P.parents[2]
sys.path.insert(0,str(P/'scripts'))
sets={'Relax':['RelaxIdle','RelaxWalkForward','RelaxRunForward','RelaxLaydownLayDown','RelaxDrink1'],'1Hand':['MaceAttackR1','MaceAttackR2','MaceAttackR3'],'Unarmed':['UnarmedGetHitF1']}
for name,clips in sets.items():
 for view in ['front','left','three_quarter']:
  out=P/'review/g1'/name/view
  sys.argv=['rpg_preview.py','--',str(R/'anim_library/humanoid_set'/f'{name}.glb'),str(out),view,'4',*clips]
  runpy.run_path(str(P/'scripts/rpg_preview.py'),run_name='__main__')
print('G1 previews rendered',flush=True)
