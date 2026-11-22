"""Runs the Codex paint session of the World of Xeen certificate (BRIEF.md): one worker, both candidates; skipped when
both exist. The log is raw/xeen_cert_codex_run.log; the prompt goes on stdin (`codex exec -i` takes every following
argument as an image). Usage: python3 -I scripts/run_codex.py"""
import os
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
INPUTS = ['guide.png', 'refs/6winbg.png', 'refs/7winbg.png', 'refs/eg270001.png', 'refs/eg280001.png',
          'refs/eg140001.png']


def main():
    outputs = [os.path.join(HERE, 'raw', f'xeen_cert_{suffix}.png') for suffix in 'ab']
    if all(os.path.exists(path) for path in outputs):
        print('skipped')
        return
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for image in INPUTS:
        arguments += ['-i', os.path.join(HERE, image)]
    folder = os.path.relpath(HERE, REPO)
    prompt = (f'Follow the brief {folder}/BRIEF.md exactly. The attached images are its inputs, in this order: '
              + ', '.join(INPUTS) + '. Produce the images with your built-in image generation tool and save them as '
              'specified. Do not edit, move or delete any other file.')
    with open(os.path.join(HERE, 'raw', 'xeen_cert_codex_run.log'), 'w') as log:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=log, stderr=subprocess.STDOUT)
    print(f'exit {result.returncode}, {sum(os.path.exists(p) for p in outputs)}/2 images')


main()
