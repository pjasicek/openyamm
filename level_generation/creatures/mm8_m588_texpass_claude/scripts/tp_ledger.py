"""Replaces (or appends) the ledger row of one model: tp_ledger.py <model> '<full row text starting with |>'"""
import sys
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'audit_mm678_20261111/fixes/LEDGER_texpass.md'
model, row = sys.argv[1], sys.argv[2]
lines = p.read_text().rstrip('\n').split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith(f'| {model} |')]
if hit:
    lines[hit[-1]] = row
else:
    lines.append(row)
tmp = p.with_suffix('.tmp')
tmp.write_text('\n'.join(lines) + '\n')
tmp.replace(p)
print('LEDGER', model)
