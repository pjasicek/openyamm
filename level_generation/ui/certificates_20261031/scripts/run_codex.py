"""Runs the Codex paint sessions of the completion certificates (briefs/<name>.md), all at once; a certificate whose
two candidates exist is skipped. Each session's log is raw/<name>_codex_run.log; the prompt goes on stdin, since
`codex exec -i` takes every following argument as an image.
Usage: python3 -I run_codex.py <name> [...]   (enroth, antagarich, jadame, grand)"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
GLOBES = ['ref_globe_enroth.png', 'ref_globe_antagarich.png', 'ref_globe_jadame.png']
INPUTS = {
    'enroth': ['guide_continent.png', 'ref_obsidian_frame.png', 'ref_openyamm_seal.png', 'ref_globe_enroth.png'],
    'antagarich': ['guide_continent.png', 'ref_obsidian_frame.png', 'ref_openyamm_seal.png',
                   'ref_globe_antagarich.png'],
    'jadame': ['guide_continent.png', 'ref_obsidian_frame.png', 'ref_openyamm_seal.png', 'ref_globe_jadame.png'],
    'grand': ['guide_grand.png', 'ref_obsidian_frame.png', 'ref_openyamm_seal.png'] + GLOBES,
}


def paint(name):
    outputs = [os.path.join(HERE, 'raw', f'{name}_{suffix}.png') for suffix in 'ab']
    if all(os.path.exists(path) for path in outputs):
        return name, 'skipped'
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for image in INPUTS[name]:
        arguments += ['-i', os.path.join(HERE, image)]
    folder = os.path.relpath(HERE, REPO)
    prompt = (f'Follow the briefs {folder}/briefs/COMMON.md and {folder}/briefs/{name}.md exactly. The attached images '
              'are their inputs, in this order: ' + ', '.join(INPUTS[name]) + '. Produce the images with your '
              'built-in image generation tool and save them as specified.')
    with open(os.path.join(HERE, 'raw', f'{name}_codex_run.log'), 'w') as log:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    done = sum(os.path.exists(path) for path in outputs)
    return name, f'exit {result.returncode}, {done}/2 images'


def main():
    with ThreadPoolExecutor(len(sys.argv) - 1) as pool:
        for name, status in pool.map(paint, sys.argv[1:]):
            print('DONE', name, status, flush=True)


main()
