"""Hair spike centrelines from MM9's meshes: 19 tips (8 a side, 3 on top) in model/hair1/hair2. For each tip: rings of neighbours walking back to the head give the centreline, the width and the bones.
spike_lines() -> list of dict(points (k,3) tip first, width (k,), bones [ {name: w}... ], normal hint). numpy only."""
import numpy as np
HB = ('Xhairmid', 'XhmA', 'XhmB', 'Xhairtop', 'XhtA', 'XhtB', 'Xhairbot', 'XhbA', 'XhbB')
C0 = np.array([0, -0.2, 0.62])


def spike_lines(d):
    bones = d['bones']
    out = []
    for nm in ('model', 'hair1', 'hair2'):
        co, tri, J, W = d[nm + '_co'], d[nm + '_tri'], d[nm + '_J'], d[nm + '_W']
        dom = bones[J[np.arange(len(J)), W.argmax(1)]]
        nb = [set() for _ in co]
        for t in tri:
            for i in range(3):
                nb[t[i]].update(int(x) for x in t if x != t[i])
        r = np.linalg.norm(co - C0, axis=1)
        ish = np.array([str(x).startswith(HB) for x in dom])
        for i in range(len(co)):
            if not ish[i] or not all(r[j] < r[i] for j in nb[i]):
                continue
            seen = {i}; ring = [i]; pts = [co[i]]; wid = [0.0]; bn = [str(dom[i])]
            for step in range(4):
                nxt = sorted({j for k in ring for j in nb[k] if j not in seen and r[j] < r[ring[0]] + 0.01})
                nxt = [j for j in nxt if ish[j] or dom[j] in ('Xhead', 'Xheadpiv')][:6]
                if not nxt:
                    break
                c = co[nxt].mean(0)
                seen.update(nxt)
                pts.append(c)
                wid.append(float(max(np.linalg.norm(co[a] - co[b]) for a in nxt for b in nxt)))
                vals, cnt = np.unique(dom[nxt], return_counts=True)
                bn.append(str(vals[cnt.argmax()]))
                ring = nxt
                if str(bn[-1]) in ('Xhead', 'Xheadpiv'):
                    break
            out.append(dict(piece=nm, tip=i, points=np.array(pts), width=np.array(wid), bones=bn))
    return out
