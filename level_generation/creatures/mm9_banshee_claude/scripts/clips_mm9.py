"""Write the role clips onto the exported body GLB from the original MM9 clips (MM9 rig reuse, humanoid NPCs).

Usage: python3 clips_mm9.py <body.glb> <out.glb> <roles.json> [report.json]

roles.json: {"root": "<pelvis joint>", "sources": {"<id>": "<mm9 glb with the clips>"},
             "roles": {"<Role>": {"src": "<id>", "clips": ["<mm9 clip>", ...], "loop": bool, "ease": "both|in|none",
                                  "rate": 1.0, "trim": [t0, t1]}, ...},
             "standing": "<Role used as the ease target>", "dead_from": "<death role>"}

The body was fitted with the MM9 joints TRANSLATED only, so every joint's rest rotation is the MM9 one and the MM9
clips' local rotations are copied unchanged. Translations keep our rest plus the clip's offset from the source rest,
scaled by our/source pelvis height (only the pelvis and a few helper bones really move).
- LithTech keys (linear, often sparse) are resampled as monotone cubic (PCHIP) curves through the same key poses
  (quaternions sign-continuous, renormalised) at FPS.
- Several clips in one role are stitched; the jump at each join is blended out over BLEND seconds.
- Loops: the seam residual is spread over the clip. One-shots ease from and back to the Standing first pose
  (EASE seconds; deaths only ease in). Dead = the death's last pose held one second.
"""
import json, sys
import numpy as np
from pygltflib import GLTF2, Animation, AnimationChannel, AnimationChannelTarget, AnimationSampler, Accessor, \
    BufferView

FPS = 30
FROZEN = ('\0',)
BLEND = 0.25
EASE_IN = 0.15
EASE_OUT = 0.2


def pchip(t, y, tq):
    """Monotone cubic interpolation per column (Fritsch-Carlson)."""
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    if len(t) == 1:
        return np.repeat(y[:1], len(tq), 0)
    h = np.diff(t)
    d = np.diff(y, axis=0) / h[:, None]
    m = np.zeros_like(y)
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, len(t) - 1):
        a, b = d[k - 1], d[k]
        w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
        with np.errstate(divide='ignore', invalid='ignore'):
            mk = (w1 + w2) / (w1 / a + w2 / b)
        mk[(a * b) <= 0] = 0
        m[k] = np.nan_to_num(mk)
    tq = np.clip(tq, t[0], t[-1])
    idx = np.clip(np.searchsorted(t, tq, side='right') - 1, 0, len(t) - 2)
    hh = h[idx][:, None]
    s = ((tq - t[idx]) / h[idx])[:, None]
    h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
    h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
    return h00 * y[idx] + h10 * hh * m[idx] + h01 * y[idx + 1] + h11 * hh * m[idx + 1]


def read(g, acc_index):
    acc = g.accessors[acc_index]
    bv = g.bufferViews[acc.bufferView]
    data = g.binary_blob()
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[acc.type]
    off = (bv.byteOffset or 0) + (acc.byteOffset or 0)
    stride = bv.byteStride or 4 * n
    raw = np.frombuffer(data, dtype=np.uint8, count=stride * (acc.count - 1) + 4 * n, offset=off)
    out = np.lib.stride_tricks.as_strided(raw.view(np.float32), shape=(acc.count, n), strides=(stride, 4)) \
        if stride != 4 * n else raw.view(np.float32).reshape(acc.count, n)
    return np.array(out, dtype=np.float64)


def quat_continuous(q):
    q = q.copy()
    for k in range(1, len(q)):
        if np.dot(q[k], q[k - 1]) < 0:
            q[k] = -q[k]
    return q


def qnorm(q):
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def slerp(a, b, w):
    if np.dot(a, b) < 0:
        b = -b
    d = np.clip(np.dot(a, b), -1, 1)
    th = np.arccos(d)
    if th < 1e-6:
        return qnorm(a * (1 - w) + b * w)
    return (np.sin((1 - w) * th) * a + np.sin(w * th) * b) / np.sin(th)


def source_clips(path):
    g = GLTF2().load(path)
    names = [n.name for n in g.nodes]
    rest = {n.name: (np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float))
            for n in g.nodes}
    clips = {}
    for a in g.animations:
        ch = {}
        dur = 0
        for c in a.channels:
            s = a.samplers[c.sampler]
            t = read(g, s.input)[:, 0]
            v = read(g, s.output)
            ch[(names[c.target.node], c.target.path)] = (t, v)
            dur = max(dur, t[-1])
        clips[a.name.lower()] = (ch, dur)
    return g, rest, clips


