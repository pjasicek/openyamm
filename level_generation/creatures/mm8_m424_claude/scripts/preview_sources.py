"""G1 source-mannequin previews, using the current humanoid playbook helpers."""
from pathlib import Path
import runpy
import sys

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
LIB = ROOT / 'anim_library/humanoid_set'
SCRIPTS = PROJECT / 'scripts'
assert (LIB / '1Hand.glb').is_file()
sys.argv = ['grip_from_source.py', '--', str(LIB / '1Hand.glb'), 'DaggerAttackR2:0', 'DaggerAttackR3:12']
runpy.run_path(str(SCRIPTS / 'grip_from_source.py'), run_name='__main__')
for source, clips in [('1Hand', ['DaggerAttackR2', 'DaggerAttackR3']),
                      ('Relax', ['RelaxIdle', 'RelaxWalkForward']),
                      ('Unarmed', ['UnarmedGetHitF1', 'UnarmedDeath1'])]:
    for view in ['front', 'left', 'three_quarter']:
        output = PROJECT / 'review/source_motion' / source / view
        sys.argv = ['set_preview.py', '--', str(LIB / (source + '.glb')), str(output), view, '5', *clips]
        runpy.run_path(str(SCRIPTS / 'set_preview.py'), run_name='__main__')
print('SOURCE_PREVIEW complete')
