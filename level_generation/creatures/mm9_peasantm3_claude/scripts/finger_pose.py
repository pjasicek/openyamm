#!/usr/bin/env python3
"""Relaxed five-finger hands that follow MM9's mitten curl (user review 2026-11-02, Standing: "both hands read as stiff
splayed claws"). Replaces the finger_alias keys of clips_mm9.py for the 30 MPFB finger bones in every clip.

Why: finger_alias copied Finger1's whole rotation (twist and abduction too) onto every finger's MCP and Finger11/12's
rotation away from MM9's bind onto the distal joints in mismatched frames. MM9's bind mitten is already curled
(MCP 27, PIP 15 deg) and the MPFB bind is splayed (left hand index/ring/pinky 19/14/24 deg off the middle finger, right
13/4/10), so Standing kept the splayed bind with hooked tips: claws instead of MM9's relaxed mitten and hand on the hip.

Now, per key: MM9's mitten flexion, measured absolutely in the hand (MCP = Hand axis -> Finger1 -> Finger11, PIP, DIP;
thumb IP from Finger0 -> Finger01) drives a flexion-only pose of each MPFB finger about its own lateral axis (palm
normal from the MPFB bind curl), so the fingers stay together and curl as one:
  MM9's bind mitten (MCP 28.6, PIP 14.5) counts as the MPFB bind's curl; the fingers follow MM9's curl relative to its bind:
  MCP = bind + clip(MM9 MCP - 28.6, -OPEN, 45) + (MCP_EXTRA + cascade) x relax, PIP = bind + clip(MM9 PIP - 14.5,
  -OPEN, 70) + (PIP_EXTRA + cascade) x relax, DIP = bind + 0.6 (PIP - bind); relax = clip(1 + mean(MCP, PIP delta)/OPEN,
  0, 1): the relaxed curl (mostly at the knuckle, so the fingers do not hook) fades out where MM9 opens the hand
  (Sc2_KIRA5's flat gesture); cascade index -4 / middle 0 / ring +4 / pinky +8 (MCP), 0/0/+3/+6 (PIP).
  Spread in the palm plane set to SPREAD (index +3 towards the thumb, ring -3, pinky -6 deg from the middle finger).
  Thumb: IP THUMB_IP deg plus half of MM9's thumb flexion beyond its bind, about the thumb's own bend axis, and
  THUMB_IN deg towards the index.
Usage: finger_pose.py <in glb> <out glb> [--mcp-extra 18] [--pip-extra 6] [--open 12] [--thumb-ip 20] [--thumb-in 8]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--mcp-extra', type=float, default=18.0); ap.add_argument('--pip-extra', type=float, default=6.0)
ap.add_argument('--thumb-ip', type=float, default=20.0)
ap.add_argument('--thumb-in', type=float, default=8.0)
ap.add_argument('--open', type=float, default=12.0)
o = ap.parse_args(); OPEN = o.open
FING = ['Index', 'Middle', 'Ring', 'Pinky']
CAS_MCP = dict(Index=-4, Middle=0, Ring=4, Pinky=8); CAS_PIP = dict(Index=0, Middle=0, Ring=3, Pinky=6)
SPREAD = dict(Index=3.0, Middle=0.0, Ring=-3.0, Pinky=-6.0)
g = Glb(o.src); m = Model(g); names = [n.get('name') for n in g.json['nodes']]; ix = {n: i for i, n in enumerate(names)}
W0 = m.world({})


def rotm(axis, ang):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def unit(v): return v / np.linalg.norm(v)
def rot(M): return M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
def sang(a, b, lat):
    """signed angle a -> b about lat"""
    return np.degrees(np.arctan2(np.dot(np.cross(a, b), lat), np.dot(a, b)))


# skin vertices for the finger tips (bind)
pr = m.primitives[0]; jn = [names[j] for j in m.joints]
P0 = np.vstack([p['positions'] for p in m.primitives if p['skinned']])
J0 = np.vstack([p['joints'] for p in m.primitives if p['skinned']]); Wt = np.vstack([p['weights'] for p in m.primitives if p['skinned']])
SIDE = {}
for s in 'LR':
    B = lambda n: f'Bip01 {s} {n}'
    H = ix[B('Hand')]; HR = rot(W0[H]); pos = lambda n: W0[ix[n]][:3, 3]
    hand_l = lambda v: HR.T @ v                     # world (bind) -> hand-local
    d = {}
    for f in FING + ['Thumb']:
        p = [pos(B(f'{f}{k}')) for k in (1, 2, 3)]
        j3 = jn.index(B(f'{f}3')); w3 = (Wt * (J0 == j3)).sum(1)
        cand = np.where(w3 > 0.5)[0]; seg = p[2] - p[1]
        tip = P0[cand[np.argmax((P0[cand] - p[2]) @ seg)]]
        d[f] = [hand_l(unit(p[1] - p[0])), hand_l(unit(p[2] - p[1])), hand_l(unit(tip - p[2]))]
        d[f + '_j1'] = hand_l(p[0] - W0[H][:3, 3])
    # palm normal: where the MPFB fingers bend (PIP), averaged
    n = sum(unit(d[f][1] - d[f][0] * (d[f][1] @ d[f][0])) for f in FING); n = unit(n)
    mdir = unit(d['Middle_j1'])
    info = dict(n=n, mdir=mdir, d=d, G={})
    for f in FING + ['Thumb']:
        for k in (1, 2, 3):
            info['G'][f'{f}{k}'] = HR.T @ rot(W0[ix[B(f'{f}{k}')]])
    rest = {}
    for f in FING:
        lat = unit(np.cross(d[f][0], n))
        # sign: +angle bends towards the palm normal
        rest[f] = dict(lat=lat, mcp=sang(mdir - n * (mdir @ n) * 0, d[f][0], lat), pip=sang(d[f][0], d[f][1], lat), dip=sang(d[f][1], d[f][2], lat),
                       spread=sang(d['Middle'][0] - n * (d['Middle'][0] @ n), d[f][0] - n * (d[f][0] @ n), n))
    tl = unit(np.cross(d['Thumb'][0], d['Thumb'][1]))
    rest['Thumb'] = dict(lat=tl, ip=sang(d['Thumb'][1], d['Thumb'][2], tl),
                         spread=sang(d['Middle'][0] - n * (d['Middle'][0] @ n), d['Thumb'][0] - n * (d['Thumb'][0] @ n), n))
    info['tsgn'] = 1.0 if rest['Thumb']['spread'] > 0 else -1.0
    # MM9 mitten bind, hand-local
    mit = lambda nm: HR.T @ rot(W0[ix[B(nm)]])
    hx = unit(HR.T @ (pos(B('Finger1')) - W0[H][:3, 3]))
    f1 = unit(HR.T @ (pos(B('Finger11')) - pos(B('Finger1'))))
    nm9 = unit(f1 - hx * (f1 @ hx)); latm = unit(np.cross(hx, nm9))
    if np.degrees(np.arccos(np.clip(f1 @ hx, -1, 1))) < 15:
        # mm9_peasantm3: PeasantMale's bind mitten is nearly flat (MCP 1-9 deg), so the curl gives no bend axis: take the
        # mitten's own bone Z (Biped fingers bend about it), signed so that it agrees with the MPFB fingers' curl axis
        z = unit(HR.T @ rot(W0[ix[B('Finger1')]]) @ np.array([0, 0, 1.0]))
        ref = unit(np.cross(d['Middle'][0], n))
        latm = z if z @ ref > 0 else -z
    info.update(rest=rest, hx=hx, latm=latm)
    SIDE[s] = info
    print('FINGERREST', s, json.dumps({f: {k: round(float(v), 1) for k, v in r.items() if k != 'lat'} for f, r in rest.items()}),
          'palm n.mdir', round(float(n @ mdir), 2))


def mitten(w, s):
    B = lambda nm: w[ix[f'Bip01 {s} {nm}']]
    HR = rot(B('Hand')); I = SIDE[s]
    loc = lambda p: HR.T @ (p - B('Hand')[:3, 3])
    p1, p11 = loc(B('Finger1')[:3, 3]), loc(B('Finger11')[:3, 3])
    if f'Bip01 {s} Finger12' in ix:
        p12 = loc(B('Finger12')[:3, 3])
        d3 = HR.T @ rot(B('Finger12')) @ np.array([-1.0, 0, 0])
    else:   # mm9_peasantm3: the PeasantMale mitten has two joints (no Finger12 tip node): the distal segment runs along
        # Finger11's own bone axis (-X, as the thumb's Finger01 below), DIP 0
        d3 = HR.T @ rot(B('Finger11')) @ np.array([AX, 0, 0])
        p12 = p11 + d3 * np.linalg.norm(p11 - p1)
    lat = I['latm']; hx = unit(p1)
    mcp = sang(I['hx'], unit(p11 - p1), lat); pip = sang(unit(p11 - p1), unit(p12 - p11), lat); dip = sang(unit(p12 - p11), d3, lat)
    if f'Bip01 {s} Finger12' not in ix:
        # mm9_peasantm3: MM9's PeasantMale clips turn Finger11 about mixed axes (twist + bend), so a signed angle about
        # one bend axis flipped by 150-180 deg; flexion only, unsigned (a pure twist reads as 0)
        ang = lambda a, b: float(np.degrees(np.arccos(np.clip(unit(a) @ unit(b), -1, 1))))
        mcp, pip, dip = ang(I['hx'], p11 - p1), ang(p11 - p1, d3), 0.0
    t0, t1 = loc(B('Finger0')[:3, 3]), loc(B('Finger01')[:3, 3])
    td = HR.T @ rot(B('Finger01')) @ np.array([AX, 0, 0])
    tip = np.degrees(np.arccos(np.clip(unit(t1 - t0) @ unit(td), -1, 1)))
    return mcp, pip, dip, tip


# bone axis along the segment: -X on Kira's skeleton, +X on PeasantMale (mm9_peasantm3); from the bind thumb Finger0 -> Finger01
_t0, _t1 = W0[ix['Bip01 L Finger0']], W0[ix['Bip01 L Finger01']]
AX = -1.0 if (rot(_t0) @ np.array([-1.0, 0, 0])) @ (_t1[:3, 3] - _t0[:3, 3]) > 0 else 1.0
print('MITTEN axis', AX)
MREST = {s: mitten(W0, s) for s in 'LR'}
print('MITTENREST', {s: [round(float(x), 1) for x in v] for s, v in MREST.items()})


def pose(s, mm):
    I = SIDE[s]; R = I['rest']; n = I['n']; G = I['G']
    mcp_m, pip_m, dip_m, tip_m = mm
    out = {}
    for f in FING:
        r = R[f]; lat = r['lat']
        dm, dp = mcp_m - MREST[s][0], pip_m - MREST[s][1]
        relax = min(max(1 + 0.5 * (dm + dp) / OPEN, 0), 1)      # MM9 opening the hand past its bind fades the relaxed curl out
        mcp = r['mcp'] + min(max(dm, -OPEN), 45) + (o.mcp_extra + CAS_MCP[f]) * relax
        pip = r['pip'] + min(max(dp, -OPEN), 70) + (o.pip_extra + CAS_PIP[f]) * relax
        dip = r['dip'] + 0.6 * (pip - r['pip'])
        Rs = rotm(n, np.radians(SPREAD[f] * I['tsgn'] - r['spread']))
        R1 = Rs @ rotm(lat, np.radians(mcp - r['mcp']))
        R2 = R1 @ rotm(lat, np.radians(pip - r['pip']))
        R3 = R2 @ rotm(lat, np.radians(dip - r['dip']))
        g1, g2, g3 = R1 @ G[f'{f}1'], R2 @ G[f'{f}2'], R3 @ G[f'{f}3']
        out[f'{f}1'], out[f'{f}2'], out[f'{f}3'] = g1, g1.T @ g2, g2.T @ g3
    tl = R['Thumb']['lat']; extra = np.radians(np.clip(0.5 * (tip_m - MREST[s][3]), 0, 30))
    Rin = rotm(n, np.radians(o.thumb_in) * (1 if np.dot(np.cross(I['d']['Thumb'][0], I['d']['Index'][0]), n) > 0 else -1))
    T1 = Rin; T2 = T1 @ rotm(tl, extra * 0.6); T3 = T2 @ rotm(tl, extra + np.radians(o.thumb_ip - R['Thumb']['ip']))
    g1, g2, g3 = T1 @ G['Thumb1'], T2 @ G['Thumb2'], T3 @ G['Thumb3']
    out['Thumb1'], out['Thumb2'], out['Thumb3'] = g1, g1.T @ g2, g2.T @ g3
    return out


rep = {}
for an in g.json['animations']:
    clip = an.get('name'); ch = {}
    for c in an['channels']:
        if c['target']['path'] == 'rotation': ch[names[c['target']['node']]] = c
    stats = {}
    for s in 'LR':
        ref = ch.get(f'Bip01 {s} Hand') or ch.get(f'Bip01 {s} Finger1')
        times = g.accessor(an['samplers'][ref['sampler']]['input'])[:, 0]
        Q = {f'{f}{k}': [] for f in FING + ['Thumb'] for k in (1, 2, 3)}; mm_all = []
        for t in times:
            mm = mitten(m.world(m.sample(clip, float(t))), s); mm_all.append(mm)
            for k, L in pose(s, mm).items(): Q[k].append(matrix_quaternion(L))
        tin = an['samplers'][ref['sampler']]['input']
        for k, qs in Q.items():
            qs = np.array(qs)
            for i in range(1, len(qs)):
                if np.dot(qs[i], qs[i - 1]) < 0: qs[i] = -qs[i]
            node = f'Bip01 {s} {k}'; acc = g.append_accessor(qs, 'VEC4')
            if node in ch:
                smp = an['samplers'][ch[node]['sampler']]; smp['input'] = tin; smp['output'] = acc; smp['interpolation'] = 'LINEAR'
            else:
                an['samplers'].append({'input': tin, 'output': acc, 'interpolation': 'LINEAR'})
                an['channels'].append({'sampler': len(an['samplers']) - 1, 'target': {'node': ix[node], 'path': 'rotation'}})
        mm_all = np.array(mm_all)
        stats[s] = dict(mcp=[round(float(x)) for x in (mm_all[:, 0].min(), mm_all[:, 0].max())], pip=[round(float(x)) for x in (mm_all[:, 1].min(), mm_all[:, 1].max())])
    rep[clip] = stats
g.write(o.dst)
print('FINGERPOSE', json.dumps(rep)[:1500])
