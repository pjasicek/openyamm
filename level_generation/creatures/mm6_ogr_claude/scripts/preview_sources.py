"""G1: reuse the playbook mannequin previews and ROM extraction before Ogre modelling."""
from pathlib import Path
import runpy
import sys
import bpy
p = Path(__file__).resolve().parents[1]
repo = p.parents[2]
library = repo / 'anim_library/humanoid_set'
scripts = p / 'scripts'
def run(name, args):
    sys.argv = [str(scripts / name), '--'] + [str(a) for a in args]
    runpy.run_path(str(scripts / name), run_name='__main__')
run('grip_from_source.py', [library / '1Hand.glb', 'SwordAttackR6:0'])
for view in ('front', 'left', 'three_quarter'):
    run('rpg_preview.py', [library / '1Hand.glb', p / 'review/motion' / ('swords_' + view), view, 9,
                           'SwordAttackR1', 'SwordAttackR5', 'SwordAttackR6'])
for view in ('front', 'left', 'three_quarter'):
    run('rpg_preview.py', [library / 'Armed.glb', p / 'review/motion' / ('roles_' + view), view, 7,
                           'ArmedIdle', 'ArmedWalk', 'ArmedRunForward', 'ArmedGetHitF1', 'ArmedDeath1'])
run('rom_extract.py', [f'{role}={library / file}:{clip}' for role, file, clip in [
    ('Standing', 'Armed.glb', 'ArmedIdle'), ('Walking', 'Armed.glb', 'ArmedWalk'),
    ('Running', 'Armed.glb', 'ArmedRunForward'), ('Hit', 'Armed.glb', 'ArmedGetHitF1'),
    ('Death', 'Armed.glb', 'ArmedDeath1'), ('Attack', '1Hand.glb', 'SwordAttackR6')]])
assert (p / 'work/rom.json').is_file()
