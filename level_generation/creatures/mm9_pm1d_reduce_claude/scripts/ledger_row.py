"""Set this project's ledger row (82, mm9_pm1d.glb) columns. Run under the flock.
usage: ledger_row.py <status> [after] [lods] [project] [rollback]"""
import os, sys
P = '/home/pjasicek/github/OpenYAMM/level_generation/creatures/REDUCTION_LEDGER.md'
lines = open(P).read().split('\n')
hit = 0
for i, l in enumerate(lines):
    c = l.split('|')
    if len(c) > 11 and c[1].strip() == '82' and '`mm9_pm1d.glb`' in c[4]:
        args = sys.argv[1:]
        c[8] = ' ' + args[0] + ' '
        if len(args) > 1: c[6] = ' ' + args[1] + ' '
        if len(args) > 2: c[7] = ' ' + args[2] + ' '
        if len(args) > 3: c[9] = ' ' + args[3] + ' '
        if len(args) > 4: c[10] = ' ' + args[4] + ' '
        lines[i] = '|'.join(c); hit += 1
assert hit == 1, hit
tmp = P + '.tmp_pm1d'
open(tmp, 'w').write('\n'.join(lines))
os.replace(tmp, P)
print(lines[[j for j, l in enumerate(lines) if '`mm9_pm1d.glb`' in l][0]])
