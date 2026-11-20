"""Torso weight refinement for the MM9 sheep, from mm9_wolf_claude (numpy only; used by refine_weights.py in Blender).
The sheep fix: Running frame 10, flank and shoulder folds (user 2026-10-30). The wolf text below still applies.
2026-10-30, after the skin flap in the rearing bite (AttackMelee frame ~17 at 48 fps).

Why: rig_body.py labels each vertex with the bone of the nearest MM9 vertex and diffuses the labels along the mesh.
1. MM9's rigid skin gives the leg roots (Bone11/Bone16 front, Bone01/Bone06 hind) the chest and hip sides, and the
   left and right roots meet directly under the brisket and in the groin: when one leg swings and the other does
   not, the skin between them folds.
2. The voxel body keeps fused fur layers as lips and pockets (chest fur over the top of the forelegs, the neck ruff
   over the throat). Diffusion along the surface gives the two sides of a pocket different bones (the lip the chest,
   the skin under it the leg), so a pocket opens into a flap with a hard crease when the leg or head turns.

3. The fit (fit_quad.py) and the voxel remesh left 90 folded-over rest faces (normal against the surrounding
   surface) where the elbow meets the chest and at the tail base: torn sawtooth slits even in the standing pose.

What:
- Untangle (untangle()): Laplacian relax around the folded rest faces until none is left or ten passes bring no
  improvement (90 -> 8 faces, mean move 0.015, max 0.10 model units; UVs unchanged).
- Spatial smoothing: each torso vertex takes the Gaussian-weighted mean (SIGMA, Euclidean distance, not along the
  surface) of the weights around it, so both sides of a pocket move together and every leg/chest border is wide.
  Sources from another limb chain are ignored (the tail hangs between the thighs). Lower legs below the elbow/knee,
  the tail past its base, the muzzle, jaw, ears and the rigid small pieces keep their
  weights; the change fades in over a few edge rings from them.
- Midline (after the smoothing): leg-subtree weights fade to the core bone (Bone32 chest at the front, Bone33 hips
  at the back) towards the body midline (smoothstep on |x| over MID), outside the tail and the kept parts, so the
  left and right leg never share skin.
- At most four influences, small ones dropped, normalised.
Coordinates are Blender world (z up, the wolf faces -y).
"""
import numpy as np

MIDX = float(__import__('os').environ.get('REFINE_MIDX', '0.15'))
MIDX0 = float(__import__('os').environ.get('REFINE_MIDX0', '0.07'))
# limb chains kept as weighted: root, child joint (axis), fit chain index (fit_quad.py CHAINS order), kept past this
# axis fraction and within this distance of the root-child axis (the fit's chains reach the brisket and groin)
KEEP = [('Xflegpiv01', 'Xfleg01', 0, 0.55, 0.13), ('Xflegpiv', 'Xfleg', 1, 0.55, 0.13),
        ('Xblegpiv01', 'Xbleg01', 2, 1.3, 0.15), ('Xblegpiv', 'Xbleg', 3, 1.3, 0.15)]
KEEP_BONES = ('Xheadpiv', 'Xhead', 'Xjawpiv', 'Xearpiv', 'Xear', 'Xearpiv01', 'Xear01', 'Xtail')
# midline: leg roots whose subtrees fade out, target core bone, smoothstep |x| range, y range (front/back half)
MID = [(('Xflegpiv', 'Xflegpiv01'), 'Xback', (MIDX0, MIDX), (-9.0, 0.1)),
       (('Xblegpiv', 'Xblegpiv01'), 'XbackC', (MIDX0, MIDX), (0.1, 9.0))]
_e = __import__('os').environ.get
SPINE = ('Xback', 'XbackA', 'XCENTER', 'XbackB', 'XbackC', 'Xfrontleg')
SPINE_SIGMA = float(_e('SPINE_SIGMA', '0.11'))
ALONG = [(('Xblegpiv', 'Xblegpiv01'), 'XCENTER', (-0.36, -0.14), -1),   # hind root off the belly: gone at y 0.14, whole at y 0.36
         (('Xflegpiv', 'Xflegpiv01'), 'XCENTER', (-0.14, 0.04), 1)]     # front root: whole at y -0.14, gone at y 0.04
