"""MM9 clips -> OpenYAMM role clips (Blender module; from mm9_lobber_claude/scripts/clips_mm9.py, role tables for the
Jellyspore (JELLY) and the Sea Monster (SEA) added; a role may give a playback rate as a third item).

The MM9 clips are played unchanged except:
- sparse linear keys (LithTech keyframes) are resampled as smooth monotone cubic (PCHIP) curves through the SAME key
  poses (no overshoot, holds stay holds), baked at FPS;
- loops get their seam closed: the residual between the last and first key is distributed over the clip;
- stitched roles join their clips with each jump blended out over BLEND_SECONDS;
- Running (pod) = the MM9 run; Dead = the last Death pose held one second.
The role table is per body (LOBBER, POD); the Lobber's death wilt is added by build_export.py after DieAir1.

Values are pose-bone basis channels (rotation_quaternion, location, scale) of the imported MM9 armature.
"""
import math
import bpy
from mathutils import Quaternion, Vector

FPS = 30
BLEND_SECONDS = 0.3

# role -> (source clips, loop)
LOBBER = {
    'Standing': (['StandAir'], True),
    'Fidget': (['FidgetAir1'], False),
    'AttackRanged': (['Rattack1'], False),
    'Cast': (['LaunchPod'], False),
    'Hit': (['winceAir2'], False),
    'Death': (['DieAir1'], False),
}
POD = {
    'Standing': (['stand'], True),
    'Walking': (['walk'], True),
    'Running': (['run'], True),
    'Fidget': (['fidget'], False),
    'AttackMelee': (['Hattack1'], False),
    'AttackRanged': (['Rattack1'], False),
    'Hit': (['wince1'], False),
    'Death': (['die1'], False),
}
# Jellyspore (JELLYSPORE.abc has no death clip: build_export.py builds Death from wincewater2 + a collapse)
JELLY = {
    'Standing': (['standwater'], True),
    'Walking': (['swim'], True),
    'Running': (['swim'], True, 36 / 26),  # swim x1.38: 26 whole frames at 30 fps, so the loop closes
    'Fidget': (['fidgetwater'], False),
    'AttackMelee': (['hattackwater1'], False),
    'AttackRanged': (['Hattackwater2'], False),
    'Hit': (['wincewater1'], False),
    'Death': (['wincewater2'], False),
}
# Sea Monster
SEA = {
    'Standing': (['standwater'], True),
    'Walking': (['swim'], True),
    'Fidget': (['fidgetwater1'], False),
    'AttackMelee': (['Hattackwater1'], False),
    'AttackRanged': (['Hattackwater2'], False),
    'Hit': (['wincewater1'], False),
    'Death': (['diewater2'], False),
}
ROLES = LOBBER


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
        out[bone] = rec
    return out


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
    samples_src = [x * rate for x in samples_out]
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
    for role, spec in (roles or ROLES).items():
        names, loop = spec[0], spec[1]
        rate = spec[2] if len(spec) > 2 else 1.0
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
        act, n = write_action(arm, role, rec, duration, loop, rate=rate)
        if rate != 1.0:
            info['rate'] = rate
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
