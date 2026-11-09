"""Bakes every design whose five paintings exist and whose export is missing or older than them (hes_texture.py bake),
then renders its textured review and a review sheet of the designs baked in this run.
Usage: python3 -I bake_ready.py"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ('front', 'back', 'left', 'right', 'top')


def main():
    ready = []
    for icon in sorted(os.listdir(os.path.join(HERE, 'codex_tex'))):
        paints = [os.path.join(HERE, 'codex_tex', icon, f'paint_{view}.png') for view in VIEWS]
        if not all(os.path.exists(path) for path in paints):
            continue
        export = os.path.join(HERE, 'work', f'{icon}_export.glb')
        if not os.path.exists(export) or os.path.getmtime(export) < max(os.path.getmtime(path) for path in paints):
            ready.append(icon)
    if not ready:
        print('nothing to bake')
        return
    scripts = os.path.join(HERE, 'scripts')
    for script, mode in (('hes_texture.py', 'bake'), ('review.py', 'textured')):
        result = subprocess.run(['blender', '--background', '--python', os.path.join(scripts, script), '--', mode]
                                + ready, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith(('BAKED', 'Traceback', 'Error')) or 'Error' in line:
                print(line[:160])
    subprocess.run([sys.executable, '-I', os.path.join(scripts, 'sheet.py'), 'textured'] + ready)


main()
