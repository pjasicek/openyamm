"""MM9 fish clips -> OpenYAMM role clips (Blender module, on clips_mm9.py: PCHIP resampling at 30 fps, loop seams).

FISH.abc has one clip, `swim` (0.7 s, 6 keys); fish.scr only ever Walks (and asks for a `Jump` clip FISH.abc lacks).
Every role is built from the swim keys; all changes are made on the keys (amplitude = slerp/lerp of each key toward the
bind pose, an added roll on XCENTER), never per frame:
  Walking  swim as is (0.7 s, seam closed)                 Running  swim x1.5 (0.467 s, 14 whole frames)
  Standing swim x0.6, amplitude 0.5 (1.167 s): idle finning Fidget   two beats, amplitude 0.5 -> 1.2 -> 0.5 (1.4 s)
  Hit      swim x2.1 (one beat in 0.333 s), amplitude 1.35, a 14 degree roll in and out on XCENTER
  Death    four keyed beats whose amplitude decays 1 -> 0 while XCENTER rolls 90 degrees onto the fish's side (eased),
           and the pectoral fins fold 14 degrees flat against the flanks, then 0.5 s still; all played x1.4 (2.37 s);
           the floor pass lowers the corpse onto the floor
  Dead     the last Death pose held one second.
"""
import math
import bpy
from mathutils import Quaternion, Vector, Matrix
import clips_mm9 as C

FPS = C.FPS


def scaled(rec, amp):
    """One bone's key record with every key moved toward the bind pose (identity) by amp (amp > 1 overshoots)."""
    out = {'t': list(rec['t']), 'q': [], 'l': [], 's': list(rec['s'])}
    for q, l in zip(rec['q'], rec['l']):
        q = q.copy()
        if q.w < 0:
            q.negate()
        ax, ang = q.to_axis_angle()
        out['q'].append(Quaternion(ax, ang * amp))
        out['l'].append(l * amp)
    return out


def repeat(rec, cycles, amps=None, rolls=None, roll_axis=None, hold=0.0):
    """cycles x the (seam-closed) loop; amps/rolls: per output key (callables of normalised time 0..1)."""
    T = rec['t'][-1] - rec['t'][0]
    out = {'t': [], 'q': [], 'l': [], 's': []}
    keys = len(rec['t'])
    total = T * cycles + hold
    for c in range(cycles):
        for k in range(keys):
            if c > 0 and k == 0:
                continue
            t = c * T + rec['t'][k] - rec['t'][0]
            a = amps(t / total) if amps else 1.0
            q, l = rec['q'][k].copy(), rec['l'][k]
            if q.w < 0:
                q.negate()
            ax, ang = q.to_axis_angle()
            q = Quaternion(ax, ang * a)
            if rolls:
                q = Quaternion(roll_axis, math.radians(rolls(t / total))) @ q
            out['t'].append(t); out['q'].append(q); out['l'].append(l * a); out['s'].append(rec['s'][k])
    if hold > 0:
        for dt in (hold * 0.5, hold):
            t = T * cycles + dt
            q, l = out['q'][-1].copy(), out['l'][-1].copy()
            out['t'].append(t); out['q'].append(q); out['l'].append(l); out['s'].append(out['s'][-1])
    return out


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def build(arm, fps_import):
    act = bpy.data.actions['swim']
    src = C.read_keys(act, fps_import)
    pops = {}
    for b, r in src.items():
        pops[b] = C.close_seam(r)
    T = next(iter(src.values()))['t'][-1]
    R = arm.data.bones['XCENTER'].matrix_local.to_3x3()
    roll_axis = (R.inverted() @ Vector((0, 1, 0))).normalized()   # the body's long axis in XCENTER's rest frame
    rep = {'fps': FPS, 'swim_seconds': T, 'seam_pop_before_deg': round(max(pops.values()), 2), 'clips': {}}

    def emit(role, rec_by_bone, duration, loop, rate=1.0, note=''):
        a, n = C.write_action(arm, role, rec_by_bone, duration, loop, rate=rate)
        rep['clips'][role] = {'duration': n / FPS, 'frames': n, 'loop': bool(loop), 'note': note}
        return a

    emit('Walking', src, T, True, note='swim')
    emit('Running', src, T, True, rate=1.5, note='swim x1.5')
    emit('Standing', {b: scaled(r, 0.5) for b, r in src.items()}, T, True, rate=0.6, note='swim x0.6, amplitude 0.5')
    amp_f = lambda x: 0.5 + 0.7 * math.sin(math.pi * x)
    emit('Fidget', {b: repeat(r, 2, amps=amp_f) for b, r in src.items()}, 2 * T, False,
         note='two beats, amplitude 0.5-1.2-0.5')
    roll_hit = lambda x: 14.0 * math.sin(math.pi * x)
    hit = {b: (repeat(r, 1, amps=lambda x: 1.35, rolls=roll_hit, roll_axis=roll_axis) if b == 'XCENTER'
               else scaled(r, 1.35)) for b, r in src.items()}
    emit('Hit', hit, T, False, rate=2.1, note='swim x2.1, amplitude 1.35, roll 14 deg')
    cyc, hold = 4, 0.5
    amp_d = lambda x: max(0.0, 1.0 - x * (cyc * T + hold) / (cyc * T)) ** 1.5
    roll_d = lambda x: 90.0 * smooth((x * (cyc * T + hold) - 0.35) / (cyc * T - 0.35))
    # the pectoral fins fold flat against the flanks as the fish dies (the one underneath would hold the corpse a
    # centimetre off the floor): a 14 degree turn about the vertical through the fin root, eased in with the roll
    fold = {}
    for b, sgn in (('Xsfin01', 1.0), ('Xsfin', -1.0)):
        Rb = arm.data.bones[b].matrix_local.to_3x3()
        fold[b] = ((Rb.inverted() @ Vector((0, 0, 1))).normalized(), sgn)
    death = {}
    for b, r in src.items():
        if b == 'XCENTER':
            death[b] = repeat(r, cyc, amps=amp_d, rolls=roll_d, roll_axis=roll_axis, hold=hold)
        elif b in fold:
            ax, sgn = fold[b]
            death[b] = repeat(r, cyc, amps=amp_d, rolls=lambda x, sgn=sgn: sgn * 14.0 * roll_d(x) / 90.0,
                              roll_axis=ax, hold=hold)
        else:
            death[b] = repeat(r, cyc, amps=amp_d, hold=hold)
    emit('Death', death, cyc * T + hold, False, rate=1.4, note='4 decaying beats at x1.4, roll 90 deg, 0.36 s still')
    rep['roll_axis_local'] = list(roll_axis)
    return rep
