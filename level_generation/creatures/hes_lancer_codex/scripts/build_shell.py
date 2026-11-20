"""Reproduce the fitted Lancer shell from the shared-import Standard Run checkpoint."""
import os
from pathlib import Path
import runpy
import sys

P = Path(__file__).resolve().parents[1]
S = P / 'scripts'
W = P / 'work'
CLIPS = ['Carbine_Standing', 'Carbine_Walking', 'Lancer_Running', 'Carbine_Attack',
         'Carbine_Hit', 'Carbine_Fidget', 'Carbine_Death', 'Carbine_Dead']
os.environ.update(MAX='55', SOFT='0.25', LEFT='1', MARGIN='0.015', PASSES='2', CYCLIC='1')

def step(script, *args):
    print('STEP', script, flush=True)
    sys.argv = [str(S / script), '--', *map(str, args)]
    runpy.run_path(str(S / script), run_name='__main__')

step('leg_limit.py', W / 'carry_v3.blend', W / 'limited_v3.blend', 'Lancer_Running')
step('bulk_body.py', W / 'limited_v3.blend', W / 'bulk_v3.blend')
step('make_armour.py', W / 'bulk_v3.blend', S / 'armour_lancer.json', W / 'armour_v3.blend')
step('make_lance.py', W / 'armour_v3.blend', W / 'weapons_v4.blend')
step('skin_shell.py', W / 'weapons_v4.blend', S / 'armour_lancer.json', W / 'shell_v3.blend')
step('armour_clear.py', W / 'shell_v3.blend', W / 'clear_v3.blend', *CLIPS[:6])
step('foot_floor.py', W / 'clear_v3.blend', W / 'floor_v3.blend', 'Lancer_Running')
step('helper_bones.py', W / 'floor_v3.blend', W / 'final_lancer.blend')
step('armour_gate.py', W / 'final_lancer.blend', 'v4', S / 'armour_lancer.json', *CLIPS)
