"""Prints RESULTS.md's measured tables (Markdown) from the work directory: the playthrough per difficulty, the
real-group results and the generic pack sizes per build, stage and difficulty."""
import json, os
from simdir import S

D = json.load(open(os.path.join(S, 'page', 'data.json')))
LABELS = D['labels']
DIFFS = [('normal', 'Normal'), ('maw', 'MAW'), ('hard', 'Hard'), ('hell', 'Hell'), ('nightmare', 'Nightmare'),
         ('doom', 'Doom'), ('insanity', 'Road to Insanity'), ('madness', 'Beyond Madness')]
LEVELS = [10, 50, 200, 500]
ORDER = ['dragon', 'seraph', 'troll', 'troll_staff', 'shaman', 'minotaur_dual', 'troll_knight', 'vamp_knight',
         'knight_sns', 'knight_2h', 'minotaur_knight_dual', 'minotaur_one', 'dk_vampire', 'dk_minotaur_dual',
         'dk_minotaur', 'nosferatu', 'monk', 'archer', 'archmage', 'elementalist', 'assassin', 'priest']
route = {(r['b'], r['L'], r['d']): r for r in D['rows'] if r['m'] == 'route'}
real = {(r['b'], r['L'], r['d']): r for r in D['real']}
PT = D['pt']

print('### Playthrough (median of five seeds)\n')
print('Per stage: monster level there · maps cleared · monsters killed · chests opened · quest share of experience.\n')
print('| Difficulty | ' + ' | '.join(f'Level {L}' for L in LEVELS) + ' | Full clear ends at |')
print('|---|' + '---|' * (len(LEVELS) + 1))
for d, name in DIFFS:
    cells = []
    for L in LEVELS:
        p = PT[d].get(str(L)); r = route.get(('knight_sns', L, d))
        if p:
            cells.append(f"L{r['M'] if r else '?'} · {p['maps']} · {p['kills']:,} · {p['chests']} · {p['qshare']} %")
        else:
            cells.append(f"not reached (stand-in: end of clear, monsters L{r['M']})" if r else 'not reached')
    print(f'| {name} | ' + ' | '.join(cells) + f" | level {PT[d]['final']} |")

for d, name in DIFFS:
    print(f'\n### Real map groups: {name}\n')
    print('Share of the monsters (%) in groups the build beats. P4 = pulled four at a time, no potions; P4+ = with '
          'potions; W = whole group at once, no potions; s = seconds of fighting per monster in pulls of 4. '
          'Class = the class the character has at that stage.\n')
    print('| Build | ' + ' | '.join(f'L{L}: P4 / P4+ / W · s · class' for L in LEVELS) + ' |')
    print('|---|' + '---|' * len(LEVELS))
    for b in ORDER:
        cells = []
        for L in LEVELS:
            r = real.get((b, L, d))
            cells.append(f"{r['ok4']} / {r['ok4p']} / {r['ok']} · {r['spm4']} · {r['cls']}" if r else '–')
        print(f'| {LABELS[b]} | ' + ' | '.join(cells) + ' |')

print('\n### Generic packs: largest pack survived standing, no potions\n')
print('B-tier physical melee monsters of the content level, all attacking from the first second; 40 = 40 or more. '
      'Columns: Normal, MAW, Hard, Hell, Nightmare, Doom, Road to Insanity, Beyond Madness.\n')
print('| Build | ' + ' | '.join(f'L{L}' for L in LEVELS) + ' |')
print('|---|' + '---|' * len(LEVELS))
for b in ORDER:
    cells = []
    for L in LEVELS:
        cells.append(' '.join(str(round(route[(b, L, d)]['mx'])) if (b, L, d) in route else '–' for d, _ in DIFFS))
    print(f'| {LABELS[b]} | ' + ' | '.join(cells) + ' |')
