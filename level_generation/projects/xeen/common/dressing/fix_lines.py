import pathlib
"""A7, D-7.1: move props flagged dressing.walking_line (errors) square off the line, by what the audit asks plus 8.
fix_lines.py <key> [--dry]: reads output/studio_cal/<key>/a7_xaudit.txt and the installed map in root_d7, edits
devdocs/xeen/briefs/<key>/L4/objects.yml (`at:` of each deco). Run xcycle.sh afterwards and look again."""
import json, math, re, subprocess, sys
R = str(pathlib.Path(__file__).resolve().parents[5])
key = sys.argv[1]; dry = '--dry' in sys.argv
root = f'{R}/output/studio_cal/a7/root_d7'
exp = f'{R}/output/studio_cal/a7/dressing/fix_{key}.json'
subprocess.run([f'{R}/openyamm-studio/build-xeen/oymap', 'export', f'{root}/worlds/xeen/maps/xeen_{key}.blv',
                '--out', exp], capture_output=True)
m = json.load(open(exp))['map']
def centre(faces):
    vs = [m['vertices'][i] for f in faces for i in m['faces'][f]['vertices']]
    return sum(v[0] for v in vs) / len(vs), sum(v[1] for v in vs) / len(vs)
pat = re.compile(r'^error dressing\.walking_line: decoration \d+ \(([^,]+), [^,]+, radius (\d+)\) at \[(-?\d+), (-?\d+), '
                 r'-?\d+\] stands (\d+) from the walking line between the openings of faces ([\d+]+) and ([\d+]+)')
p = f'{R}/devdocs/xeen/briefs/{key}/L4/objects.yml'
s = open(p).read()
for line in open(f'{R}/output/studio_cal/{key}/a7_xaudit.txt'):
    g = pat.match(line)
    if not g:
        continue
    name, rad, x, y, d = g.group(1), int(g.group(2)), int(g.group(3)), int(g.group(4)), int(g.group(5))
    (ax, ay) = centre([int(f) for f in g.group(6).split('+')]); (bx, by) = centre([int(f) for f in g.group(7).split('+')])
    dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
    t = ((x - ax) * dx + (y - ay) * dy) / (L * L); px, py = ax + t * dx, ay + t * dy
    side = 1 if (x - px) * nx + (y - py) * ny >= 0 else -1
    k = rad + 64 + 8 - d
    new = [round(x + side * nx * k), round(y + side * ny * k)]
    ident = f'  - id: deco:{name}\n'
    if ident not in s:
        print('not found', name); continue
    a = s.index(ident); i = s.index('at: [', a); j = s.index(']', i)
    old = s[i:j + 1]
    print(f'{name}: {old} -> at: {new} (was {d} from line, needs {rad + 64})')
    s = s[:i] + f'at: [{new[0]}, {new[1]}]' + s[j + 1:]
if not dry:
    open(p, 'w').write(s)