def world_z(g, name):
    """Rest world height (glTF +Y) of a node."""
    byname = {n.name: i for i, n in enumerate(g.nodes)}
    parent = {}
    for i, n in enumerate(g.nodes):
        for c in n.children or []:
            parent[c] = i

    def mat(n):
        t = np.array(n.translation or [0, 0, 0], float)
        x, y, z, w = n.rotation or [0, 0, 0, 1]
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        s = np.array(n.scale or [1, 1, 1], float)
        M = np.eye(4)
        M[:3, :3] = R * s
        M[:3, 3] = t
        return M
    i = byname[name]
    M = np.eye(4)
    while i is not None:
        M = mat(g.nodes[i]) @ M
        i = parent.get(i)
    return M[1, 3]


def qmul(a, b):
    x1, y1, z1, w1 = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    x2, y2, z2, w2 = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], -1)


def qpow(q, k):
    """rotation q scaled to k times its angle (shortest arc)"""
    q = np.where(q[..., 3:4] < 0, -q, q)
    ang = 2 * np.arccos(np.clip(q[..., 3], -1, 1))
    s = np.sin(ang / 2)
    ax = np.where(s[..., None] > 1e-8, q[..., :3] / np.maximum(s, 1e-8)[..., None], 0)
    return np.concatenate([ax * np.sin(ang * k / 2)[..., None], np.cos(ang * k / 2)[..., None]], -1)


qmul_v = qmul
FINGER_ALIAS = {}


def thin(t, v, eps):
    """MM9's exported keys hold (a key repeats the previous value, the next jumps twice as far), a stop-start at 15-20 Hz that
    PCHIP keeps as zero slope (hand acceleration 127 mm/f2 in walk). Repeated keys go, so the curve runs through the moving keys."""
    if not THIN or len(t) < 3:
        return t, v
    keep = [0]
    for i in range(1, len(t) - 1):
        if np.abs(v[i] - v[keep[-1]]).max() > eps:
            keep.append(i)
    keep.append(len(t) - 1)
    return t[keep], v[keep]


THIN = False
ROOT_LIFT = {}


def sample_clip(ch, dur, joints, times, ours_rest, src_rest, k, root):
    """{joint: (T[n,3], Q[n,4])} at times (seconds within the source clip).
    FINGER_ALIAS (roles json "finger_alias", 2026-10-30 five-finger hands): {new joint: [MM9 mitten joint, k, mode]}:
    "copy" = the mitten joint's local rotation (the new finger bone has the mitten bone's rest frame), "delta" = our
    rest times k x the mitten joint's rotation away from its rest (distal joints)."""
    out = {}
    for j in joints:
        t_rest, q_rest = ours_rest[j]
        if (j, 'rotation') in ch:
            t, v = ch[(j, 'rotation')]
            t, v = thin(t, quat_continuous(v), 2e-4)
            Q = qnorm(pchip(t, v, times))
        else:
            Q = np.repeat(q_rest[None], len(times), 0)
        if (j, 'translation') in ch and j in src_rest and not j.startswith(FROZEN):
            t, v = ch[(j, 'translation')]
            t, v = thin(t, v, 1e-4)
            off = pchip(t, v, times) - src_rest[j][0]
            if j in ROOT_LIFT:          # the clips stand on the floor, the bind is centred on the pelvis (our armature carries that lift)
                off = off - np.array([0.0, ROOT_LIFT[j], 0.0])
            # only the pelvis and the scene root carry real motion; other offsets are the source's own proportions
            T = t_rest + (off * k if j in root else np.where(np.abs(off) > 0.004, off * k, 0.0))
        else:
            T = np.repeat(t_rest[None], len(times), 0)
        out[j] = (T, Q)
    for j, (sj, kk, mode) in FINGER_ALIAS.items():
        if j not in out or (sj, 'rotation') not in ch:
            continue
        t, v = ch[(sj, 'rotation')]
        Qs = qnorm(pchip(t, quat_continuous(v), times))
        qr_src = src_rest[sj][1] if sj in src_rest else ours_rest[sj][1]
        d = qmul(np.repeat((qr_src * np.array([-1, -1, -1, 1]))[None], len(times), 0), Qs)   # rest^-1 * q
        if mode == 'copy':
            Q = qmul(np.repeat(ours_rest[sj][1][None], len(times), 0), qpow(d, kk))
        else:
            Q = qmul(np.repeat(ours_rest[j][1][None], len(times), 0), qpow(d, kk))
        out[j] = (out[j][0], qnorm(Q))
    return out


