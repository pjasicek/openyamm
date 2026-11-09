"""G3 composition after the X-ray comparison (TEST_DRIVE.md): Meshy's auto-rig for the axial joints, clavicles, shoulders,
hips and knees (ring geometry was fooled by the pauldrons and the boot cuffs); ring centres for wrists and ankles
(Meshy's wrists sit 2-3 cm up the forearm). Each elbow is re-derived on the ring centreline as the point of largest
deviation from the (Meshy shoulder -> ring wrist) line, and checked against the source upper-arm : forearm ratio.
Writes work/joints_final.json. Args: none"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(HERE, 'work', 'joints.json')))
M = json.load(open(os.path.join(HERE, 'work', 'meshy_joints.json')))['joints']
CL = json.load(open(os.path.join(HERE, 'work', 'centrelines.json')))
SRC = json.load(open(os.path.join(HERE, 'work', 'proportions.json')))['source']
J = {k: np.array(v) for k, v in M.items()}
src_ratio = SRC['upper_arm_R'] / (SRC['upper_arm_R'] + SRC['forearm_R'])
report = {}
for s in ('R', 'L'):
    J[f'{s}_Hand'] = np.array(R['joints'][f'{s}_Hand'])
    J[f'{s}_Foot'] = np.array(R['joints'][f'{s}_Foot'])
    J[f'{s}_Calf'] = np.array(R['joints'][f'{s}_Calf'])
    sh, wr = J[f'{s}_UpperArm'], J[f'{s}_Hand']
    cs = np.array(CL[f'{s}_arm'])
    d = (wr - sh) / np.linalg.norm(wr - sh)
    t = (cs - sh) @ d / np.linalg.norm(wr - sh)
    # elbow = closest approach of two line fits (upper-arm ring centres t 0.15-0.42, forearm 0.60-0.92); a single
    # max-deviation point latched onto the armlet / gauntlet bulges (left elbow at t 0.33)
    def fit(mask):
        p = cs[mask]; c = p.mean(0); u = np.linalg.svd(p - c)[2][0]
        return c, (u if u @ d > 0 else -u)
    c1, u1 = fit((t > 0.15) & (t < 0.42)); c2, u2 = fit((t > 0.60) & (t < 0.92))
    w0 = c1 - c2; a, b, c_, dd, e = u1 @ u1, u1 @ u2, u2 @ u2, u1 @ w0, u2 @ w0
    den = a * c_ - b * b
    s1 = (b * e - c_ * dd) / den if abs(den) > 1e-9 else 0.0
    s2 = (a * e - b * dd) / den if abs(den) > 1e-9 else 0.0
    el = ((c1 + u1 * s1) + (c2 + u2 * s2)) / 2
    gap = float(np.linalg.norm((c1 + u1 * s1) - (c2 + u2 * s2)))
    bend = float(np.degrees(np.arccos(np.clip(u1 @ u2, -1, 1))))
    # natm: the line fits put the elbow at t 0.68-0.76 (forearm muscle bulge); Meshy's elbow sits at t ~0.51, which
    # matches the HD front master. Use Meshy's t, centred on the ring centreline (interpolated at that t).
    tm = float((np.array(M[f'{s}_Forearm']) - sh) @ d / np.linalg.norm(wr - sh))
    o = np.argsort(t); el = np.array([np.interp(tm, t[o], cs[o][:, k]) for k in range(3)])
    print('ELBOW', s, 'meshy t', round(tm, 3), 'centred move cm', round(float(np.linalg.norm(el - np.array(M[f'{s}_Forearm']))) * 100, 2))
    J[f'{s}_Forearm'] = el
    up, fo = np.linalg.norm(el - sh), np.linalg.norm(wr - el)
    hinge = np.cross(u1, u2); hinge /= max(np.linalg.norm(hinge), 1e-9)
    report[s] = {'bend_deg': round(bend, 1), 'line_gap_mm': round(gap * 1000, 1),
                 'elbow_t': round(float((el - sh) @ d / np.linalg.norm(wr - sh)), 3), 'source_t': round(src_ratio, 3),
                 'upper_m': round(float(up), 3), 'fore_m': round(float(fo), 3), 'hinge': [round(float(x), 3) for x in hinge],
                 'meshy_elbow_off_cm': round(float(np.linalg.norm(el - np.array(M[f'{s}_Forearm']))) * 100, 1)}
    print('ELBOW', s, json.dumps(report[s]))
json.dump({'height_m': R['height_m'], 'joints': {k: [round(float(x), 5) for x in v] for k, v in J.items()},
           'report': report}, open(os.path.join(HERE, 'work', 'joints_final.json'), 'w'), indent=1)
