"""Preview civilian idle/gesture and required unarmed reactions on source mesh."""
from pathlib import Path
import sys, runpy
p=Path(__file__).resolve().parents[1]
lib=p.parents[2]/'anim_library/humanoid_set'
for name, clips in [('Relax',['RelaxIdle','RelaxWalkForward','RelaxTalk1','RelaxYes']),
                    ('Unarmed',['UnarmedAttackR1','UnarmedAttackR2','UnarmedGetHitF1','UnarmedDeath1'])]:
 for view in ['front','left','three_quarter']:
  out=p/'review/source_motion'/name/view
  sys.argv=['set_preview.py','--',str(lib/(name+'.glb')),str(out),view,'9',*clips]
  runpy.run_path(str(p/'scripts/set_preview.py'),run_name='__main__')
