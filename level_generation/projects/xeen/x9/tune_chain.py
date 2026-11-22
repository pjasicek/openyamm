"""Places a chain's middle islands along a bowed line so that the rim-to-rim gaps are equal (design aid; prints)."""
import sys
import math
import geom as G
import design as D


def bez(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])


def gaps(chain, ts, ctrl):
    a, b = G.SPACE[chain[0]]['at'], G.SPACE[chain[-1]]['at']
    for sid, t in zip(chain[1:-1], ts):
        x, y = bez(a, ctrl, b, t)
        G.SPACE[sid]['at'] = (round(x / 128) * 128, round(y / 128) * 128)
    polys = G.outlines()
    out = []
    for u, v in zip(chain, chain[1:]):
        p = G.ray_exit(polys[u], G.SPACE[u]['at'], G.SPACE[v]['at'])
        q = G.ray_exit(polys[v], G.SPACE[v]['at'], G.SPACE[u]['at'])
        out.append(G.length(p, q))
    return out


def solve(chain, ctrl):
    n = len(chain) - 2
    ts = [(i + 1) / (n + 1) for i in range(n)]
    for _ in range(400):
        g = gaps(chain, ts, ctrl)
        mean = sum(g) / len(g)
        for i in range(n):
            # move island i toward the longer of its two gaps
            ts[i] -= (g[i] - g[i + 1]) / 80000.0
        ts = [min(max(t, 0.02), 0.98) for t in ts]
    g = gaps(chain, ts, ctrl)
    for sid in chain[1:-1]:
        print(sid, G.SPACE[sid]['at'])
    print('gaps', [round(x) for x in g])


solve(['room:se_nest', 'room:east_pillar', 'room:east_ledge', 'room:east_horn', 'room:aviary'], (17000, -2000))  # D-50: the aviary moved east (2026-11-21)
solve(['room:sw_nest', 'room:west_pillar', 'room:west_spine', 'room:west_shelf', 'room:nw_isle'], (-19500, -2500))


if __name__ == '__main__' and '--apply' in sys.argv:
    import re
    from pathlib import Path
    path = Path(__file__).with_name('design.py')
    src = path.read_text()
    for sid in ('room:east_pillar', 'room:east_ledge', 'room:east_horn', 'room:west_pillar', 'room:west_spine',
                'room:west_shelf'):
        x, y = G.SPACE[sid]['at']
        m = re.search(r"(dict\(id='%s'.*?at=)\(([-\d]+), ([-\d]+)\)" % re.escape(sid), src, re.S)
        src = src[:m.start()] + m.group(1) + f'({x}, {y})' + src[m.end():]
    # the landing: the unseen way exactly UNSEEN_CELLS cells
    link = next(l for l in D.LINKS if l['id'] == 'link:unseen_way')
    best = None
    for y in range(-6000, -2500, 8):
        G.SPACE['room:landing']['at'] = (0, y)
        p, q = G.link_ends(link, G.outlines())
        err = abs(G.length(p, q) - 512 * D.UNSEEN_CELLS)
        if best is None or err < best[0]:
            best = (err, y)
    m = re.search(r"(dict\(id='room:landing'.*?at=)\(([-\d]+), ([-\d]+)\)", src, re.S)
    src = src[:m.start()] + m.group(1) + f'(0, {best[1]})' + src[m.end():]
    path.write_text(src)
    print('applied; landing y', best[1], 'error', round(best[0]))
