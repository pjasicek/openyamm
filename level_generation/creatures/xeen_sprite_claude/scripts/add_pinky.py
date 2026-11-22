"""Smart Topology gave both hands a thumb and only three fingers (two draws, v1 and v2; the HD masters show five).
Adds a pinky per hand: a closed copy of the outermost finger (the finger above its web, found by connectivity at the
depth where the fingers separate), shortened to PINKY_LEN, spread outward by SPREAD degrees about the palm normal,
moved one finger spacing outward (OFFSET x the spacing between the middle and outer finger bases) and sunk BASE_SINK m
into the palm so its base is hidden inside the hand. Piece 0 (skin), point attribute 'extra_finger' = 1, orig_co = its
new position (Meshy weights reach it through the nearest-vertex transfer; finger weights come from finger_weights.py).
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, json, math
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
import numpy as np
from mathutils import Vector, Matrix
src, out = sys.argv[sys.argv.index('--') + 1:]
E_ = lambda k, d: float(os.environ.get(k, d))
PINKY_LEN, SPREAD, OFFSET, BASE_SINK = E_('PINKY_LEN', 0.80), E_('SPREAD', 14.0), E_('OFFSET', 0.8), E_('BASE_SINK', 0.02)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; me = ob.data
J = json.load(open('work/joints_final.json'))['joints']
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
E = np.array([tuple(e.vertices) for e in me.edges])


def components(mask):
    idx = np.where(mask)[0]; s = set(idx.tolist()); adj = {i: [] for i in idx}
    for a, b in E:
        if a in s and b in s:
            adj[a].append(b); adj[b].append(a)
    seen, comps = set(), []
    for i in idx:
        if i in seen:
            continue
        st, c = [i], []
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); c.append(x); st.extend(adj[x])
        comps.append(np.array(c))
    return comps


new_parts = []
for side in ('R', 'L'):
    wr = np.array(J[f'{side}_Hand']); fa = np.array(J[f'{side}_Forearm']); d = (wr - fa) / np.linalg.norm(wr - fa)
    hand = (pv == 0) & (np.linalg.norm(co - wr, axis=1) < 0.3) & ((co - wr) @ d > -0.01) & (np.sign(co[:, 0]) == np.sign(wr[0]))
    dep = (co - wr) @ d
    # depth with the most separate digits (thumb + 3 fingers)
    best = max(np.arange(0.08, 0.17, 0.0025), key=lambda c: (len([x for x in components(hand & (dep > c)) if len(x) >= 10]), -c))
    comps = [x for x in components(hand & (dep > best)) if len(x) >= 10]
    tips = [c[np.argmax(dep[c])] for c in comps]
    # thumb = the digit whose tip lies farthest from the other tips' mean direction; outer finger = farthest from thumb
    cen = [co[c].mean(0) for c in comps]
    lat = [np.linalg.norm(co[t] - np.mean([co[u] for u in tips if u != t], axis=0)) for t in tips]
    ti = int(np.argmax(lat))
    others = [i for i in range(len(comps)) if i != ti]
    oi = max(others, key=lambda i: np.linalg.norm(cen[i] - cen[ti]))
    mi = min([i for i in others if i != oi], key=lambda i: np.linalg.norm(cen[i] - cen[oi]))   # the neighbour
    # the whole outer finger: hand vertices round its axis (line fit through the separated part) from EXTEND m behind
    # the web split to the tip, within RADIUS_K x the separated part's radius (the web hides the proximal phalanx)
    sep = co[comps[oi]]; c0 = sep.mean(0); ax0 = np.linalg.svd(sep - c0)[2][0]
    ax0 = ax0 if ax0 @ d > 0 else -ax0
    rad = float(np.median(np.linalg.norm((sep - c0) - np.outer((sep - c0) @ ax0, ax0), axis=1)))
    tt = (co - c0) @ ax0; rr = np.linalg.norm((co - c0) - np.outer(tt, ax0), axis=1)
    t_sep = float(((sep - c0) @ ax0).min())
    finger = np.where(hand & (tt > t_sep - E_('EXTEND', 0.03)) & (rr < E_('RADIUS_K', 1.35) * rad))[0]
    print('PINKY', side, 'split depth cm', round(best * 100, 1), 'digits', len(comps), 'outer finger radius cm', round(rad * 100, 2))
    # procedural pinky: continue the finger fan. Each separated finger gives a web point (lowest ring of its separated
    # part) and a direction (web -> tip). The pinky turns from the outer finger's direction by SPREAD deg about the
    # fan's own axis (middle -> outer), its root = the outer finger's knuckle (web moved KNUCKLE m back) + OFFSET x
    # the middle -> outer web spacing, sunk BASE_SINK m into the palm; length PINKY_LEN x the outer finger's.
    def web_dir(c):
        P = co[c]; dp = (P - wr) @ d
        tip = P[np.argmax(dp)]; web = P[dp < dp.min() + 0.005].mean(0)
        v = tip - web; return web, tip, v / np.linalg.norm(v)
    web_o, tip_o, dir_o = web_dir(comps[oi]); web_m, tip_m, dir_m = web_dir(comps[mi])
    fan = np.cross(dir_m, dir_o); fan /= np.linalg.norm(fan)
    axis = np.array(Matrix.Rotation(math.radians(SPREAD), 3, Vector(fan))) @ dir_o
    knuckle = web_o - dir_o * E_('KNUCKLE', 0.015)
    full = float(np.linalg.norm(tip_o - knuckle))
    lateral = web_o - web_m; lat_u = lateral / np.linalg.norm(lateral)
    # the palm's outer edge beside the outer finger's knuckle: the hand skin (not the fingers) in a depth band round the
    # knuckle, farthest along the lateral direction; the pinky root sits EDGE_IN x its radius inside that edge, its tip
    # follows the fan (axis) for PINKY_LEN x the outer finger's length
    kd = (knuckle - wr) @ d
    band = hand & (np.abs(dep - (kd - 0.01)) < 0.012)
    edge = co[band][np.argmax((co[band] - knuckle) @ lat_u)]
    mid_thick = co[band][np.abs((co[band] - edge) @ lat_u) < 0.012].mean(0)     # centre of the palm's thickness there
    root0 = mid_thick - lat_u * rad * E_('EDGE_IN', 1.0)
    root = root0 - axis * BASE_SINK
    L = full * PINKY_LEN + BASE_SINK + max(0.0, float((knuckle - root0) @ axis))
    normal = np.cross(axis, lateral); normal /= np.linalg.norm(normal)
    u = np.cross(axis, normal); u /= np.linalg.norm(u)
    NS, rings = 8, []
    prof = [(0.0, 0.95), (0.25, 0.92), (0.5, 0.86), (0.75, 0.8), (0.9, 0.74), (0.96, 0.55), (0.99, 0.3)]
    bm = bmesh.new()
    for sfrac, k in prof:
        c = root + axis * L * sfrac; r = rad * k
        # slightly flattened toward the palm normal, like the other fingers
        rings.append([bm.verts.new(Vector(c + r * (math.cos(2 * math.pi * j / NS) * u + 0.85 * math.sin(2 * math.pi * j / NS) * normal))) for j in range(NS)])
    tipv = bm.verts.new(Vector(root + axis * L)); basev = bm.verts.new(Vector(root - axis * rad * 0.3))
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for j in range(NS):
            j1 = (j + 1) % NS
            bm.faces.new((a_[j], a_[j1], b_[j1])); bm.faces.new((a_[j], b_[j1], b_[j]))
    for j in range(NS):
        j1 = (j + 1) % NS
        bm.faces.new((rings[-1][j], rings[-1][j1], tipv)); bm.faces.new((rings[0][j1], rings[0][j], basev))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    pm = bpy.data.meshes.new(f'Pinky_{side}'); bm.to_mesh(pm); bm.free()
    po = bpy.data.objects.new(f'Pinky_{side}', pm); bpy.context.scene.collection.objects.link(po)
    n = len(pm.vertices)
    pm.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [0] * n)
    pm.attributes.new('extra_finger', 'INT', 'POINT').data.foreach_set('value', [1] * n)
    nc = np.array([tuple(v.co) for v in pm.vertices])
    pm.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', nc.ravel())
    print('PINKY', side, 'verts', n, 'tris', sum(len(p.vertices) - 2 for p in pm.polygons), 'length cm',
          round(float(np.ptp(nc @ axis)) * 100, 1), 'outer finger cm', round(full * 100, 1), 'root', np.round(root, 3).tolist(), 'axis', np.round(axis, 2).tolist(),
          'spacing cm', round(float(np.linalg.norm(lateral)) * 100, 1))
    new_parts.append(po)
if 'extra_finger' not in me.attributes:
    me.attributes.new('extra_finger', 'INT', 'POINT')
for o in bpy.data.objects:
    o.select_set(o is ob or o in new_parts)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
print('TRIS', sum(len(p.vertices) - 2 for p in ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
