#!/usr/bin/env python3
"""Barred gates for the six slime pens of XD-01 L4: one mover per pen (the bottom rail), parts for the bars and the
top rail, each a rotated box standing 20 inside the pen's mouth wall, centred on the gate opening. Prints YAML for
objects.yml movers, lights and decorations. Numbers come from the pens' outlines in rooms.yml (the mouth is each pen's
outline edge 0, the gate opening is centred on it)."""
import math
pens = {
    1: [[1395, 5464], [1608, 5677], [1416, 5939], [1133, 5656]],
    2: [[1253, 5143], [1375, 5437], [1095, 5598], [941, 5228]],
    3: [[1375, 4483], [1253, 4777], [941, 4692], [1095, 4322]],
    4: [[1608, 4243], [1395, 4456], [1133, 4264], [1416, 3981]],
    5: [[1929, 4101], [1635, 4223], [1474, 3943], [1844, 3789]],
    6: [[2829, 4456], [2616, 4243], [2808, 3981], [3091, 4264]],
}
INSET = 22      # bars stand this far inside the pen from its mouth wall
SPAN = 272      # rails' length (the opening is 256 wide)
BARS = 7        # bars, 40 apart
BAR = 14        # a bar's thickness
def box(cx, cy, ux, uy, length, depth):
    # a rotated box centred at (cx, cy), long side along u; points counter-clockwise, whole units
    vx, vy = -uy, ux
    hl, hd = length / 2, depth / 2
    pts = [(cx - ux * hl - vx * hd, cy - uy * hl - vy * hd), (cx + ux * hl - vx * hd, cy + uy * hl - vy * hd),
           (cx + ux * hl + vx * hd, cy + uy * hl + vy * hd), (cx - ux * hl + vx * hd, cy - uy * hl + vy * hd)]
    pts = [[round(x), round(y)] for x, y in pts]
    area = sum(pts[i][0] * pts[(i + 1) % 4][1] - pts[(i + 1) % 4][0] * pts[i][1] for i in range(4))
    if area < 0:
        pts.reverse()
    return pts
def fmt(pts):
    return "[" + ", ".join(f"[{x}, {y}]" for x, y in pts) + "]"
out = []
for n, o in pens.items():
    (ax, ay), (bx, by) = o[0], o[1]
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -uy, ux                     # left of the edge: inside a counter-clockwise outline
    mx, my = (ax + bx) / 2, (ay + by) / 2
    cx, cy = mx + nx * INSET, my + ny * INSET
    out.append(f"  - id: mover:pen_{n}_bars")
    out.append(f"    room: room:pen_{n}")
    out.append(f"    outline: {fmt(box(cx, cy, ux, uy, SPAN, 16))}")
    out.append("    height: 16")
    out.append("    travel: [0, 0, 322]")
    out.append("    speed: 160")
    out.append("    surface: {texture: rustjlf2n5, size: [128, 128]}")
    out.append("    parts:")
    for i in range(BARS):
        t = (i - (BARS - 1) / 2) * 40
        out.append(f"      - {{outline: {fmt(box(cx + ux * t, cy + uy * t, ux, uy, BAR, BAR))}, bottom: 16, height: 216}}")
    out.append(f"      - {{outline: {fmt(box(cx, cy, ux, uy, SPAN, 16))}, bottom: 232, height: 16}}")
    out.append(f"    notes: \"Pen {n}'s barred gate: a bottom rail (the mover's block), seven iron bars and a top rail (its parts), "
               f"standing {INSET} inside the pen's mouth; it rises 322 into the pen's ceiling.\"")
print("\n".join(out))
print()
for n, o in pens.items():
    cx = sum(p[0] for p in o) / 4; cy = sum(p[1] for p in o) / 4
    print(n, round(cx), round(cy))

print()
for n, o in pens.items():
    (ax, ay), (bx, by) = o[0], o[1]
    L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = -uy, ux
    cx = sum(p[0] for p in o) / 4; cy = sum(p[1] for p in o) / 4
    print(f"pen {n}: centre {round(cx)},{round(cy)} back {round(cx+nx*90)},{round(cy+ny*90)} side {round(cx+ux*80)},{round(cy+uy*80)} light {round(cx+nx*40)},{round(cy+ny*40)}")
