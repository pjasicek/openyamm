#!/usr/bin/env python3
"""One codex exec image worker per sheet. Usage: gen.py NAME VERSION; the prompt is prompts/NAME.txt and the
reference images are refs/ref_a.png and refs/ref_b.png. Writes raw/NAME_vVERSION.png (unchanged) and a log."""
import subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parent
WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using all attached images as reference images and the IMAGE PROMPT below.
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""
name, version = sys.argv[1], sys.argv[2]
refs = ['ref_a.png', 'ref_b.png']
target = W / 'raw' / f'{name}_v{version}.png'
prompt = (W / 'prompts' / f'{name}.txt').read_text().strip()
command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(W), '--skip-git-repo-check']
for ref in refs:
    command += ['-i', str(W / 'refs' / ref)]
with open(W / 'raw' / f'{name}_v{version}.log', 'w') as log:
    subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True, stdout=log,
                   stderr=subprocess.STDOUT, timeout=900)
print(target, target.exists())
