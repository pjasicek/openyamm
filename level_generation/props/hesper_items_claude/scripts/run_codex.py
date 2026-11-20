"""Runs the Codex paint sessions of Hesper item designs (codex_tex/<icon>/CODEX_BRIEF.md), at most four at once
(the integrator's limit, P4.md 2026-10-24). A design whose five paintings exist is skipped. Each session's log is
codex_tex/<icon>/codex_run.log; the prompt goes on stdin, since `codex exec -i` takes every following argument as
an image.
A `master:<icon>` target instead runs the HD master brief in meshy/<icon>/references_hd (input icon_master.png,
output 00_three_quarter.png), for designs whose icon shows them in another pose (the cloaks).
Usage: python3 -I run_codex.py <icon | master:icon> [...]"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIEWS = ('front', 'back', 'left', 'right', 'top')
INPUTS = ['design_reference.png'] + [f'guide_{view}.png' for view in VIEWS]
PARALLEL = 4


def paint(target):
    master = target.startswith('master:')
    icon = target.split(':')[-1]
    folder = os.path.join(HERE, 'meshy', icon, 'references_hd') if master else os.path.join(HERE, 'codex_tex', icon)
    outputs = ['00_three_quarter.png'] if master else [f'paint_{view}.png' for view in VIEWS]
    inputs = ['icon_master.png'] if master else INPUTS
    if all(os.path.exists(os.path.join(folder, name)) for name in outputs):
        return target, 'skipped'
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for name in inputs:
        arguments += ['-i', os.path.join(folder, name)]
    brief = os.path.relpath(os.path.join(folder, 'CODEX_BRIEF.md'), REPO)
    prompt = (f'Follow the brief in {brief} exactly. The attached images are its inputs (named as in the brief, in '
              'this order: ' + ', '.join(inputs) + '). Produce the images with your built-in image '
              'generation tool and save them as specified.')
    with open(os.path.join(folder, 'codex_run.log'), 'w') as log:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    done = sum(os.path.exists(os.path.join(folder, name)) for name in outputs)
    return target, f'exit {result.returncode}, {done}/{len(outputs)} images'


def main():
    with ThreadPoolExecutor(PARALLEL) as pool:
        for icon, status in pool.map(paint, sys.argv[1:]):
            print('DONE', icon, status, flush=True)


main()