HEIGHT = [(('Xflegpiv', 'Xflegpiv01'), 'Xback', (float(_e('H_F0', '0.30')), float(_e('H_F1', '0.40'))), (-9.0, 0.1)),
          (('Xblegpiv', 'Xblegpiv01'), 'XbackC', (float(_e('H_H0', '0.46')), float(_e('H_H1', '0.64'))), (0.1, 9.0))]
SIGMA = float(__import__('os').environ.get('REFINE_SIGMA', '0.08'))     # model units (body width about 0.5)
FADE_RINGS = 4


def subtree(root, bones, parents):
    out = {root}
    grew = True
    while grew:
        grew = False
        for b, p in zip(bones, parents):
            if p in out and b not in out:
                out.add(b)
                grew = True
    return out


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def refine(co, tris, W, bones, heads, parents, chain, piece, keep=KEEP, keep_bones=KEEP_BONES, mid=MID,
           sigma=SIGMA, fade_rings=FADE_RINGS):
    bones = [str(b) for b in bones]
    parents = [str(p) for p in parents]
    bi = {b: i for i, b in enumerate(bones)}
    n = len(co)
    body = piece == 0
    W0 = W
    report = {'mid': {}, 'keep': {}}
    # 1. kept parts
    kept = ~body | (W0[:, [bi[b] for b in keep_bones if b in bi]].sum(1) > 0)
    for root, child, ch, frac, rmax in keep:
        a, b = heads[bi[root]], heads[bi[child]]
        ax = b - a
        t = (co - a) @ ax / (ax @ ax)
        rad = np.linalg.norm((co - a) - t[:, None] * ax, axis=1)
        k = body & (chain == ch) & (t >= frac) & (rad <= rmax)
        kept |= k
        report['keep'][root] = int(k.sum())
    # fade: 0 on kept vertices, 1 after FADE_RINGS edge rings
    E = np.unique(np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1), axis=0)
    ring = np.where(kept, 0, fade_rings).astype(float)
    for r in range(1, fade_rings):
        near = np.zeros(n, bool)
        prev = ring < r
        near[E[prev[E[:, 0]], 1]] = True
        near[E[prev[E[:, 1]], 0]] = True
        ring[near & (ring > r)] = r
    alpha = ring / fade_rings
    # 2./3. spatial smoothing (sources: all body vertices; small pieces are no sources)
    src = np.nonzero(body)[0]
    S = W.copy()
    tgt = np.nonzero(alpha > 0)[0]
    for i0 in range(0, len(tgt), 512):
        idx = tgt[i0:i0 + 512]
        d2 = ((co[idx, None, :] - co[None, src, :]) ** 2).sum(-1)
        g = np.exp(-d2 / (2 * sigma * sigma))
        g[d2 > (3 * sigma) ** 2] = 0
        # no mixing between two different limbs (left/right legs, tail and thighs); the core mixes with all
        cv, cu = chain[idx, None], chain[None, src]
        g[(cv != cu) & (cv >= 0) & (cu >= 0)] = 0
        S[idx] = (g @ W[src]) / g.sum(1, keepdims=True)
    X = W * (1 - alpha[:, None]) + S * alpha[:, None]
    # 4. midline fade (after the smoothing, which would carry leg weight back onto the midline)
    for legs, core, (x0, x1), (y0, y1) in mid:
        cols = sorted(bi[b] for b in set().union(*[subtree(r, bones, parents) for r in legs]))
        f = smoothstep(x0, x1, np.abs(co[:, 0]))
        s = body & (chain != 4) & (co[:, 1] > y0) & (co[:, 1] < y1) & (f < 1)
        moved = X[s][:, cols] * ((1 - f[s]) * alpha[s])[:, None]   # kept parts (lower legs) keep theirs
        X[np.ix_(s, cols)] -= moved
        X[s, bi[core]] += moved.sum(1)
        report['mid'][core] = {'verts': int(s.sum()), 'moved_weight': round(float(moved.sum()), 2)}
    # 3b. torso skin never follows the swinging lower leg (Xfleg turns up to 98 deg): lower-leg weight on torso vertices
    # goes to the leg's root pivot, which the fades below take to the core
    for root in ('Xflegpiv', 'Xflegpiv01', 'Xblegpiv', 'Xblegpiv01'):
        cols = sorted(bi[b] for b in subtree(root, bones, parents) if b != root)
        t = (alpha > 0) & body
        mv = X[t][:, cols] * alpha[t, None]
        X[np.ix_(t, cols)] -= mv
        X[t, bi[root]] += mv.sum(1)
    # 4a. along the body: the belly between the legs follows the core, the hind root reaches forward to y1, the front root
    # back to y1 (a wide smooth band across the flank)
    for legs, core, (y0, y1), sign in ALONG:
        cols = sorted(bi[b] for b in set().union(*[subtree(r, bones, parents) for r in legs]))
        f = smoothstep(y0, y1, co[:, 1] * sign)
        s = body & (chain != 4) & (f > 0)
        moved = X[s][:, cols] * (f[s] * alpha[s])[:, None]
        X[np.ix_(s, cols)] -= moved
        X[s, bi[core]] += moved.sum(1)
    # 4b. height fade: the leg pivots sit at the bottom of the fleece, so skin above them must not follow the leg (the
    # swing pushed the chest down into a bag): above the band the leg subtree's weight goes to the core
    for legs, core, (z0, z1), (y0, y1) in HEIGHT:
        cols = sorted(bi[b] for b in set().union(*[subtree(r, bones, parents) for r in legs]))
        f = smoothstep(z0, z1, co[:, 2])
        s = body & (chain != 4) & (co[:, 1] > y0) & (co[:, 1] < y1) & (f > 0)
        moved = X[s][:, cols] * (f[s] * alpha[s])[:, None]
        X[np.ix_(s, cols)] -= moved
        X[s, bi[core]] += moved.sum(1)
        report.setdefault('height', {})[core] = {'verts': int(s.sum()), 'moved_weight': round(float(moved.sum()), 2)}
    # 4c. the fades hand weight to different spine bones in front of and behind y 0.1: smooth the spine share among the
    # torso vertices (Euclidean Gaussian) so the belly has no step where the spine bends; each vertex keeps its spine total
    spine = [bi[b] for b in SPINE]
    t = np.nonzero((alpha > 0) & body)[0]
    for i0 in range(0, len(t), 512):
        idx = t[i0:i0 + 512]
        d2 = ((co[idx, None, :] - co[None, t, :]) ** 2).sum(-1)
        g = np.exp(-d2 / (2 * SPINE_SIGMA ** 2))
        g[d2 > (3 * SPINE_SIGMA) ** 2] = 0
        G = g @ X[t][:, spine]
        tot = X[idx][:, spine].sum(1, keepdims=True)
        X[np.ix_(idx, spine)] = G / np.maximum(G.sum(1, keepdims=True), 1e-9) * tot
    report['smoothed_verts'] = int((alpha > 0).sum())
    report['kept_verts'] = int(kept.sum())
    # 5. four influences, drop small, normalise
    order = np.argsort(-X, axis=1)
    out = np.zeros_like(X)
    for i in range(n):
        keep_i = order[i, :4]
        row = np.zeros(X.shape[1])
        row[keep_i] = X[i, keep_i]
        row[row < 0.02] = 0
        out[i] = row / row.sum()
    out[~body] = W0[~body]
    report['max_influences'] = int((out > 0).sum(1).max())
    report['changed_verts'] = int((np.abs(out - W0).max(1) > 1e-3).sum())
    return out, report


