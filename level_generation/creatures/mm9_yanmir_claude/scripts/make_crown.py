#!/usr/bin/env python3
"""Yanmir's ice crown as its own rigid part on Head (MM9: a band of engraved silver knotwork with a pointed plate over the forehead
and a dozen clear ice spikes, the tallest at the front and the temples). Built on our head (work/body_rest.npz, Blender axes,
rest): the band follows the hair's cross-section 6 mm proud, level at the hairline (front 1.205-1.250, back 1.215-1.258), a
V plate dips 3 cm down the brow at the front; spikes are 6-sided cones on the band's top edge leaning a little outward.
UVs on the accessory atlas (make_staff.py): band and plate silver (v 0.50-0.75), spikes ice (u 0.5-1.0, v 0.75-1.0).
Writes work/crown.npz: V (Blender world, rest), F, UV, KIND (1 silver, 3 ice). Args: none (project folder)"""
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
d = np.load(HERE / 'work' / 'body_rest.npz'); P = d['P']; pa = d['part']
P = P[pa == 0]
N = 64
Z0F, Z1F, Z0B, Z1B = 1.205, 1.250, 1.215, 1.258
OFF, TH = 0.006, 0.010
CY = 0.0                                   # the skull's centre front-to-back at band height (y -0.15 .. +0.15)
ang = np.linspace(0, 2 * np.pi, N, endpoint=False)


def surf_radius(zc):
    """outer radius of the head per angle (front = -y) in a 1.2 cm slab round height zc"""
    s = P[(np.abs(P[:, 2] - zc) < 0.012) & (np.abs(P[:, 0]) < 0.25) & (np.abs(P[:, 1]) < 0.25)]
    a = np.arctan2(s[:, 0], -(s[:, 1] - CY)) % (2 * np.pi); r = np.hypot(s[:, 0], s[:, 1] - CY)
    out = np.zeros(N)
    for i, t in enumerate(ang):
        dd = np.abs((a - t + np.pi) % (2 * np.pi) - np.pi)
        m = dd < 2 * np.pi / N * 1.5
        out[i] = r[m].max() if m.any() else np.nan
    ok = ~np.isnan(out); out = np.interp(np.arange(N), np.nonzero(ok)[0], out[ok], period=N)
    k = np.array([1, 4, 6, 4, 1]) / 16.0
    return np.convolve(np.r_[out[-2:], out, out[:2]], k, 'valid')


front = (1 + np.cos(ang)) / 2                       # 1 at the front, 0 at the back
zb = Z0B + (Z0F - Z0B) * front; zt = Z1B + (Z1F - Z1B) * front
R = np.maximum(surf_radius((Z0F + Z1F) / 2), surf_radius(Z1F)) + OFF
dip = 0.032 * np.clip(1 - np.abs(((ang + np.pi) % (2 * np.pi)) - np.pi) / np.radians(16), 0, 1)   # the V plate at the front
V, F, UV, K = [], [], [], []


def add(p, uv): V.append(tuple(p)); UV.append(uv); return len(V) - 1


def pt(i, r, z):
    return (r * np.sin(ang[i % N]), CY - r * np.cos(ang[i % N]), z)


SV = lambda t: 0.52 + 0.21 * t
rows = []       # outer bottom, outer top, inner top, inner bottom (closed section)
for i in range(N + 1):
    u = i / N * 3.0                                  # the knotwork tile three times round
    j = i % N
    zb_ = zb[j] - dip[j]
    rows.append([add(pt(j, R[j] + TH, zb_), (u, SV(0.0))), add(pt(j, R[j] + TH, zt[j]), (u, SV(1.0))),
                 add(pt(j, R[j] - 0.002, zt[j]), (u, SV(0.95))), add(pt(j, R[j] - 0.002, zb_), (u, SV(0.05)))])
for a, b in zip(rows[:-1], rows[1:]):
    for k in range(4):
        k1 = (k + 1) % 4
        F.append((a[k], b[k], b[k1])); F.append((a[k], b[k1], a[k1])); K += [1, 1]
