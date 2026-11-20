"""MM9 dog clips -> OpenYAMM role clips (Blender module; from mm9_wolf_claude/scripts/clips_mm9.py).

The MM9 clips are played unchanged except:
- sparse linear keys (LithTech keyframes) are resampled as smooth monotone cubic (PCHIP) curves through the SAME key
  poses (no overshoot, holds stay holds), baked at FPS;
- loops get their seam closed: the residual between the last and first key is distributed over the clip;
- stitched roles join their clips with each jump blended out over BLEND_SECONDS;
- Dead = the last Death pose held one second.

Values are pose-bone basis channels (rotation_quaternion, location, scale) of the imported MM9 armature.
"""
import math
import bpy
from mathutils import Matrix, Quaternion, Vector
import clips_keys as K

FPS = 30
BLEND_SECONDS = 0.3

# ---------------- role clips of the MM9 dog: MM9 has no Hit or Death for it (it is an NPC animal); see clips_keys.py
def dog_hit(arm, sources):
    b = K.pose_of(sources['stand'], 0.0)
    s = 'Xheadpiv'
    keys = [(0.0, []),
            (0.1, [('XCENTER', 'loc', (0, 0.03, -0.035)), ('XbackA', 'rot', (1, 0, 0), -5), (s, 'rot', (1, 0, 0), -14)]),
            (0.22, [('XCENTER', 'loc', (0, 0.022, -0.025)), ('XbackA', 'rot', (1, 0, 0), -3), (s, 'rot', (1, 0, 0), -9)]),
            (0.5, [])]
    return K.keyed(arm, b, keys)


def dog_death(arm, sources):
    b = K.pose_of(sources['stand'], 0.0)
    drop = [('Xflegpiv', 'rot', (0, 1, 0), -24), ('Xblegpiv', 'rot', (0, 1, 0), -24),
            ('Xflegpiv01', 'rot', (0, 1, 0), 10), ('Xblegpiv01', 'rot', (0, 1, 0), 10)]
    neck = [('XneckC', 'rot', (0, 1, 0), 14), ('XneckB', 'rot', (0, 1, 0), 16), ('Xheadpiv', 'rot', (0, 1, 0), 12)]
    keys = [(0.0, []),
            (0.22, [('XCENTER', 'loc', (0, 0.02, -0.09)), ('XneckC', 'rot', (1, 0, 0), 10), ('Xheadpiv', 'rot', (1, 0, 0), 12)]),
            (0.62, [('XCENTER', 'loc', (0, 0.03, -0.30)), ('XCENTER', 'rot', (0, 1, 0), 62)] + drop[:0] + neck[:1]),
            (0.95, [('XCENTER', 'loc', (0, 0.03, -0.37)), ('XCENTER', 'rot', (0, 1, 0), 88)] + drop + neck),
            (1.2, [('XCENTER', 'loc', (0, 0.03, -0.37)), ('XCENTER', 'rot', (0, 1, 0), 90)] + drop + neck)]
    return K.keyed(arm, b, keys)


KEYED = {'dog_hit': dog_hit, 'dog_death': dog_death}
DOG = {
    'Standing': (['stand'], True),
    'Walking': (['walk'], True),
    'Running': (['run'], True),
    'Fidget': (['fidget1'], False),
    'AttackMelee': (['Bark'], False),
    'Hit': (['keys:dog_hit'], False),
    'Death': (['keys:dog_death'], False),
}
ROLES = DOG


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags
               for fc in cb.fcurves]
    return fcs


