"""G5: fingers from the mesh by connectivity (gob2 rule). Per hand: the vertices beyond the wrist along the hand's
direction (wrist -> fingertip) are cut at increasing depth; the first depth at which FINGERS separate pieces exist gives
the digits. The thumb is the piece that separates first (the smaller piece of the earliest two-piece cut; it is short and
ends before the fingers part); the four fingers are the pieces of the first deeper cut with four pieces besides it,
ordered from the thumb outward. Each piece's centreline runs from its base (lowest-depth ring centre) to its
tip (farthest vertex from the base, the claw tip), its base extended toward the hand by WEB x its length (the webbing
hides part of the proximal phalanx). Joints at 0, .46, .77 of the chain, tip at 1.
Writes work/fingers_fit.json {side: {thumb|index|middle|ring|pinky: [[x,y,z] x4], 'vertices': {...}}} and
review/fingers_<side>.png."""
import bpy, bmesh, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
FINGERS = 5
WEB = 0.15
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step3.blend'))
ob = bpy.data.objects['Queen']
me = ob.data
co = np.array([tuple(v.co) for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges])
J = json.loads((P / 'work' / 'joints.json').read_text())['joints']
rep = json.loads((P / 'work' / 'joints.json').read_text())['report']


def components(ids):
    ids = set(ids)
    adj = {}
    for a, b in E:
        if a in ids and b in ids:
            adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for v in ids:
        if v in seen:
            continue
        comp, st = [], [v]
        seen.add(v)
        while st:
            x = st.pop(); comp.append(x)
            for w in adj.get(x, []):
                if w not in seen:
                    seen.add(w); st.append(w)
        out.append(comp)
    return [c for c in out if len(c) >= 6]


out = {}
for side, sg in (('L', 1), ('R', -1)):
    wr = np.array(J[f'{side}_Hand']); tip = np.array(rep[f'{side}_arm']['fingertip'])
    fd = (tip - wr) / np.linalg.norm(tip - wr)
    rel = co - wr
    depth = rel @ fd
    hand = np.where((depth > 0.0) & (np.linalg.norm(rel, axis=1) < 0.45) & (co[:, 0] * sg > 0.25))[0]
    # The thumb separates first and is short (it ends before the fingers part); the four fingers part together later.
    first_split = None
    fingers = None
    for d in np.arange(0.01, 0.35, 0.004):
        comps = components(hand[depth[hand] > d])
        if first_split is None and len(comps) >= 2:
            first_split = (d, min(comps, key=len))
        if first_split is not None:
            rest = [c for c in comps if not set(c) & set(first_split[1])]
            if len(rest) >= FINGERS - 1:
                fingers = (d, sorted(rest, key=len, reverse=True)[:FINGERS - 1])
                break
    if fingers is None:
        raise SystemExit(f'{side}: no depth separates {FINGERS - 1} fingers after the thumb')
    d_split, comps = fingers
    comps = [first_split[1]] + comps
    t_index = 0
    chains = []
    for i, c in enumerate(comps):
        pc = co[c]
        base_ids = np.array(c)[np.argsort(depth[c])[:max(6, len(c) // 12)]]
        base = co[base_ids].mean(0)
        far = pc[np.argmax(np.linalg.norm(pc - base, axis=1))]
        length = float(np.linalg.norm(far - base))
        knuckle = base - (far - base) / length * (WEB * length)
        # follow the piece: centres of slabs along the base->tip direction (the claws curve)
        ax = (far - base) / length
        t = (pc - base) @ ax
        pts = [knuckle]
        for f in (0.2, 0.45, 0.7, 0.9):
            sel = np.abs(t - f * length) < 0.06 * length
            pts.append(pc[sel].mean(0) if sel.any() else base + ax * f * length)
        pts.append(far)
        poly = np.array(pts)
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))]
        joints = [np.array([np.interp(a * arc[-1], arc, poly[:, k]) for k in range(3)]) for a in (0, 0.46, 0.77, 1.0)]
        chains.append({'i': i, 'joints': joints, 'base': base, 'verts': [int(x) for x in c]})
    thumb = chains[t_index]
    others = [c for c in chains if c is not thumb]
    others.sort(key=lambda c: np.linalg.norm(c['base'] - thumb['base']))
    names = ['index', 'middle', 'ring', 'pinky']
    out[side] = {'split_depth': float(d_split), 'thumb_split_depth': float(first_split[0]),
                 'thumb': [j.tolist() for j in thumb['joints']]}
    out[side]['vertices'] = {'thumb': thumb['verts']}
    for n, c in zip(names, others):
        out[side][n] = [j.tolist() for j in c['joints']]
        out[side]['vertices'][n] = c['verts']
    print('FINGERS', side, 'split depth', round(d_split, 3), 'thumb split', round(first_split[0], 3),
          {n: round(float(np.linalg.norm(np.array(out[side][n][-1]) - np.array(out[side][n][0]))), 3)
           for n in ['thumb'] + names})
(P / 'work' / 'fingers_fit.json').write_text(json.dumps(out))
# review: finger pieces coloured on the hands
col = me.color_attributes.new('fing', 'BYTE_COLOR', 'POINT')
palette = {'thumb': (1, 0.2, 0.2), 'index': (1, 0.7, 0.1), 'middle': (0.2, 0.8, 0.2), 'ring': (0.2, 0.5, 1),
           'pinky': (0.7, 0.3, 1)}
for i in range(len(me.vertices)):
    col.data[i].color = (0.8, 0.8, 0.8, 1)
for side in out:
    for n, ids in out[side]['vertices'].items():
        for i in ids:
            col.data[i].color = (*palette[n], 1)
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'VERTEX'
for side in ('L', 'R'):
    c = np.array(J[f'{side}_Hand'])
    common.render_views(str(P / 'review' / f'fingers_{side}'), float(c[2]) - 0.12, 0.45, views=('front', 'left'),
                        resolution=(500, 500), target=(float(c[0]), float(c[1])))
