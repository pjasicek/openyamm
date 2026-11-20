#!/usr/bin/env python3
"""Step 2b: choose which leaf cards stay, per LOD, by what they show (system Python).

Rasterises the LOD's cards (texture alpha >= 0.5, as overdraw.py) and its opaque parts (bark and the shell from
work/<id>/shell.npz) orthographically from many views (8 azimuths x elevations -70, -40, 0, 20, 45, 75; eye-level views
weigh most). Per view pixel, `count` = card fragments in front of the opaque depth. A pixel's value is 1 once a card
covers it (`fringe` x that outside the opaque silhouette: the crown's leafy edge, i.e. its coverage) plus `depth`
for a second card. Reverse greedy (lazy heap): the card whose removal loses the least value goes first (cards inside
or behind the shell in every view cost nothing), until the mean card layers over the views (all fragments, no depth
test, per covered pixel) reach `cards.layers[lod]`. So the cards kept are the ones that cover the shell's gaps and the
silhouette, not an even share per clump. A card's cost is scaled by its COLOR_0 brightness (the baked occlusion, not
the leaf palette) relative to the median, to the power `cards.dark_bias`, so deep dark cards go before lit ones.
Real sky gaps: shell triangles in front of or behind an eye-level gap of the installed crown (no card, no bark, at least
`cards.carve_px` connected pixels) are removed first, so the sky still shows through them.
Rewrites l<lod>_keep / l<lod>_reason (3 = removed by this step) and l<lod>_faces (carved) in shell.npz. Usage: select_cards.py <id>"""
import heapq, io, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, glb

tid = sys.argv[1]
spec = common.load(tid); W = spec['work']; C = spec['cards']
m = glb.read(os.path.join(W, 'installed.glb'))
shp = os.path.join(W, 'shell.npz'); sh = dict(np.load(shp)); cards = np.load(os.path.join(W, 'cards.npz'))
RES = C.get('select_res', 160)
UNDER = C.get('under_weight', 0.6)           # views from below the crown (close by, looking up)
VIEWS = [(az, el, wt) for el, wt in ((-70, UNDER), (-40, UNDER), (0, 1.0), (20, 1.0), (45, 0.7), (75, 0.3))
         for az in range(0, 360, 45)]


def per_lod(v, lod):
    return v[lod] if isinstance(v, (list, tuple)) else v


def view_matrix(az, el):
    """Rows: screen x, screen y, toward the viewer (glTF: y up)."""
    a, e = math.radians(az), math.radians(el)
    fwd = np.array([math.cos(e) * math.sin(a), math.sin(e), math.cos(e) * math.cos(a)])   # toward the viewer
    right = np.cross([0.0, 1.0, 0.0], fwd); right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    return np.stack([right, up, fwd])


def tri_pixels(t, frame):
    """Pixels inside triangle t (3, 3) in view space: (iy, ix, w0, w1, w2, z)."""
    x0, y0, scale = frame
    px = (t[:, 0] - x0) * scale; py = (y0 - t[:, 1]) * scale
    xmin, xmax = int(max(math.floor(px.min()), 0)), int(min(math.ceil(px.max()), RES - 1))
    ymin, ymax = int(max(math.floor(py.min()), 0)), int(min(math.ceil(py.max()), RES - 1))
    if xmin > xmax or ymin > ymax:
        return None
    gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
    d = (py[1] - py[2]) * (px[0] - px[2]) + (px[2] - px[1]) * (py[0] - py[2])
    if abs(d) < 1e-9:
        return None
    w0 = ((py[1] - py[2]) * (gx - px[2]) + (px[2] - px[1]) * (gy - py[2])) / d
    w1 = ((py[2] - py[0]) * (gx - px[2]) + (px[0] - px[2]) * (gy - py[2])) / d
    w2 = 1 - w0 - w1
    ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    if not ins.any():
        return None
    w0, w1, w2 = w0[ins], w1[ins], w2[ins]
    return (gy[ins].astype(int), gx[ins].astype(int), w0, w1, w2, w0 * t[0, 2] + w1 * t[1, 2] + w2 * t[2, 2])


def alpha_of(prim):
    mat = m.doc['materials'][prim['material']]
    tex = m.doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    return np.asarray(Image.open(io.BytesIO(m.images[tex])).convert('RGBA'))[..., 3] >= 128


