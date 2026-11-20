"""Run the shared humanoid numeric gates on every bound role, with project-specific equipment checks."""
import os
from pathlib import Path
import runpy
import sys

P = Path(__file__).resolve().parents[1]
S = P / 'scripts'
os.environ['STEP'] = '0.5'
shell_only = '--shell-only' in sys.argv

def step(name, *args):
    print('AUDIT', name, flush=True)
    sys.argv = [str(S / name), '--', *map(str, args)]
    runpy.run_path(str(S / name), run_name='__main__')

for mode, clips in [
    ('lancer', ['Carbine_Standing', 'Carbine_Walking', 'Lancer_Running', 'Carbine_Attack',
                'Carbine_Hit', 'Carbine_Fidget', 'Carbine_Death', 'Carbine_Dead']),
    ('forge', [f'Forge_{r}' for r in ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Fidget', 'Cast', 'Death', 'Dead')])]:
    source = P / f'work/{mode}_complete.blend'
    if not shell_only:
        step('gates.py', source, mode, *clips)
        step('sole_probe.py', source, *clips)
        step('jerk_probe.py', source, *clips)
        step('stride.py', source, *[c for c in clips if c.endswith(('Walking', 'Running'))])
    step('shell_stretch.py', source, S / ('armour_forge.json' if mode == 'forge' else 'armour_lancer.json'), mode, *clips)
    step('shell_leak.py', source, S / ('armour_forge.json' if mode == 'forge' else 'armour_lancer.json'), mode, *clips)
    step('equipment_gate.py', source, mode, *clips)
    step('armour_gate.py', source, mode, S / ('armour_forge.json' if mode == 'forge' else 'armour_lancer.json'), *clips)
