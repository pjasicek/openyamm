# doorshots.py <scene.yml> <out_dir> <tour.yml>: two views of each door (both sides), and chests from above-front.
import yaml, sys, math
scene = yaml.safe_load(open(sys.argv[1]))
ids = yaml.safe_load(open('devdocs/xeen/briefs/xd02/L4/ids.lock.yml'))
names = {v: k for k, v in ids.get('doors', ids).items()} if isinstance(ids.get('doors'), dict) else {}
def find(node):
    if isinstance(node, dict):
        if 'doors' in node and isinstance(node['doors'], list) and node['doors'] and 'x_offsets' in node['doors'][0]:
            return node['doors']
        for v in node.values():
            r = find(v)
            if r: return r
lines = [f'output_dir: {sys.argv[2]}', 'exit: true', 'settle_seconds: 1.2', 'shots:']
want = {1: 'bunk', 2: 'chapel', 4: 'foot', 7: 'gate_station', 9: 'hoist_gate', 10: 'lamp', 12: 'strongroom', 13: 'tally', 14: 'vent1', 6: 'gate_landing'}
for d in find(scene):
    i = d['door_id']
    if i not in want: continue
    xs, ys, zs = d['x_offsets'], d['y_offsets'], d['z_offsets']
    cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)
    if i == 2:  # two leaves: take both
        pass
    dx, dy = max(xs) - min(xs), max(ys) - min(ys)
    nx, ny = (1, 0) if dx < dy else (0, 1)
    for s, side in ((1, 'a'), (-1, 'b')):
        x, y = cx + s * nx * 360, cy + s * ny * 360
        yaw = math.atan2(-s * ny, -s * nx)
        lines.append(f'  - {{name: door-{want[i]}-{side}, position: [{int(x)}, {int(y)}, {int(z0)}], yaw: {yaw:.4f}, pitch: 0.0, commands: ["render hud off"]}}')
open(sys.argv[3], 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
