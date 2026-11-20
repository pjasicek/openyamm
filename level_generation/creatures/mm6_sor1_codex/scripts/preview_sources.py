import sys,runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
root=p.parents[2]
sets={'Relax':['RelaxIdle','RelaxWalkForward','RelaxLaydownLayDown'], 'Armed':['ArmedCastLBuff2','ArmedCastLAttack1'], 'Unarmed':['UnarmedGetHitF1']}
for group, clips in sets.items():
 for view in ('front','left','three_quarter'):
  out=p/'review'/'source_clips'/f'{group}_{view}'
  sys.argv=['rpg_preview.py','--',str(root/'anim_library/humanoid_set'/f'{group}.glb'),str(out),view,'4',*clips]
  runpy.run_path(str(p/'scripts/rpg_preview.py'),run_name='__main__')
