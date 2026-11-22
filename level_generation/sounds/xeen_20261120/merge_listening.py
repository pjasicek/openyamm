#!/usr/bin/env python3
"""Merge listening.yml (lane AU's choices and notes) into picks.yml; run `process` afterwards to apply the choices."""
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
notes = yaml.safe_load((HERE / 'listening.yml').read_text()) or {}
picks_path = HERE / 'picks.yml'
text = picks_path.read_text()
header = ''.join(line + '\n' for line in text.splitlines() if line.startswith('#'))
picks = yaml.safe_load(text) or {}
for job_id, entry in notes.items():
    target = picks.setdefault(job_id, {})
    if 'choice' in entry:
        target['choice'] = entry['choice']
    else:
        target.pop('choice', None)
    target['listening'] = entry.get('listening', '')
temporary = picks_path.with_name('picks.yml.tmp')
temporary.write_text(header + yaml.safe_dump(picks, sort_keys=False, allow_unicode=True, width=120))
temporary.replace(picks_path)
print(f'{len(notes)} notes merged')