def read_keys(action, fps_import):
    """{bone: {'t': [s], 'q': [Quaternion], 'l': [Vector], 's': [Vector]}} at the action's own key times."""
    curves = {}
    times = set()
    for fc in fcurves(action):
        if not fc.data_path.startswith('pose.bones["'):
            continue
        bone = fc.data_path.split('"')[1]
        channel = fc.data_path.rsplit('.', 1)[1]
        curves.setdefault(bone, {}).setdefault(channel, {})[fc.array_index] = fc
        for kp in fc.keyframe_points:
            times.add(round(kp.co.x, 4))
    times = sorted(times)
    out = {}
    for bone, ch in curves.items():
        rec = {'t': [f / fps_import for f in times], 'q': [], 'l': [], 's': []}
        for f in times:
            q = ch.get('rotation_quaternion')
            rec['q'].append(Quaternion([q[i].evaluate(f) for i in range(4)]) if q else Quaternion())
            l = ch.get('location')
            rec['l'].append(Vector([l[i].evaluate(f) for i in range(3)]) if l else Vector())
            s = ch.get('scale')
            rec['s'].append(Vector([s[i].evaluate(f) for i in range(3)]) if s else Vector((1, 1, 1)))
        off = REST_OFFSET.get(bone)
        if off is not None:
            inv = off.inverted()
            for k in range(len(rec['t'])):
                l_, q_, s_ = (inv @ Matrix.LocRotScale(rec['l'][k], rec['q'][k], rec['s'][k])).decompose()
                rec['l'][k], rec['q'][k], rec['s'][k] = l_, q_, s_
        out[bone] = rec
    # a bone the clip does not key sits at the MM9 rest: under a moved rest it needs the converted identity
    for bone, off in REST_OFFSET.items():
        if bone not in out:
            ts = [times[0] / fps_import, times[-1] / fps_import] if times else [0.0, 0.0]
            l_, q_, s_ = off.inverted().decompose()
            out[bone] = {'t': ts, 'q': [q_.copy(), q_.copy()], 'l': [l_.copy(), l_.copy()], 's': [s_.copy(), s_.copy()]}
    return out


# rig_body.py REST_FROM_POSE: bone -> old basis matrix of the reference pose that became the rest pose; set by
# build_export.py from the armature's 'rest_offset_json'. MM9 keys are converted to the new rest on read.
REST_OFFSET = {}


def align_hemisphere(qs):
    out = [qs[0].copy()]
    for q in qs[1:]:
        q = q.copy()
        if out[-1].dot(q) < 0:
            q.negate()
        out.append(q)
    return out


