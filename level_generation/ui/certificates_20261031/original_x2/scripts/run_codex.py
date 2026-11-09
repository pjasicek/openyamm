"""Runs the Codex restorations of the MM6 and MM7 certificate backgrounds (BRIEF.md); a name whose two attempts exist
is skipped. Logs go to raw/<name>_codex_run.log. Usage: python3 -I run_codex.py 6winbg 7winbg"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))


def restore(name):
    outputs = [os.path.join(HERE, 'raw', f'{name}_{suffix}.png') for suffix in 'ab']
    if all(os.path.exists(path) for path in outputs):
        return name, 'skipped'
    inputs = [f'{name}_native.png', f'{name}_canvas.png']
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for image in inputs:
        arguments += ['-i', os.path.join(HERE, image)]
    folder = os.path.relpath(HERE, REPO)
    prompt = (f'Follow the brief {folder}/BRIEF.md exactly, with <name> = {name}. The attached images are its inputs, '
              'in this order: ' + ', '.join(inputs) + '. Produce the images with your built-in image generation tool '
              'and save them as specified.')
    with open(os.path.join(HERE, 'raw', f'{name}_codex_run.log'), 'w') as log:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    done = sum(os.path.exists(path) for path in outputs)
    return name, f'exit {result.returncode}, {done}/2 images'


with ThreadPoolExecutor(len(sys.argv) - 1) as pool:
    for name, status in pool.map(restore, sys.argv[1:]):
        print('DONE', name, status, flush=True)
