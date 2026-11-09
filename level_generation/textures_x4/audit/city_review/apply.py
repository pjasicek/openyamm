#!/usr/bin/env python3
"""Apply first-pass review files after the texture session checked them: apply.py JOB [JOB...].

ACCEPT lines are accepted (latest candidate); RETRY lines queue `tex.py retry` with their roll and note. Accepted
cut-outs whose native carries alpha then get the native alpha (`alpha-from-native`), as for the dungeons."""
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEX = HERE.parents[1] / 'tex.py'
sys.path.insert(0, str(TEX.parent))
import tex  # noqa: E402

for job in sys.argv[1:]:
    accept, retries = [], []
    for line in (HERE / f'{job}.txt').read_text().splitlines():
        line = line.split(' # ')[0].strip()
        if not line or line.startswith('#'):
            continue
        name, verdict, *rest = line.split(maxsplit=2)
        if verdict == 'ACCEPT':
            accept.append(name)
        elif verdict == 'RETRY':
            roll = re.search(r'roll=(\S+)', line).group(1)
            note = re.search(r'note="([^"]*)"', line).group(1)
            retries.append((name, roll, note))
    if accept:
        print(subprocess.run([sys.executable, str(TEX), 'accept', job, *accept], capture_output=True, text=True)
              .stdout.strip().splitlines()[-1])
    for name, roll, note in retries:
        command = [sys.executable, str(TEX), 'retry', job, name, '--note', note]
        if roll != '-':
            command += ['--roll', roll]
        result = subprocess.run(command, capture_output=True, text=True)
        print((result.stdout or result.stderr).strip().splitlines()[-1])
    inventory = tex.inventory()
    cutouts = [f'mm9/{name}' for name in accept if inventory[f'mm9/{name}'].get('cutout')]
    if cutouts:
        print(subprocess.run([sys.executable, str(TEX), 'alpha-from-native', *cutouts], capture_output=True,
                             text=True).stdout.strip())
