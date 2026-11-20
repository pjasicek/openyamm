"""Rebuild both shells from the final plate spec, then add caste equipment and export review masters."""
from pathlib import Path
import runpy
import subprocess
import sys

P = Path(__file__).resolve().parents[1]
S, W = P / 'scripts', P / 'work'
sys.path.insert(0, str(S))

def step(name, *args):
    print('STEP', name, flush=True)
    sys.argv = [str(S / name), '--', *map(str, args)]
    runpy.run_path(str(S / name), run_name='__main__')

for mode, source in [('lancer', 'lancer_polished.blend'), ('forge', 'forge_weighted.blend')]:
    shell = W / f'{mode}_shell.blend'
    step('bake_new_twists.py', W / source, shell)
    step('helper_bones.py', shell, shell)
    step('make_armour.py', shell, S / 'armour_lancer.json', shell)
    if mode == 'lancer':
        step('make_lance.py', shell, shell)
    step('skin_shell.py', shell, S / 'armour_lancer.json', shell)
    step('helper_bones.py', shell, shell)
    step('add_hull_parts.py', shell, mode, W / f'{mode}_complete.blend')
    subprocess.run(['python3', str(S / 'armour_texture.py')], check=True)
    step('export_lancer.py', W / f'{mode}_complete.blend', mode)