# ---- geometry: untangle the fold-overs of the rest mesh -----------------------------------------------------------
def edges_of(tris):
    return np.unique(np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), 1), axis=0)


def folded_faces(co, t, smooth_rings=6):
    """Faces of t whose normal points against the smoothed normal of their neighbourhood (fold-overs, pockets)."""
    fn = np.cross(co[t[:, 1]] - co[t[:, 0]], co[t[:, 2]] - co[t[:, 0]])
    a = np.linalg.norm(fn, axis=1)
    fn = fn / np.maximum(a, 1e-15)[:, None]
    vn = np.zeros_like(co)
    for c in range(3):
        np.add.at(vn, t[:, c], fn * a[:, None])
    E = edges_of(t)
    for _ in range(smooth_rings):
        acc = vn.copy()
        np.add.at(acc, E[:, 0], vn[E[:, 1]])
        np.add.at(acc, E[:, 1], vn[E[:, 0]])
        vn = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)
    sm = vn[t].mean(1)
    return (fn * sm).sum(1) < 0


UNTANGLE_RINGS = 2
UNTANGLE_ITERS = 80


def untangle(co, tris, piece, rings=UNTANGLE_RINGS, iters=UNTANGLE_ITERS):
    """Laplacian-relax the body around its folded rest faces (fit/voxel pockets at the armpits and the tail base)
    until none is left or ten passes bring no improvement: returns new positions and a report."""
    t = tris[(piece[tris] == 0).all(1)]
    E = edges_of(t)
    n = len(co)
    deg = np.zeros(n)
    np.add.at(deg, E[:, 0], 1)
    np.add.at(deg, E[:, 1], 1)
    p = co.copy()
    start = int(folded_faces(p, t).sum())
    touched = np.zeros(n, bool)
    best, best_k = start, 0
    for k in range(iters):
        bad = folded_faces(p, t)
        if bad.sum() < best:
            best, best_k = int(bad.sum()), k
        # stop when done, or when the last few faces stay folded (more passes only drift the pocket)
        if not bad.any() or k - best_k >= 10:
            break
        m = np.zeros(n)
        m[t[bad].ravel()] = 1
        for r in range(rings):
            val = 1 - (r + 1) / (rings + 1)
            grow = np.zeros(n)
            np.maximum.at(grow, E[:, 0], np.where(m[E[:, 1]] > val, val, 0))
            np.maximum.at(grow, E[:, 1], np.where(m[E[:, 0]] > val, val, 0))
            m = np.maximum(m, grow)
        touched |= m > 0
        acc = np.zeros_like(p)
        np.add.at(acc, E[:, 0], p[E[:, 1]])
        np.add.at(acc, E[:, 1], p[E[:, 0]])
        p = p + 0.5 * m[:, None] * (acc / np.maximum(deg, 1)[:, None] - p)
    disp = np.linalg.norm(p - co, axis=1)
    return p, {'folded_before': start, 'folded_after': int(folded_faces(p, t).sum()), 'iterations': k + 1,
               'moved_verts': int((disp > 1e-6).sum()), 'max_move': round(float(disp.max()), 4),
               'mean_move_touched': round(float(disp[touched].mean()) if touched.any() else 0.0, 4)}