# spikes: (angle deg, length, base radius)
SP = [(0, 0.175, 0.017), (24, 0.085, 0.011), (-24, 0.085, 0.011), (48, 0.150, 0.015), (-48, 0.150, 0.015), (78, 0.090, 0.012),
      (-78, 0.090, 0.012), (112, 0.125, 0.014), (-112, 0.125, 0.014), (145, 0.080, 0.011), (-145, 0.080, 0.011), (180, 0.110, 0.013)]
NS = 6
for adeg, L, rb in SP:
    t = np.radians(adeg) % (2 * np.pi)
    j = int(round(t / (2 * np.pi) * N)) % N
    r0 = R[j] + TH * 0.5
    base = np.array(pt(j, r0, zt[j] - 0.012))
    out = np.array((np.sin(ang[j]), -np.cos(ang[j]), 0.0))
    ax = np.array((0, 0, 1.0)) * np.cos(np.radians(12)) + out * np.sin(np.radians(12))
    e1 = out - ax * (out @ ax); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
    u0 = 0.5 + 0.5 * ((hash(adeg) % 7) / 7.0)
    ring = [add(base + rb * (np.cos(2 * np.pi * q / NS) * e1 + np.sin(2 * np.pi * q / NS) * e2), (0.5 + 0.5 * q / NS, 0.77)) for q in range(NS + 1)]
    mid = [add(base + ax * L * 0.45 + 0.62 * rb * (np.cos(2 * np.pi * q / NS + 0.3) * e1 + np.sin(2 * np.pi * q / NS + 0.3) * e2), (0.5 + 0.5 * q / NS, 0.87)) for q in range(NS + 1)]
    tip = add(base + ax * L, (0.75, 0.99))
    for q in range(NS):
        F.append((ring[q], ring[q + 1], mid[q + 1])); F.append((ring[q], mid[q + 1], mid[q])); F.append((mid[q], mid[q + 1], tip)); K += [3, 3, 3]
V = np.array(V); F = np.array(F); UV = np.array(UV); K = np.array(K)
# winding: outward from the band's section centre / the spike axis (both convex pieces about a local centre)
cen = V[F].mean(1); nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
ref = np.zeros_like(cen)
band = K == 1
rr = np.hypot(cen[band, 0], cen[band, 1] - CY); dirr = np.c_[cen[band, 0], cen[band, 1] - CY, np.zeros(band.sum())] / rr[:, None]
Rm = np.interp(np.arctan2(cen[band, 0], -(cen[band, 1] - CY)) % (2 * np.pi), np.r_[ang, 2 * np.pi], np.r_[R, R[0]]) + TH / 2 - 0.001
zm = (np.interp(np.arctan2(cen[band, 0], -(cen[band, 1] - CY)) % (2 * np.pi), np.r_[ang, 2 * np.pi], np.r_[zb, zb[0]]) + np.interp(np.arctan2(cen[band, 0], -(cen[band, 1] - CY)) % (2 * np.pi), np.r_[ang, 2 * np.pi], np.r_[zt, zt[0]])) / 2
sec = np.c_[dirr[:, 0] * Rm, CY + dirr[:, 1] * Rm, zm]
out = np.zeros_like(cen); out[band] = cen[band] - sec
fi = np.where(~band)[0]
for s0 in range(0, len(fi), 3 * NS):           # per spike: away from its axis line
    ids = fi[s0:s0 + 3 * NS]; vs = np.unique(F[ids]); c = V[vs].mean(0)
    tipv = V[vs][np.argmax(V[vs][:, 2])]; a_ = tipv - c; a_ /= np.linalg.norm(a_)
    w = cen[ids] - c; out[ids] = w - np.outer(w @ a_, a_)
flip = np.einsum('ij,ij->i', nrm, out) < 0
F[flip] = F[flip][:, ::-1]
np.savez(HERE / 'work' / 'crown.npz', V=V, F=F, UV=UV, KIND=K)
print('CROWN', len(V), 'verts', len(F), 'tris', 'flipped', int(flip.sum()), 'band r', R.min().round(3), R.max().round(3), 'top z', V[:, 2].max().round(3))