chain = m.mesh_chain()
allpos = np.concatenate([m.get(p['attributes']['POSITION']) for p in m.doc['meshes'][chain[0]]['primitives']])
centre = 0.5 * (allpos.min(0) + allpos.max(0))
size = float(np.linalg.norm(allpos.max(0) - allpos.min(0))) * 1.02
frame = (-size / 2, size / 2, RES / size)
for lod in (0, 1, 2):
    target = per_lod(C.get('layers', [2.8, 2.7, 2.0]), lod)
    if target is None:
        continue
    mesh = chain[lod]
    prim = (m.primitive(mesh, 'LeavesFar') if lod == 2 else None) or m.primitive(mesh, 'Leaves')
    pos = m.get(prim['attributes']['POSITION']).astype(np.float64) - centre
    grow = per_lod(C['grow'], lod)            # compose.py grows the kept cards about their centres the same way
    if grow != 1.0:
        q = pos.reshape(-1, 4, 3); c = q.mean(1, keepdims=True); pos = (c + (q - c) * grow).reshape(-1, 3)
    uv = m.get(prim['attributes']['TEXCOORD_0']).astype(np.float64)
    idx = m.get(prim['indices']).reshape(-1, 3)
    alpha = alpha_of(prim); th, tw = alpha.shape
    ncard = len(pos) // 4
    keep0 = np.ones(ncard, bool)                 # every card is a candidate (cards inside the shell cost nothing)
    bark = [(m.get(p['attributes']['POSITION']).astype(np.float64) - centre, m.get(p['indices']).reshape(-1, 3))
            for p in m.doc['meshes'][mesh]['primitives']
            if m.doc['materials'][p['material']].get('alphaMode') != 'MASK']
    sverts = sh[f'l{lod}_verts'] - centre; sfaces = sh[f'l{lod}_faces']
    npx = RES * RES; nv = len(VIEWS)
    bark_depth = np.full(nv * npx, -np.inf)
    shell_tri = []                               # per view: (pixel ids, z, triangle ids) of every shell fragment
    frag_pid = [[] for _ in range(ncard)]; frag_z = [[] for _ in range(ncard)]
    for vi, (az, el, wt) in enumerate(VIEWS):
        R = view_matrix(az, el)
        bd = np.full((RES, RES), -np.inf)
        for P, F in bark:
            v = P @ R.T
            for t in v[F]:
                r = tri_pixels(t, frame)
                if r is not None:
                    np.maximum.at(bd, (r[0], r[1]), r[5])
        bark_depth[vi * npx:(vi + 1) * npx] = bd.reshape(-1)
        v = sverts @ R.T; sp, sz, st = [], [], []
        for ti, t in enumerate(v[sfaces]):
            r = tri_pixels(t, frame)
            if r is not None:
                sp.append(vi * npx + r[0] * RES + r[1]); sz.append(r[5]); st.append(np.full(len(r[0]), ti))
        shell_tri.append((np.concatenate(sp), np.concatenate(sz), np.concatenate(st)) if sp else
                         (np.zeros(0, int), np.zeros(0), np.zeros(0, int)))
        v = pos @ R.T
        for k in range(ncard):
            for tri in idx[2 * k:2 * k + 2]:
                r = tri_pixels(v[tri], frame)
                if r is None:
                    continue
                iy, ix, w0, w1, w2, z = r
                u_ = w0 * uv[tri[0], 0] + w1 * uv[tri[1], 0] + w2 * uv[tri[2], 0]
                v_ = w0 * uv[tri[0], 1] + w1 * uv[tri[1], 1] + w2 * uv[tri[2], 1]
                ok = alpha[np.clip((np.mod(v_, 1) * th).astype(int), 0, th - 1),
                           np.clip((np.mod(u_, 1) * tw).astype(int), 0, tw - 1)]
                frag_pid[k].append(vi * npx + iy[ok] * RES + ix[ok]); frag_z[k].append(z[ok])
    frag_pid = [np.concatenate(p) if p else np.zeros(0, int) for p in frag_pid]
    frag_z = [np.concatenate(z) if z else np.zeros(0) for z in frag_z]
    vweight = np.repeat([wt for _, _, wt in VIEWS], npx).astype(float)
    acount = np.zeros(nv * npx, np.int32)
    for k in range(ncard):
        np.add.at(acount, np.unique(frag_pid[k]), 1)
    # real sky gaps: eye-level view pixels that the installed crown leaves open (no card, no bark) but the shell
    # covers. Shell triangles over a gap region of at least `carve_px` pixels are removed (front and back), so the
    # sky still shows through; smaller gaps stay filled.
    carve_px = per_lod(C.get('carve_px', 12), lod)
    removed_tris = set()
    if carve_px:
        from scipy import ndimage
        for vi, (az, el, wt) in enumerate(VIEWS):
            if abs(el) > 20:
                continue
            sp, sz, st = shell_tri[vi]
            covered_shell = np.zeros(nv * npx, bool); covered_shell[sp] = True
            sl = slice(vi * npx, (vi + 1) * npx)
            gap = (acount[sl] == 0) & ~np.isfinite(bark_depth[sl]) & covered_shell[sl]
            lab, n = ndimage.label(gap.reshape(RES, RES))
            if not n:
                continue
            sizes = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
            big = np.isin(lab.reshape(-1), 1 + np.where(sizes >= carve_px)[0])
            gp = np.where(big)[0] + vi * npx
            removed_tris.update(np.unique(st[np.isin(sp, gp)]).tolist())
    keep_tri = np.ones(len(sfaces), bool); keep_tri[list(removed_tris)] = False
    # open underside (`shell.open_bottom[lod]`: faces whose normal points further down than this go): from under
    # the tree one sees the kept cards and the sky through the crown, not a flat ceiling
    ob = per_lod(spec['shell'].get('open_bottom', [-0.35, -0.35, None]), lod)
    if ob is not None:
        fv = sverts[sfaces]; fn = np.cross(fv[:, 1] - fv[:, 0], fv[:, 2] - fv[:, 0])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        fc = fv.mean(1); rh = fc[:, [0, 2]] / np.maximum(np.linalg.norm(fc[:, [0, 2]], axis=1, keepdims=True), 1e-9)
        inward = (fn[:, 0] * rh[:, 0] + fn[:, 2] * rh[:, 1] < -0.2) & (fc[:, 1] < np.median(fc[:, 1]))
        down = (fn[:, 1] < ob) | inward          # and lower faces turned toward the trunk (seen from under it)
        keep_tri &= ~down
        print(f'OPEN LOD{lod} removed {int(down.sum())} downward shell triangles (normal y < {ob})')
    shell_depth = np.full(nv * npx, -np.inf)
    for sp, sz, st in shell_tri:
        ok = keep_tri[st]
        np.maximum.at(shell_depth, sp[ok], sz[ok])
    depth = np.maximum(shell_depth, bark_depth)
    front_pix = [np.unique(frag_pid[k][frag_z[k] > depth[frag_pid[k]] + 1e-4]) for k in range(ncard)]
    all_pix = [np.unique(frag_pid[k]) for k in range(ncard)]
    inside_sil = np.isfinite(depth)
    shell_front = np.isfinite(shell_depth) & (shell_depth >= bark_depth)
    sh[f'l{lod}_faces'] = sfaces[keep_tri]
    if removed_tris:
        print(f'CARVE LOD{lod} removed {len(removed_tris)} of {len(sfaces)} shell triangles over sky gaps')
    count = np.zeros(nv * npx, np.int32)
    for k in range(ncard):
        np.add.at(count, front_pix[k], 1)
    count0 = count.copy()
    fringe = per_lod(C.get('fringe', 2.0), lod); depth_bonus = per_lod(C.get('depth', 0.15), lod)
    pw = vweight * np.where(inside_sil, 1.0, fringe)

    # dark cards (deep in the crown, their baked occlusion low) go before lit ones of equal value: once the cards
    # around them are gone they would show as black patches in front of the shell
    lum = cards[f'c{lod}_vc'].mean(1)          # COLOR_0 only: the occlusion, not the leaf palette
    bright = (lum / np.median(lum)) ** per_lod(C.get('dark_bias', 0.5), lod)

    def cost(k):
        c = count[front_pix[k]]
        return float((pw[front_pix[k]] * ((c == 1) * 1.0 + (c == 2) * depth_bonus)).sum()) * bright[k]

    alive = keep0.copy()
    heap = [(cost(k), k) for k in np.where(alive)[0]]; heapq.heapify(heap)
    frags = float(acount.sum()); covered = int((acount > 0).sum())
    removed = 0
    while heap and frags / max(covered, 1) > target:
        c, k = heapq.heappop(heap)
        cn = cost(k)
        if heap and cn > heap[0][0] + 1e-9:
            heapq.heappush(heap, (cn, k)); continue
        alive[k] = False; removed += 1
        np.subtract.at(count, front_pix[k], 1)
        np.subtract.at(acount, all_pix[k], 1)
        frags -= len(all_pix[k]); covered -= int((acount[all_pix[k]] == 0).sum())
    reason = sh[f'l{lod}_reason'].copy()
    reason[alive] = 0; reason[~alive & (reason == 0)] = 3
    sh[f'l{lod}_keep'] = alive; sh[f'l{lod}_reason'] = reason
    crown = (count0 > 0) | shell_front           # crown pixels (cards or the shell in front of the bark)
    print(f'SELECT LOD{lod} cards {ncard} -> {int(alive.sum())}; view layers {frags / max(covered, 1):.2f} '
          f'(target {target}); shell seen (no card in front) {((count0 == 0) & crown).sum() / crown.sum() * 100:.1f}'
          f' -> {((count == 0) & crown).sum() / crown.sum() * 100:.1f} % of the crown, fringe pixels lost '
          f'{((count == 0) & (count0 > 0) & ~inside_sil).sum() / max(((count0 > 0) & ~inside_sil).sum(), 1) * 100:.1f} %')
np.savez(shp, **sh)
