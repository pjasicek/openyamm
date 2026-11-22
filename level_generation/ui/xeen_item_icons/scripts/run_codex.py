"""Runs one Codex paint session per target (briefs/COMMON.md + briefs/<file>.md), at most PARALLEL at once. A target
whose paint_a.png exists is skipped (move it aside to regenerate; raw returns are kept as paint_*.png). Each
session's log is items/<file>/codex_run.log; the prompt goes on stdin, since `codex exec -i` takes every following
argument as an image.
Usage: python3 -I run_codex.py [<key> ...]   (no keys: every target in manifest.yml)"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PARALLEL = 4


def paint(target):
    folder = os.path.join(HERE, 'items', target['file'])
    output = os.path.join(folder, 'paint_a.png')
    if os.path.exists(output):
        return target['key'], 'skipped'
    rel = os.path.relpath(HERE, REPO)
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check',
                 '-i', os.path.join(folder, 'style_reference.png')]
    prompt = (f"Follow the briefs {rel}/briefs/COMMON.md and {rel}/briefs/{target['file']}.md exactly. The attached "
              f"image is their style_reference.png (from {rel}/items/{target['file']}/). Produce the image with your "
              f"built-in image generation tool and save it unchanged as {rel}/items/{target['file']}/paint_a.png.")
    with open(os.path.join(folder, 'codex_run.log'), 'w') as log:
        try:
            result = subprocess.run(arguments, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=900)
            code = result.returncode
        except subprocess.TimeoutExpired:
            log.write('\nrun_codex.py: timed out after 900 s\n')
            code = -1
    return target['key'], f"exit {code}, {'painted' if os.path.exists(output) else 'NO IMAGE'}"


def main():
    manifest = yaml.safe_load(open(os.path.join(HERE, 'manifest.yml')))
    wanted = set(sys.argv[1:])
    targets = [t for t in manifest['targets'] if not wanted or t['key'] in wanted]
    with ThreadPoolExecutor(PARALLEL) as pool:
        for key, status in pool.map(paint, targets):
            print('DONE', key, status, flush=True)


main()