# ---- teeth: each fang rides the jaw it sits on --------------------------------------------------------------------
JAWS = ('Bone28', 'Bone30')   # upper muzzle, lower jaw


def seat_teeth(co, tris, W, bones, piece, jaws=JAWS, k=8):
    """rig_body.py splits the teeth by a least-squares plane between the MM9 upper and lower jaw vertices; near the
    front of the mouth that plane put two lower fangs on the upper jaw (they floated 4.6 cm off the gums in the bite).
    Each small piece weighted to a jaw is made rigid on the jaw that owns most of the k body vertices nearest it."""
    bones = [str(b) for b in bones]
    ja, jb = bones.index(jaws[0]), bones.index(jaws[1])
    body = np.nonzero(piece == 0)[0]
    jaw_v = body[(W[body, ja] + W[body, jb]) > 0.5]
    par = np.arange(len(co))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for t in tris[(piece[tris] != 0).all(1)]:
        for a, b in ((t[0], t[1]), (t[1], t[2])):
            ra, rb = find(a), find(b)
            if ra != rb:
                par[ra] = rb
    roots = np.array([find(i) for i in range(len(co))])
    W = W.copy()
    moved = []
    for r in np.unique(roots[piece != 0]):
        v = np.nonzero(roots == r)[0]
        if W[v][:, [ja, jb]].sum(1).mean() < 0.5:
            continue
        d2 = ((co[v, None, :] - co[None, jaw_v, :]) ** 2).sum(-1)
        near = jaw_v[np.argsort(d2.min(0))[:k]]
        side = ja if (W[near, ja] > W[near, jb]).mean() > 0.5 else jb
        if W[v, side].mean() < 0.999:
            moved.append({'verts': len(v), 'centre': np.round(co[v].mean(0), 3).tolist(), 'to': bones[side]})
        W[v] = 0
        W[v, side] = 1
    return W, moved