def main():
    body_path, out_path, roles_path = sys.argv[1:4]
    report_path = sys.argv[4] if len(sys.argv) > 4 else None
    spec = json.load(open(roles_path))
    FINGER_ALIAS.update(spec.get('finger_alias', {}))
    global FROZEN
    FROZEN = tuple(spec.get('freeze_translation', ['\0']))  # Ghost: MM9's arm joints slide up to 5.5 cm along the limb in its clips (rigid pieces hide it); a continuous sleeve tears
    global THIN
    THIN = spec.get('thin_keys', False)
    ROOT_LIFT.update(spec.get('root_lift', {}))
    g = GLTF2().load(body_path)
    skin = g.skins[0]
    joint_nodes = list(skin.joints)
    joints = [g.nodes[i].name for i in joint_nodes]
    node_of = {g.nodes[i].name: i for i in joint_nodes}
    ours_rest = {g.nodes[i].name: (np.array(g.nodes[i].translation or [0, 0, 0], float),
                                   np.array(g.nodes[i].rotation or [0, 0, 0, 1], float)) for i in joint_nodes}
    root = set(spec.get('root_nodes', [spec['root']]))
    # model-space y = 0 is the actor's floor: the MM9 bind is centred on the pelvis, so the scene root carries the lift
    # (its rest and every key; the inverse bind matrices are unchanged, so the skinned mesh moves with it)
    lift = 0.0
    if spec.get('lift_to_floor'):
        lift = -min(g.accessors[p.attributes.POSITION].min[1] for m in g.meshes for p in m.primitives)
        top = spec.get('top_joint', 'Scene Root')
        t, q = ours_rest[top]
        ours_rest[top] = (t + np.array([0, lift, 0]), q)
        tn = g.nodes[node_of[top]]
        tn.translation = [float(x) for x in ours_rest[top][0]]
    sources = {}
    for sid, path in spec['sources'].items():
        sg, srest, sclips = source_clips(path)
        # leg length ratio from the pelvis height above the lowest toe joint
        foot = spec['foot']
        k = (world_z(g, spec['root']) - world_z(g, foot)) / (world_z(sg, spec['root']) - world_z(sg, foot))
        sources[sid] = (srest, sclips, k)
    rep = {}
    built = {}
    for role, r in spec['roles'].items():
        srest, sclips, k = sources[r['src']]
        segs = []
        for name in r['clips']:
            ch, dur = sclips[name.lower()]
            t0, t1 = r.get('trim', [0, dur]) if len(r['clips']) == 1 else (0, dur)
            rate = r.get('rate', 1.0)
            n = max(2, int(round((t1 - t0) / rate * FPS)) + 1)
            times = np.linspace(t0, t1, n)
            segs.append(sample_clip(ch, dur, joints, times, ours_rest, srest, k, root))
        # stitch
        pose = {j: (segs[0][j][0].copy(), segs[0][j][1].copy()) for j in joints}
        for seg in segs[1:]:
            nb = int(BLEND * FPS)
            for j in joints:
                T0, Q0 = pose[j]
                T1, Q1 = seg[j]
                dT = T0[-1] - T1[0]
                q0, q1 = Q0[-1], Q1[0]
                w = np.ones(len(T1))
                w[:nb] = 1 - (np.arange(nb) / nb)
                w[nb:] = 0
                w = w * w * (3 - 2 * w)
                T1 = T1 + dT[None] * w[:, None]
                # rotate each frame by the residual (q0 * q1^-1) faded out
                def qmul(a, b):
                    x1, y1, z1, w1 = a
                    x2, y2, z2, w2 = b
                    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
                inv = q1 * np.array([-1, -1, -1, 1])
                res = qmul(q0, inv)
                Qn = np.array([qmul(slerp(np.array([0, 0, 0, 1.0]), res, w[i]), seg[j][1][i]) for i in range(len(T1))])
                pose[j] = (np.concatenate([T0, T1[1:]]), np.concatenate([Q0, Qn[1:]]))
        n = len(pose[joints[0]][0])
        # loops: spread the seam residual
        if r.get('loop'):
            for j in joints:
                T, Q = pose[j]
                Q = quat_continuous(Q)
                ramp = np.linspace(0, 1, n)[:, None]
                T = T - (T[-1] - T[0])[None] * ramp
                Q = qnorm(Q - (Q[-1] - Q[0])[None] * ramp)
                pose[j] = (T, Q)
        built[role] = pose
        rep[role] = {'frames': n, 'seconds': round((n - 1) / FPS, 3), 'sources': r['clips'], 'k': round(k, 3)}
    # the jaw: MM9 opens it up to 94 deg with two hinges at the throat, through a black flap. Ours is one hinge at the TMJ on real cheeks: Xjawpiv + Xjaw fold into Xjaw, opening saturating at jaw_fold[0] = [A, B] (A tanh(open / B)), closing limited (the teeth meet)
    if spec.get('jaw_fold'):
        ko, kc = spec['jaw_fold']
        for role, pose in built.items():
            Tp, Qp = pose['Xjawpiv']; Tj, Qj = pose['Xjaw']
            q = qmul_v(qnorm(Qp), qnorm(Qj))
            th = 2 * np.arctan2(q[:, 0], q[:, 3])                # about glTF x
            th = np.where(th < 0, -ko[0] * np.tanh(-th / ko[1]), kc * np.tanh(th / kc))
            pose['Xjaw'] = (np.repeat(ours_rest['Xjaw'][0][None], len(th), 0), np.stack([np.sin(th / 2), 0 * th, 0 * th, np.cos(th / 2)], 1))
            pose['Xjawpiv'] = (np.repeat(ours_rest['Xjawpiv'][0][None], len(th), 0), np.repeat(ours_rest['Xjawpiv'][1][None], len(th), 0))
    # optional damping: chosen joints (a dress's skirt chains) keep only part of a clip's motion, the rest is the
    # standing first pose (MM9's spinning wince throws the skirt bones far beyond what an HD dress can stretch)
    st = built[spec['standing']]
    for role, r in spec['roles'].items():
        d = r.get('damp')
        if not d:
            continue
        pose = built[role]
        for j in joints:
            if any(j.startswith(p) for p in d['prefixes']):
                T, Q = pose[j]
                Ts, Qs = st[j][0][0], st[j][1][0]
                a = d['amount']
                pose[j] = (T * (1 - a) + Ts * a, np.array([slerp(q, Qs, a) for q in Q]))
        rep[role]['damp'] = d
    # ease one-shots from/to the standing first pose
    for role, r in spec['roles'].items():
        ease = r.get('ease', 'none')
        if ease == 'none' or r.get('loop'):
            continue
        pose = built[role]
        n = len(pose[joints[0]][0])
        ni, no = int(EASE_IN * FPS), int(EASE_OUT * FPS)
        for j in joints:
            T, Q = pose[j]
            Ts, Qs = st[j][0][0], st[j][1][0]
            for i in range(n):
                w = 0.0
                if i < ni:
                    w = 1 - i / ni
                if ease == 'both' and i > n - 1 - no:
                    w = max(w, (i - (n - 1 - no)) / no)
                if w > 0:
                    w = w * w * (3 - 2 * w)
                    T[i] = T[i] * (1 - w) + Ts * w
                    Q[i] = slerp(Q[i], Qs, w)
            pose[j] = (T, Q)
    if spec.get('dead_from'):
        d = built[spec['dead_from']]
        built['Dead'] = {j: (np.repeat(d[j][0][-1:], 2, 0), np.repeat(d[j][1][-1:], 2, 0)) for j in joints}
        rep['Dead'] = {'frames': 2, 'seconds': 1.0}
    # write the animations
    blob = bytearray(g.binary_blob() or b'')
    g.animations = []

    def add(arr, typ, minmax=False):
        nonlocal blob
        arr = np.ascontiguousarray(arr, dtype=np.float32)
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob += arr.tobytes()
        g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=arr.nbytes))
        acc = Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ)
        if minmax:
            acc.min = [float(arr.min())]
            acc.max = [float(arr.max())]
        g.accessors.append(acc)
        return len(g.accessors) - 1
    for role, pose in built.items():
        n = len(pose[joints[0]][0])
        times = np.arange(n, dtype=np.float64) / FPS if role != 'Dead' else np.array([0.0, 1.0])
        ti = add(times[:, None], 'SCALAR', True)
        anim = Animation(name=role, channels=[], samplers=[])
        for j in joints:
            T, Q = pose[j]
            for path, val in (('translation', T), ('rotation', qnorm(Q))):
                vi = add(val, 'VEC3' if path == 'translation' else 'VEC4')
                anim.samplers.append(AnimationSampler(input=ti, output=vi, interpolation='LINEAR'))
                anim.channels.append(AnimationChannel(sampler=len(anim.samplers) - 1,
                                                      target=AnimationChannelTarget(node=node_of[j], path=path)))
        g.animations.append(anim)
    g.buffers[0].byteLength = len(blob)
    g.set_binary_blob(bytes(blob))
    g.save(out_path)
    if report_path:
        json.dump(rep, open(report_path, 'w'), indent=1)
    rep['lift_to_floor'] = round(lift, 4)
    print('CLIPS ' + json.dumps({k: (v['seconds'] if isinstance(v, dict) else v) for k, v in rep.items()}))


if __name__ == '__main__':
    main()