def pchip_slopes(t, y):
    n = len(t)
    h = [t[i + 1] - t[i] for i in range(n - 1)]
    d = [(y[i + 1] - y[i]) / h[i] if h[i] > 0 else 0.0 for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    if n >= 2:
        m[0] = d[0] if n == 2 else end_slope(h[0], h[1], d[0], d[1])
        m[-1] = d[-1] if n == 2 else end_slope(h[-1], h[-2], d[-1], d[-2])
    return m


def end_slope(h0, h1, d0, d1):
    s = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if s * d0 <= 0:
        return 0.0
    if d0 * d1 <= 0 and abs(s) > abs(3 * d0):
        return 3 * d0
    return s


def hermite(t, y, m, x):
    if x <= t[0]:
        return y[0]
    if x >= t[-1]:
        return y[-1]
    i = max(k for k in range(len(t) - 1) if t[k] <= x)
    h = t[i + 1] - t[i]
    if h <= 0:
        return y[i]
    s = (x - t[i]) / h
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1
    h10 = s ** 3 - 2 * s ** 2 + s
    h01 = -2 * s ** 3 + 3 * s ** 2
    h11 = s ** 3 - s ** 2
    return h00 * y[i] + h10 * h * m[i] + h01 * y[i + 1] + h11 * h * m[i + 1]


def smooth_channel(t, values, loop, samples):
    """values: list of tuples; returns list of tuples at sample times (PCHIP, periodic when loop)."""
    dims = len(values[0])
    tt = list(t)
    vv = list(values)
    if loop and len(t) >= 4:
        period = t[-1] - t[0]
        # last key == first key after the seam fix; extend by two keys each side
        tt = [t[-3] - period, t[-2] - period] + tt + [t[1] + period, t[2] + period]
        vv = [values[-3], values[-2]] + vv + [values[1], values[2]]
    out = []
    comps = []
    for c in range(dims):
        y = [v[c] for v in vv]
        comps.append((y, pchip_slopes(tt, y)))
    for x in samples:
        out.append(tuple(hermite(tt, y, m, x) for y, m in comps))
    return out


def close_seam(rec):
    """Distribute the last-to-first residual over the loop so the last key equals the first."""
    t0, t1 = rec['t'][0], rec['t'][-1]
    q_first, q_last = rec['q'][0], rec['q'][-1]
    d = q_first @ q_last.inverted()
    pop = math.degrees(d.angle) if d.angle <= math.pi else math.degrees(2 * math.pi - d.angle)
    dl = rec['l'][0] - rec['l'][-1]
    for k, t in enumerate(rec['t']):
        a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
        rec['q'][k] = Quaternion().slerp(d, a) @ rec['q'][k]
        rec['l'][k] = rec['l'][k] + dl * a
    return pop


def crossfade(rec, w):
    """Loop by cross-fade: the first w seconds blend from the clip's tail (t + T - w) into its own start, giving a
    seamless cycle of T - w (dense samples at FPS; last sample == first)."""
    t = [x - rec['t'][0] for x in rec['t']]
    T = t[-1]
    L = T - w
    n = int(round(L * FPS))
    ts = [L * k / n for k in range(n + 1)]
    qs = align_hemisphere(rec['q'])
    qa = smooth_channel(t, [tuple(q) for q in qs], False, ts)
    qb = smooth_channel(t, [tuple(q) for q in qs], False, [x + L for x in ts])
    la = smooth_channel(t, [tuple(v) for v in rec['l']], False, ts)
    lb = smooth_channel(t, [tuple(v) for v in rec['l']], False, [x + L for x in ts])
    sa = smooth_channel(t, [tuple(v) for v in rec['s']], False, ts)
    out = {'t': ts, 'q': [], 'l': [], 's': []}
    for k, x in enumerate(ts):
        a = min(1.0, x / w)
        a = a * a * (3 - 2 * a)
        if x >= w:
            q, l = Quaternion(qa[k]).normalized(), Vector(la[k])
        else:
            q = Quaternion(qb[k]).normalized().slerp(Quaternion(qa[k]).normalized(), a)
            l = Vector(lb[k]).lerp(Vector(la[k]), a)
        out['q'].append(q); out['l'].append(l); out['s'].append(Vector(sa[k]))
    out['q'][-1] = out['q'][0].copy(); out['l'][-1] = out['l'][0].copy()
    return out, L


def stitch(recs_list, durations):
    """Concatenate per-bone key records; at each join the incoming clip starts at the outgoing end pose and its
    difference eases out over BLEND_SECONDS (smoothstep). Returns (record, joins{bone: [deg per join]})."""
    out = {}
    jumps = {}
    for bone in recs_list[0]:
        rec = {'t': [], 'q': [], 'l': [], 's': []}
        offset = 0.0
        jumps[bone] = []
        for ci, recs in enumerate(recs_list):
            src = recs[bone]
            if ci == 0:
                d, dl = Quaternion(), Vector()
            else:
                d = rec['q'][-1] @ src['q'][0].inverted()
                dl = rec['l'][-1] - src['l'][0]
                ang = d.angle if d.angle <= math.pi else 2 * math.pi - d.angle
                jumps[bone].append(math.degrees(ang))
            for k, t in enumerate(src['t']):
                if ci > 0 and k == 0:
                    continue
                local = t - src['t'][0]
                a = 1.0 - min(1.0, local / BLEND_SECONDS) if ci > 0 else 0.0
                a = a * a * (3 - 2 * a)
                rec['t'].append(offset + local)
                rec['q'].append(Quaternion().slerp(d, a) @ src['q'][k])
                rec['l'].append(src['l'][k] + dl * a)
                rec['s'].append(src['s'][k])
            offset += durations[ci]
        out[bone] = rec
    return out, jumps


def write_action(arm, name, rec_by_bone, duration, loop, rate=1.0):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    n = int(round(duration / rate * FPS))
    samples_out = [k / FPS for k in range(n + 1)]
    # a loop keeps its whole cycle in whole frames (the dog's 0.25 s run in 8 frames), so its last frame is its first
    samples_src = [duration * k / n for k in range(n + 1)] if loop else [x * rate for x in samples_out]
    arm.animation_data_create()
    arm.animation_data.action = act
    for bone, rec in rec_by_bone.items():
        pb = arm.pose.bones.get(bone)
        if pb is None:
            continue
        pb.rotation_mode = 'QUATERNION'
        qs = align_hemisphere(rec['q'])
        t0 = rec['t'][0]
        tt = [t - t0 for t in rec['t']]
        qv = smooth_channel(tt, [tuple(q) for q in qs], loop, samples_src)
        lv = smooth_channel(tt, [tuple(l) for l in rec['l']], loop, samples_src)
        sv = smooth_channel(tt, [tuple(s) for s in rec['s']], loop, samples_src)
        prev = None
        for k in range(n + 1):
            q = Quaternion(qv[k]).normalized()
            if prev is not None and prev.dot(q) < 0:
                q.negate()
            prev = q
            pb.rotation_quaternion = q
            pb.location = lv[k]
            pb.scale = sv[k]
            pb.keyframe_insert('rotation_quaternion', frame=k)
            pb.keyframe_insert('location', frame=k)
            pb.keyframe_insert('scale', frame=k)
    for fc in fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    return act, n


def hold_action(arm, name, rec_by_bone, seconds=1.0):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    n = int(round(seconds * FPS))
    for bone, rec in rec_by_bone.items():
        pb = arm.pose.bones.get(bone)
        if pb is None:
            continue
        for f in (0, n):
            pb.rotation_quaternion = rec['q'][-1]
            pb.location = rec['l'][-1]
            pb.scale = rec['s'][-1]
            pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('scale', frame=f)
    return act


def build_role_clips(arm, fps_import, roles=None):
    """Create the role actions on arm from its imported MM9 actions. Returns a report."""
    sources = {}
    durations = {}
    for act in list(bpy.data.actions):
        sources[act.name] = read_keys(act, fps_import)
        any_bone = next(iter(sources[act.name].values()))
        durations[act.name] = any_bone['t'][-1] - any_bone['t'][0]
    report = {'fps': FPS, 'clips': {}}
    role_recs = {}
    for role, (names, loop) in (roles or ROLES).items():
        if names[0].startswith('keys:'):
            rec, duration = KEYED[names[0][5:]](arm, sources)
            info = {'sources': names, 'loop': False}
            if '_stitch' in rec:
                recs = [sources[x] if isinstance(x, str) else x for x in rec['_stitch']]
                durs = rec['_durations']
                common = set(recs[0]) & set(recs[1])
                rec, _ = stitch([{b: r[b] for b in common} for r in recs], durs)
                duration = sum(durs)
            act, n = write_action(arm, role, rec, duration, False)
            info['duration'] = n / FPS
            info['frames'] = n
            report['clips'][role] = info
            role_recs[role] = rec
            continue
        if isinstance(loop, str) and loop.startswith('xfade:'):
            w = float(loop.split(':')[1])
            rec, duration = {}, None
            for b, r in sources[names[0]].items():
                rec[b], duration = crossfade(r, w)
            info = {'sources': names, 'loop': True, 'crossfade_seconds': w,
                    'source_keys': len(next(iter(sources[names[0]].values()))['t'])}
            loop = True
            act, n = write_action(arm, role, rec, duration, loop)
            info['duration'] = n / FPS
            info['frames'] = n
            report['clips'][role] = info
            role_recs[role] = rec
            continue
        if len(names) == 1:
            rec = {b: {k: list(v) for k, v in r.items()} for b, r in sources[names[0]].items()}
            pops = {}
            if loop:
                for bone, r in rec.items():
                    pops[bone] = close_seam(r)
            duration = durations[names[0]]
            info = {'sources': names, 'loop': loop, 'source_keys': len(next(iter(rec.values()))['t'])}
            if loop:
                worst = max(pops, key=pops.get)
                info['seam_pop_before_deg'] = round(pops[worst], 2)
                info['seam_pop_bone'] = worst
        else:
            rec, jumps = stitch([sources[n] for n in names], [durations[n] for n in names])
            duration = sum(durations[n] for n in names)
            info = {'sources': names, 'loop': False,
                    'join_jump_deg': [round(max(j[i] for j in jumps.values()), 2) for i in range(len(names) - 1)]}
        act, n = write_action(arm, role, rec, duration, loop)
        info['duration'] = n / FPS
        info['frames'] = n
        report['clips'][role] = info
        role_recs[role] = rec
    report['_recs'] = role_recs
    return report


def seam_after(arm, action, fps):
    """Max bone rotation difference between the first and last frame of an action (degrees)."""
    worst = 0.0
    curves = {}
    for fc in fcurves(action):
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    f0, f1 = action.frame_range
    for comps in curves.values():
        q0 = Quaternion([comps[i].evaluate(f0) for i in range(4)])
        q1 = Quaternion([comps[i].evaluate(f1) for i in range(4)])
        d = q0.rotation_difference(q1)
        a = d.angle if d.angle <= math.pi else 2 * math.pi - d.angle
        worst = max(worst, math.degrees(a))
    return worst
