"""ASCII plan of a Xeen indoor maze (north up), wall codes shown on edges, with event/mob marks."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json, sys
R = _REPO_ROOT + '/reference/mm4_5_world_of_xeen/unpacked/'
n = int(sys.argv[1])
d = json.load(open(R + f'maps/dark_initial_state/maze{n:04}.dat.json'))
ev = json.load(open(R + f'events/dark_initial_state/maze{n:04}.evt.json'))
mob = json.load(open(R + f'maps/dark_initial_state/maze{n:04}.mob.json'))
cells = d['cells']
mark = {}
for e in ev:
    if e['line'] == 0:
        mark[(e['x'], e['y'])] = 'E'
sec = 0
for r in mob['records']:
    if r['terminator']:
        sec += 1
        continue
    if r['x'] > 15:
        continue
    c = 'oMw'[sec]
    if sec == 1:
        c = 'a' if r['spriteTableIndex'] == 0 else 'B'
    mark[(r['x'], r['y'])] = mark.get((r['x'], r['y']), '') + c
ch = {0: ' ', 8: '#', 9: 'D', 11: 'L', 2: ':', 4: '4', 14: 'e', 15: 'f'}
def wc(v):
    return ch.get(v, str(v % 10))
out = []
for y in range(15, -1, -1):
    top = ''
    mid = ''
    for x in range(16):
        nn, ee, ss, ww = cells[y][x]['wallsNESW']
        top += '+' + wc(nn) * 3
        m = mark.get((x, y), '')[:3]
        mid += wc(ww) + m.ljust(3)
    top += '+'
    mid += wc(cells[y][15]['wallsNESW'][1])
    out.append(top + f'   y{y}')
    out.append(mid)
bot = ''
for x in range(16):
    bot += '+' + wc(cells[0][x]['wallsNESW'][2]) * 3
out.append(bot + '+')
out.append(''.join(f'{x:<4}' for x in range(16)))
print('\n'.join(out))
