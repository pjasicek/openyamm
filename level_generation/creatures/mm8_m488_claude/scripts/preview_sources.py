"""Preview actual unarmed clips before selecting the m488 source-frame rig."""
from pathlib import Path
import runpy
import sys
p = Path(__file__).resolve().parents[1]
repo = p.parents[2]
library = repo / 'anim_library/humanoid_set'
def run(name, args):
    script = p / 'scripts' / name
    sys.argv = [str(script), '--', *map(str, args)]
    runpy.run_path(str(script), run_name='__main__')
for view in ('front', 'left', 'three_quarter'):
    run('rpg_preview.py', [library / 'Unarmed.glb', p / 'review/motion' / ('candidates_' + view), view, 6,
                          'UnarmedAttackL2', 'UnarmedAttackR3', 'UnarmedGetHitF1', 'UnarmedDeath1'])
    run('rpg_preview.py', [library / 'Relax.glb', p / 'review/motion' / ('civilian_' + view), view, 6,
                          'RelaxIdle', 'RelaxWalkForward', 'RelaxTalk1'])
run('rom_extract.py', [f'{role}={library / file}:{clip}' for role, file, clip in [
    ('StandingCandidate', 'Relax.glb', 'RelaxIdle'), ('WalkingCandidate', 'Relax.glb', 'RelaxWalkForward'),
    ('FidgetCandidate', 'Relax.glb', 'RelaxTalk1'), ('AttackCandidate', 'Unarmed.glb', 'UnarmedAttackR3'),
    ('HitCandidate', 'Unarmed.glb', 'UnarmedGetHitF1'), ('DeathCandidate', 'Unarmed.glb', 'UnarmedDeath1')]])
assert (p / 'work/rom.json').is_file()
