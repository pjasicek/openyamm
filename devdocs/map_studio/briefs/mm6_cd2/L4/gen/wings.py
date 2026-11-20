"""Per-wing account of the rebuild: sectors, how each is drawn, the comparison's score. Prints markdown."""
import json, collections
import overrides as OV
from lib import *
g = json.load(open(D + 'gen_rooms.json'))
rep = json.load(open(D + 'compare/report.json'))
sc = {s['sector']: s for s in rep['sectors']}
rooms_by = collections.defaultdict(list)
for r in g['rooms']:
    rooms_by[r['sector']].append(r['id'])
frames = {int(k) for k in g['frames']}
names = {1: 'Wing 1: entry, crypt level and ground floor of the keep', 2: 'Wing 2: stair hall, spiral, upper floor and the south cavern',
         3: 'Wing 3: great hall, its galleries, low tunnels and the north cavern', 4: 'Wing 4: gatehouse, throne hall and the inner ranges',
         5: 'Wing 5: west ward, west court, wall walk and the outer caverns', 6: 'Reached only by teleport'}
tot = collections.Counter()
for w in sorted(names):
    secs = [s for s in sorted(OV.WINGS) if OV.WINGS[s] == w]
    pts = sum(sc[s]['points'] for s in secs if s in sc)
    score = sum(sc[s]['points'] * sc[s]['score'] for s in secs if s in sc) / max(1, pts)
    drawn = [s for s in secs if rooms_by.get(s)]
    asop = [s for s in secs if s in frames]
    print('\n### %s\n' % names[w])
    print('%d sectors: %d drawn as %d rooms, %d as the thickness of an opening; compare score %.1f %% over %d points.\n' % (
        len(secs), len(drawn), sum(len(rooms_by[s]) for s in drawn), len(asop), 100 * score, pts))
    print('| Sector | What it is | Drawn as | Score |')
    print('|---|---|---|---|')
    for s in secs:
        how = ('%d room%s' % (len(rooms_by[s]), '' if len(rooms_by[s]) == 1 else 's')) if rooms_by.get(s) else ('opening' if s in frames else 'not drawn')
        print('| %d | %s | %s | %s |' % (s, OV.NAMES[s], how, ('%.0f %%' % (100 * sc[s]['score'])) if s in sc else '-'))
    tot['sectors'] += len(secs); tot['drawn'] += len(drawn); tot['open'] += len(asop); tot['compared'] += sum(1 for s in secs if s in sc)
print('\nTotals:', dict(tot))
