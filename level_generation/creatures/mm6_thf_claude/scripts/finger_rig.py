"""Mitten finger rig for the thief's relaxed open hands (work/rig_v1.blend in place, after cloak_rig.py).

Meshy's rig has no finger chains and the Smart Topology hands came back relaxed and open (review/handv_sheet.png),
so the daggers cannot be held without a curl. Per hand: the hand frame from the hand shell (principal axis a from the
wrist to the fingertips, palm normal n toward the body midline, knuckle axis k = a x n), the four fingers as one
mitten chain Fing<S>1-3 (knuckle line at KNUCKLE of the hand length, segments 0.45/0.30/0.25 of the finger length)
and the thumb as Thumb<S>1-2 (front-side vertices before the knuckle line that stand out of the palm). Weights:
palm 100 % Hand; fingers by s along a with linear blends across each joint (+-6 mm); thumb by distance from its
base. Curling a chain is a rotation about the bone's local X (= k). Writes scene['thf_hands'] (frames, bones).
Saves a classification render review/hand_classes_*.png."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data; scene = bpy.context.scene
arm.animation_data.action = None
for b in arm.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
hi = PARTS.index('Hand')
KNUCKLE = float(os.environ.get('KNUCKLE', 0.52))
THUMB_OUT = float(os.environ.get('THUMB_OUT', 0.004))
info = {}
cls = {}
for side, sx, S in (('Left', 1, 'L'), ('Right', -1, 'R')):
    vid = sorted({v for p in me.polygons if part[p.index] == hi for v in p.vertices
                  if (mesh.matrix_world @ me.vertices[v].co).x * sx > 0})
    P = np.array([tuple(mesh.matrix_world @ me.vertices[i].co) for i in vid])
    W = np.array(arm.matrix_world @ arm.data.bones[side + 'Hand'].head_local)
    c = P.mean(0)
    u, s_, vt = np.linalg.svd(P - c); a = vt[0]
    if a[2] > 0:
        a = -a                                           # toward the fingertips (down in the rest pose)
    n = np.array([-sx, 0.0, 0.0]); n = n - a * n.dot(a); n /= np.linalg.norm(n)
    k = np.cross(a, n); k /= np.linalg.norm(k)
    if k[1] > 0:
        k = -k                                           # k forward (thumb side, -Y)
    s = (P - c) @ a; s0, s1 = s.min(), s.max(); L = s1 - s0
    sk = s0 + KNUCKLE * L
    fwd = (P - c) @ k; side_n = (P - c) @ n
    # palm thickness centre line: median n-offset of the palm band
    band = (s > sk - 0.02) & (s < sk)
    n_mid = float(np.median(side_n[band])); k_front = float(np.percentile(fwd[band], 95))
    idx = {v: j for j, v in enumerate(vid)}
    adj = {j: set() for j in range(len(vid))}
    for e in me.edges:
        x, y = e.vertices
        if x in idx and y in idx:
            adj[idx[x]].add(idx[y]); adj[idx[y]].add(idx[x])
    # digits: connected components beyond the knuckle line; the most forward one is the thumb
    dig = s > sk + 0.012
    lab = -np.ones(len(vid), int); ncomp = 0
    for j in np.where(dig)[0]:
        if lab[j] >= 0:
            continue
        st = [j]; lab[j] = ncomp
        while st:
            q = st.pop()
            for m in adj[q]:
                if dig[m] and lab[m] < 0:
                    lab[m] = ncomp; st.append(m)
        ncomp += 1
    comps = [np.where(lab == q)[0] for q in range(ncomp)]
    comps = [cmp for cmp in comps if len(cmp) >= 4]
    tcomp = max(comps, key=lambda cmp: fwd[cmp].mean())
    thumb = np.zeros(len(vid), bool); thumb[tcomp] = True
    fmin = float(np.percentile(fwd[tcomp], 10))
    for _ in range(4):                                   # grow back a little toward its base (not into the palm)
        grow = thumb.copy()
        for j in np.where(thumb)[0]:
            for m in adj[j]:
                if not thumb[m] and fwd[m] > fmin - THUMB_OUT and s[m] > sk - 0.03 and not (lab[m] >= 0 and not thumb[m] and lab[m] != lab[tcomp[0]]):
                    grow[m] = True
        thumb = grow
    print('DIGITS', S, 'components', [len(cmp) for cmp in comps], 'thumb', int(thumb.sum()))
    finger = (s > sk - 0.006) & ~thumb
    tb = P[thumb]
    tbase = tb[np.argmin(((tb - c) @ a))] if len(tb) else c
    ttip = tb[np.argmax(np.linalg.norm(tb - tbase, axis=1))] if len(tb) else c
    info[S] = {'side': side, 'a': a.tolist(), 'n': n.tolist(), 'k': k.tolist(), 'c': c.tolist(), 's0': float(s0),
               's1': float(s1), 'sk': float(sk), 'n_mid': n_mid, 'thumb_base': tbase.tolist(),
               'thumb_tip': ttip.tolist(), 'counts': [int(finger.sum()), int(thumb.sum()), int((~finger & ~thumb).sum())]}
    for j, v in enumerate(vid):
        cls[v] = (S, 'F' if finger[j] else ('T' if thumb[j] else 'P'), float(s[j]))
    print('HAND', S, 'L %.3f' % L, 'counts finger/thumb/palm', info[S]['counts'])

bpy.context.view_layer.objects.active = arm
for x in bpy.data.objects:
    x.select_set(x == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; inv = arm.matrix_world.inverted()
for S, h in info.items():
    side = h['side']; a = Vector(h['a']); n = Vector(h['n']); k = Vector(h['k']); c = Vector(h['c'])
    base = c + a * h['sk'] + n * h['n_mid']
    Lf = h['s1'] - h['sk']
    pts = [base]
    for f in (0.45, 0.30, 0.25):
        pts.append(pts[-1] + a * (Lf * f))
    h['fing'] = []
    parent = eb[side + 'Hand']
    for j in range(3):
        b = eb.get(f'Fing{S}{j + 1}') or eb.new(f'Fing{S}{j + 1}')
        b.head = inv @ pts[j]; b.tail = inv @ pts[j + 1]; b.parent = parent; b.use_connect = j > 0
        b.align_roll(inv.to_3x3() @ (-n)); b.use_deform = True
        parent = b; h['fing'].append([list(pts[j]), list(pts[j + 1])])
    tb = Vector(h['thumb_base']); tt = Vector(h['thumb_tip']); tm = tb.lerp(tt, 0.5)
    parent = eb[side + 'Hand']; h['thumb'] = []
    for j, (p0, p1) in enumerate(((tb, tm), (tm, tt))):
        b = eb.get(f'Thumb{S}{j + 1}') or eb.new(f'Thumb{S}{j + 1}')
        b.head = inv @ p0; b.tail = inv @ p1; b.parent = parent; b.use_connect = j > 0
        b.align_roll(inv.to_3x3() @ (-n)); b.use_deform = True
        parent = b; h['thumb'].append([list(p0), list(p1)])
bpy.ops.object.mode_set(mode='OBJECT')
for S in info:
    for nme in [f'Fing{S}{j}' for j in (1, 2, 3)] + [f'Thumb{S}{j}' for j in (1, 2)]:
        if nme not in mesh.vertex_groups:
            mesh.vertex_groups.new(name=nme)


def seg_weights(s, cuts, names, blend=0.006):
    """Bone weights by position s along a chain with joints at `cuts` (len(names) - 1 joints)."""
    j = sum(1 for x in cuts if s > x)
    w = {names[j]: 1.0}
    for q, x in enumerate(cuts):
        if abs(s - x) < blend:
            t = 0.5 + 0.5 * (s - x) / blend                  # 0 before the joint, 1 after
            return {names[q]: 1 - t, names[q + 1]: t}
    return w


for v, (S, kind, s) in cls.items():
    h = info[S]; side = h['side']
    if kind == 'P':
        w = {side + 'Hand': 1.0}
    elif kind == 'F':
        Lf = h['s1'] - h['sk']
        cuts = [h['sk'], h['sk'] + 0.45 * Lf, h['sk'] + 0.75 * Lf]
        w = seg_weights(s, cuts, [side + 'Hand', f'Fing{S}1', f'Fing{S}2', f'Fing{S}3'])
    else:
        p = mesh.matrix_world @ me.vertices[v].co
        tb, tt = Vector(h['thumb_base']), Vector(h['thumb_tip'])
        t = (p - tb).dot((tt - tb).normalized()) / (tt - tb).length
        w = seg_weights(t, [0.22, 0.6], [side + 'Hand', f'Thumb{S}1', f'Thumb{S}2'], blend=0.2)   # soft web
    for g in me.vertices[v].groups:
        mesh.vertex_groups[g.group].remove([v])
    for nme, x in w.items():
        if x > 1e-4:
            mesh.vertex_groups[nme].add([v], x, 'REPLACE')
scene['thf_hands'] = json.dumps(info)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
# classification render (vertex colours: palm grey, fingers by segment, thumb red)
col = me.color_attributes.new('cls', 'FLOAT_COLOR', 'POINT')
C = {'P': (0.6, 0.6, 0.6, 1), 'T': (0.9, 0.2, 0.2, 1)}
for v in range(len(me.vertices)):
    col.data[v].color = (0.3, 0.3, 0.3, 1)
for v, (S, kind, s) in cls.items():
    if kind == 'F':
        h = info[S]; t = (s - h['sk']) / (h['s1'] - h['sk'])
        col.data[v].color = (0.2, 0.5 + 0.5 * t, 0.9 - 0.6 * t, 1)
    else:
        col.data[v].color = C[kind]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); pl = bm.faces.layers.int['part']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[pl] != hi], context='FACES'); bm.to_mesh(me); bm.free()
sc = scene; common.workbench_clay(sc); sc.display.shading.color_type = 'VERTEX'
for S, h in info.items():
    c = Vector(h['c']); n = Vector(h['n']); k = Vector(h['k'])
    for nm, d in (('palm', -n), ('thumb', k), ('back', n)):
        loc = c - d * 1.0
        cam = common.ortho_camera('c', loc, (0, 0, 0), 0.16)
        cam.rotation_euler = (d.to_track_quat('-Z', 'Y')).to_euler()
        sc.camera = cam; sc.render.resolution_x = sc.render.resolution_y = 360
        sc.render.filepath = os.path.join(common.REVIEW, f'hand_classes_{S}_{nm}.png'); bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
