"""Runs the Codex paint sessions of the MM9 inventory icon trial (briefs/COMMON.md + briefs/<id>.md), at most four
at once. A design whose paint_a.png exists is skipped. Each session's log is items/<id>/codex_run.log; the prompt
goes on stdin, since `codex exec -i` takes every following argument as an image.
Usage: python3 -I run_codex.py <id> [...]   (no ids: every design in designs.json)"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PARALLEL = 4


def paint(item_id):
    folder = os.path.join(HERE, 'items', item_id)
    outputs = [os.path.join(folder, 'paint_a.png')]
    if all(os.path.exists(p) for p in outputs):
        return item_id, 'skipped'
    inputs = ['source_pcx.png', 'style_reference.png']
    if os.path.exists(os.path.join(folder, 'source_upright.png')):
        inputs.append('source_upright.png')
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for name in inputs:
        arguments += ['-i', os.path.join(folder, name)]
    rel = os.path.relpath(HERE, REPO)
    prompt = (f'Follow the briefs {rel}/briefs/COMMON.md and {rel}/briefs/{item_id}.md exactly. The attached images '
              'are their inputs, in this order: ' + ', '.join(inputs) + f' (all from {rel}/items/{item_id}/). '
              'Produce the images with your built-in image generation tool and save them as specified.')
    with open(os.path.join(folder, 'codex_run.log'), 'w') as log:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    done = sum(os.path.exists(p) for p in outputs)
    return item_id, f'exit {result.returncode}, {done}/1 images'


def main():
    ids = sys.argv[1:] or [str(i['design_id']) for i in json.load(open(os.path.join(HERE, 'designs.json')))]
    with ThreadPoolExecutor(PARALLEL) as pool:
        for item_id, status in pool.map(paint, ids):
            print('DONE', item_id, status, flush=True)


main()
