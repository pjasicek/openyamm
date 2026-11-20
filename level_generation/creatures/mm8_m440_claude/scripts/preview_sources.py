"""G1 previews with a club envelope on the source mannequin; project-local outputs only."""
from pathlib import Path
import runpy, sys
p = Path(__file__).resolve().parents[1]
lib = p.parents[2] / 'anim_library/humanoid_set'
s = p / 'scripts'
sys.argv = ['grip_from_source.py', '--', str(lib/'1Hand.glb'), 'MaceAttackR1:0', 'MaceAttackR2:0']
runpy.run_path(str(s/'grip_from_source.py'), run_name='__main__')
for name, clips in [('1Hand',['MaceAttackR1','MaceAttackR2','MaceAttackR3']),
                    ('Armed',['ArmedWalk','ArmedGetHitF1','ArmedDeath1']),
                    ('Relax',['RelaxIdle'])]:
    for view in ['front','left','three_quarter']:
        out = p/'review/source_motion'/name/view
        sys.argv = ['set_preview.py','--',str(lib/(name+'.glb')),str(out),view,'9',*clips]
        runpy.run_path(str(s/'set_preview.py'),run_name='__main__')
print('G1_SET_PREVIEWS_COMPLETE')
