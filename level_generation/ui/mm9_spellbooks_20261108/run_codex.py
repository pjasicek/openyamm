"""Runs the Codex sessions of the MM9 spellbook art (BRIEF_ICONS.md, BRIEF_TEXTURES.md), at most four at once.
Usage: python3 -I run_codex.py icons <tier> [...] | textures <tier> [...]
A tier whose deliverables exist is skipped. Each session's log is <tier>/codex_<stage>.log; the prompt goes on stdin."""
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REL = os.path.relpath(HERE, REPO)


def session(stage, tier):
    folder = os.path.join(HERE, tier)
    if stage == 'icons':
        outputs = ['paint_a.png']
        inputs = [os.path.join(HERE, 'inputs', 'style_reference.png'),
                  os.path.join(HERE, 'inputs', 'mm9_skill_books_avoid.png')]
        if tier != 'normal':
            reference = os.path.join(folder, 'normal_paint.png')
            shutil.copyfile(os.path.join(HERE, 'normal', 'paint_a.png'), reference)
            inputs.append(reference)
        brief = 'BRIEF_ICONS.md'
    else:
        outputs = ['cover.png', 'spine.png']
        inputs = [os.path.join(folder, 'icon_x8.png')]
        brief = 'BRIEF_TEXTURES.md'
    if all(os.path.exists(os.path.join(folder, name)) for name in outputs):
        return tier, 'skipped'
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for path in inputs:
        arguments += ['-i', path]
    prompt = (f'Follow the brief {REL}/{brief} exactly for the tier "{tier}" (folder {REL}/{tier}/). The attached '
              'images are its inputs, in this order: ' + ', '.join(os.path.relpath(p, REPO) for p in inputs) + '. '
              'Produce the images with your built-in image generation tool and save them as specified.')
    with open(os.path.join(folder, f'codex_{stage}.log'), 'w') as log:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    done = sum(os.path.exists(os.path.join(folder, name)) for name in outputs)
    return tier, f'exit {result.returncode}, {done}/{len(outputs)} images'


def main():
    stage, tiers = sys.argv[1], sys.argv[2:]
    with ThreadPoolExecutor(4) as pool:
        for tier, status in pool.map(lambda t: session(stage, t), tiers):
            print('DONE', stage, tier, status, flush=True)


main()
