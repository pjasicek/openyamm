"""Where to move a prop off a room's walking line: line_push.py <export.json> <faceA> <faceB> <x> <y> <clearance>.
The line runs between the centres of the two portal faces (as oymap audit's dressing.walking_line); prints the
distance now and the nearest point at the clearance, pushed square to the line away from it."""
import json, math, sys
m = json.load(open(sys.argv[1]))['map']
fa, fb = int(sys.argv[2]), int(sys.argv[3])
x, y, need = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
def centre(f):
    vs = [m['vertices'][i] for i in m['faces'][f]['vertices']]
    return sum(v[0] for v in vs) / len(vs), sum(v[1] for v in vs) / len(vs)
(ax, ay), (bx, by) = centre(fa), centre(fb)
dx, dy = bx - ax, by - ay
L = math.hypot(dx, dy)
t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (L * L)))
px, py = ax + t * dx, ay + t * dy
d = math.hypot(x - px, y - py)
print(f'line {ax:.0f},{ay:.0f} -> {bx:.0f},{by:.0f}; point {x:.0f},{y:.0f} is {d:.0f} from it')
if d < need:
    nx, ny = (-dy / L, dx / L)
    side = 1 if (x - px) * nx + (y - py) * ny >= 0 else -1
    k = need + 8 - d
    print(f'move to [{round(x + side * nx * k)}, {round(y + side * ny * k)}]')
