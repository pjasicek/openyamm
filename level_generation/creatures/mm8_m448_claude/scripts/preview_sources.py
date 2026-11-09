"""Preview owned source clips using the playbook mannequin and sword-grip reference."""
from pathlib import Path
import runpy
import sys

project = Path(__file__).resolve().parents[1]
repo = project.parents[2]
preview = repo / 'level_generation/creatures/mm6_natm_claude/scripts/rpg_preview.py'
assert preview.is_file()
for view in ('front', 'left', 'three_quarter'):
    sys.argv = [str(preview), '--', str(repo / 'anim_library/humanoid_set/1Hand.glb'),
                str(project / 'review/source_motion' / view), view, '7',
                'SwordAttackR1', 'SwordAttackR4', 'SwordAttackR6']
    runpy.run_path(str(preview), run_name='__main__')
for view in ('front', 'left'):
    sys.argv = [str(preview), '--', str(repo / 'anim_library/humanoid_set/Armed.glb'),
                str(project / 'review/source_motion' / ('body_' + view)), view, '5',
                'ArmedIdle', 'ArmedWalk', 'ArmedRunForward', 'ArmedGetHitF1', 'ArmedDeath1', 'ArmedIdleAlert1']
    runpy.run_path(str(preview), run_name='__main__')
