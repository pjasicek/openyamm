"""Run the additional attack audition through the shared motion preview builder."""
from pathlib import Path
import runpy, sys
script = Path(__file__).with_name('motion_preview.py')
sys.argv = [str(script), '--attack-options']
runpy.run_path(str(script), run_name='__main__')

runpy.run_path(str(script.with_name('motion_preview_checks.py')), run_name='__main__',
               init_globals={'ATTACK_OPTIONS': True})
project = script.parents[1]
for view in ('front','three_quarter'):
    sys.argv = [str(script.with_name('clip_sheet.py')), '--', str(project/'work/rig_attack_options.blend'),
                str(project/'review/attack_options'/view), view, '9',
                'AttackRPG5','AttackRPG6','AttackInward','AttackOutward']
    runpy.run_path(sys.argv[0], run_name='__main__')
