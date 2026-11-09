"""Shared hydra part logic (Blender-free numpy): each vertex's chain from its strongest bone weight, its arc position
along that chain, and the head region (arc at least the Head bone start minus HEAD_BACK), used by reduce_bent.py
(heads kept at full density) and uv_atlas.py (heads in their own atlas tiles)."""
import numpy as np

HEAD_BACK = 0.035


def owners(obj, chains):
    bone_chain = {nm: ci for ci, c in enumerate(chains) for nm in c['names']}
    names = {g.index: g.name for g in obj.vertex_groups}
    return np.array([bone_chain[names[max(v.groups, key=lambda x: x.weight).group]] for v in obj.data.vertices])


def nearest_on_chain(J, p):
    best = (1e9, 0, 0.0)
    for i in range(len(J) - 1):
        d = J[i + 1] - J[i]; t = float(np.clip((p - J[i]) @ d / (d @ d), 0, 1))
        dist = float(np.linalg.norm(p - (J[i] + t * d)))
        if dist < best[0]:
            best = (dist, i, t)
    return best[1], best[2]


def arc(J, p):
    i, t = nearest_on_chain(J, p)
    L = np.linalg.norm(np.diff(J, axis=0), axis=1)
    return L[:i].sum() + t * L[i]


def head_part(co, owner, chains, back=HEAD_BACK):
    """Per vertex: k for head k, 0 elsewhere."""
    out = np.zeros(len(co), int)
    for v in range(len(co)):
        k = owner[v]
        if k:
            J = np.asarray(chains[k]['joints'] if 'joints' in chains[k] else chains[k]['J'])
            start = np.linalg.norm(np.diff(J, axis=0), axis=1)[:-1].sum()
            if arc(J, co[v]) >= start - back:
                out[v] = k
    return out


def head_flood(co, adj, chains, back=HEAD_BACK, ring=1.35):
    """Per vertex: k for head k, 0 elsewhere, by flood fill from the snout tip that may not cross the neck's cut ring:
    a plane across the neck at arc (Head bone start - back), blocking only edges within ring x the neck surface's
    median distance from the axis there (horns sweeping back cross the plane further out). Everything attached to the skull (horns sweeping back, fins, crests) belongs to the head; a cut by arc
    position alone gave the purple head's horns to the neck."""
    out = np.zeros(len(co), int)
    for k in range(1, len(chains)):
        J = np.asarray(chains[k]['joints']); R = np.asarray(chains[k]['radius'])
        L = np.linalg.norm(np.diff(J, axis=0), axis=1); s = L[:-1].sum() - back
        i = int(np.searchsorted(np.cumsum(L), s)); t = (s - L[:i].sum()) / L[i]
        P = J[i] + t * (J[i + 1] - J[i]); T = (J[i + 1] - J[i]) / L[i]
        side = (co - P) @ T
        radial = np.linalg.norm((co - P) - np.outer(side, T), axis=1)
        at_plane = (np.abs(side) < 0.012) & (radial < 3 * R.max())
        near = radial < ring * float(np.median(radial[at_plane]))
        start = int(np.argmin(np.linalg.norm(co - J[-1], axis=1)))
        seen = {start}; stack = [start]
        while stack:
            a = stack.pop()
            for b in adj[a]:
                if b in seen or out[b]:
                    continue
                if side[a] * side[b] <= 0 and (near[a] or near[b]):
                    continue
                seen.add(b); stack.append(b)
        if len(seen) > 0.5 * len(co):
            raise ValueError(f'head {k} flood leaked past its cut ring')
        out[list(seen)] = k
    return out
