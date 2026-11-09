"""Lower-body slimming of the m286 v2 mesh toward the native silhouette (pure numpy; used by step1_clean.py on the mesh
and by meshy_joints.py on Meshy's joints, so the rig matches the reshaped body; build_rig.py matches Meshy's weights on
the pre-reshape 'orig_co').
The Smart Topology body follows its HD master, whose hips and fur kilt are about 25 % wider than the native at the
native hip row (0.41 H) and whose legs stand apart (user 2026-10-20: "too big legs"). x is scaled toward the midline:
K_SHIN below 0.40 m (shins, hooves), K_LEG at 0.50 m (thighs), K_HIP over 0.65-0.95 m (hips and kilt), linear between, back to 1 at the waist
(1.07 m). The A-pose arms and hands beside the hips (|x| > 0.42 m above 0.55 m) are left alone, fading in over 6 cm."""
import os
import numpy as np
K_LEG = float(os.environ.get('RESHAPE_K_LEG', '0.92'))
K_HIP = float(os.environ.get('RESHAPE_K_HIP', '0.83'))
K_SHIN = float(os.environ.get('RESHAPE_K_SHIN', '0.88'))   # shins and hooves (native shin 0.077 H)


def factor(co):
    co = np.asarray(co, np.float64).reshape(-1, 3)
    z, ax = co[:, 2], np.abs(co[:, 0])
    k = np.interp(z, [0.0, 0.40, 0.50, 0.65, 0.95, 1.07], [K_SHIN, K_SHIN, K_LEG, K_HIP, K_HIP, 1.0])
    wx = np.where(z > 0.55, np.clip((0.42 - ax) / 0.06, 0, 1), 1.0)
    return 1 - (1 - k) * wx


def apply(co):
    co = np.array(co, np.float64).reshape(-1, 3)
    co[:, 0] *= factor(co)
    return co


# Arm slimming. Smart Topology made the arms about 20 % thicker than the native and the master (upper arm 0.13 H vs
# 0.11 H; deltoids 0.52 H across vs 0.43 H): radial scale ARM_K about the rest arm axis (shoulder -> elbow -> wrist, the
# rig_v2 joints of joints_final.json, A-pose), ramped in from the shoulder joint over the first 10 % of the chain so the
# torso and the armpit stay, out again over the last 10 % before the wrist (hands unchanged).
ARM_K = float(os.environ.get('RESHAPE_ARM_K', '0.84'))
ARM_AXES = {'L': [(0.2926, 0.0066, 1.4247), (0.4146, 0.0100, 1.1643), (0.5840, -0.0727, 0.9296)],
            'R': [(-0.3158, 0.0070, 1.4247), (-0.4418, 0.0111, 1.1506), (-0.5942, -0.0730, 0.9307)]}
ARM_RMAX = 0.16


def arm_apply(co):
    co = np.array(co, np.float64).reshape(-1, 3)
    out = co.copy()
    for side, pts in ARM_AXES.items():
        P = np.array(pts)
        seg = np.diff(P, axis=0); L = np.linalg.norm(seg, axis=1); total = L.sum()
        best = np.full(len(co), np.inf); foot = np.zeros_like(co); tt = np.zeros(len(co))
        for k in range(2):
            u = seg[k] / L[k]
            t = np.clip((co - P[k]) @ u, 0, L[k])
            f = P[k] + np.outer(t, u)
            d = np.linalg.norm(co - f, axis=1)
            m = d < best
            best[m], foot[m], tt[m] = d[m], f[m], (L[:k].sum() + t[m]) / total
        sel = (best < ARM_RMAX) & (np.sign(co[:, 0]) == np.sign(P[0, 0])) & (np.abs(co[:, 0]) > np.abs(P[0, 0]) - 0.04)
        ramp = np.clip(tt / 0.10, 0, 1) * np.clip((1.0 - tt) / 0.10, 0, 1)
        k = 1 - (1 - ARM_K) * ramp
        out[sel] = foot[sel] + (co[sel] - foot[sel]) * k[sel, None]
    return out


# ---------------------------------------------------------------- v2a (user review 2026-10-21: abs notch, shoulder step)
# The functions above (kept for the joints and for replay: step1_clean.py / meshy_joints.py) have hard edges: the arm
# slim stops at ARM_RMAX and at the |x| selection (a ~2.5 cm step where the deltoid meets the back) and the lower-body
# k(z) is piecewise linear with a 12 cm ramp just above the belt (a crease at the flank). fix_reshape.py replaces their
# displacement on the rigged, reduced mesh by smooth versions: the same slimming amounts, C1 transitions, and the arm
# slim weighted by each vertex's own upper-arm/forearm skin weight (no radius or selection edge).
def _smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _sinterp(z, knots, vals):
    z = np.asarray(z, np.float64); out = np.full(z.shape, float(vals[0]))
    for (z0, z1), (v0, v1) in zip(zip(knots[:-1], knots[1:]), zip(vals[:-1], vals[1:])):
        m = z >= z0
        out[m] = v0 + (v1 - v0) * _smooth((z[m] - z0) / max(z1 - z0, 1e-9))
    return out


def apply_smooth(co):
    co = np.array(co, np.float64).reshape(-1, 3)
    z, ax = co[:, 2], np.abs(co[:, 0])
    k = _sinterp(z, [0.0, 0.40, 0.50, 0.65, 0.80, 1.04], [K_SHIN, K_SHIN, K_LEG, K_HIP, K_HIP, 1.0])
    wx = 1 - _smooth((z - 0.50) / 0.10) * (1 - _smooth((0.42 - ax) / 0.07))
    co[:, 0] *= 1 - (1 - k) * wx
    return co


def arm_delta_weighted(co, w_arm):
    """Radial slim (ARM_K) about the rest arm axis scaled by w_arm[side] (per-vertex upper-arm + forearm weight),
    eased out over the last 15 % of the chain before the wrist."""
    co = np.asarray(co, np.float64).reshape(-1, 3)
    delta = np.zeros_like(co)
    for side, pts in ARM_AXES.items():
        P = np.array(pts); seg = np.diff(P, axis=0); L = np.linalg.norm(seg, axis=1); total = L.sum()
        best = np.full(len(co), np.inf); foot = np.zeros_like(co); tt = np.zeros(len(co))
        for k in range(2):
            u = seg[k] / L[k]; t = np.clip((co - P[k]) @ u, 0, L[k]); f = P[k] + np.outer(t, u)
            d = np.linalg.norm(co - f, axis=1); m = d < best
            best[m], foot[m], tt[m] = d[m], f[m], (L[:k].sum() + t[m]) / total
        w = np.asarray(w_arm[side]) * _smooth((1.0 - tt) / 0.15)
        delta += (co - foot) * ((ARM_K - 1) * w)[:, None]
    return delta
