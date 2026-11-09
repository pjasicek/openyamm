"""Guideline checks on the generated geometry (GAME_ASSET_MODELLING_GUIDELINES.md sections 1-3):
vertex valence, sliver aspect, triangle size at the viewing distance, degenerate triangles. Prints a JSON report."""
import json, math, sys
import reactor_geometry as G

# In-game: model metres x 200 = world units; the party typically sees the Reactor from 600-2000 units at a
# 1600x900 view with ~75 degree vertical field of view: pixels per world unit = 900 / (2 tan(37.5 deg) d).
SCALE = 200.0
def px_per_metre(distance):
    return SCALE * 900.0 / (2.0 * math.tan(math.radians(37.5)) * distance)

r = G.build()
out = {}
for name, m in r['meshes'].items():
    P = m.verts
    edges = {}
    worst = []
    tiny = {}
    degenerate = 0
    for t, slot in zip(m.tris, m.mat):
        a, b, c = (P[i] for i in t)
        ab, bc, ca = G.length(G.sub(b, a)), G.length(G.sub(c, b)), G.length(G.sub(a, c))
        area = 0.5 * G.length(G.cross(G.sub(b, a), G.sub(c, a)))
        if area < 1e-9:
            degenerate += 1; continue
        longest = max(ab, bc, ca)
        aspect = longest * longest / (2.0 * area)   # 1.15 equilateral; large = sliver
        worst.append((round(aspect, 1), m.bone[t[0]], round(longest, 3)))
        px_area = area * px_per_metre(1000.0) ** 2
        if px_area < 10.0:
            tiny[m.bone[t[0]]] = tiny.get(m.bone[t[0]], 0) + 1
        for i, j in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edges.setdefault(i, set()).add(j); edges.setdefault(j, set()).add(i)
    worst.sort(reverse=True)
    valence = sorted(((len(v), m.bone[k]) for k, v in edges.items()), reverse=True)
    out[name] = {
        'triangles': len(m.tris), 'vertices': len(m.verts), 'degenerate': degenerate,
        'max_valence': valence[:5],
        'worst_aspect': worst[:8],
        'aspect_over_12': sum(1 for w in worst if w[0] > 12),
        'under_10px_at_1000_units_by_bone': dict(sorted(tiny.items(), key=lambda x: -x[1])),
    }
print(json.dumps(out, indent=1))
