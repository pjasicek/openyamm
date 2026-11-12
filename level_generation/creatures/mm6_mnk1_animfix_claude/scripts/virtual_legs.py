#!/usr/bin/env python3
"""Damp the BMonk's leg-driven robe in chosen clips (anim fix, 2026-11-11).

The robe hangs on virtual legs (mm6_mnk1_codex, gait rework): `Cloth_<s>_Thigh` (child of the thigh) swings a share of
the thigh, `Cloth_<s>_Calf` (child of the calf) starts at that virtual knee and points at the real ankle, its +Y scale
the knee-ankle distance over the rest length; the hem hangs mostly on `Cloth_<s>_Foot` (child of the real foot). On Run2's long strides the virtual calf squashes to 0.55 and stretches to
1.12 and the panels between the legs flatten into sheets. Per key:
- virtual thigh: world rotation = slerp(pelvis-carried bind rotation, installed rotation, `--thigh k`);
- virtual ankle = pelvis-carried rest ankle + `--calf a` x (real ankle - rest ankle);
- virtual calf: from the new virtual knee to the virtual ankle (+Y scale = distance / rest length);
- virtual foot (hem): at the virtual ankle; rotation = slerp(pelvis-carried rest, real foot, `--foot f`).
Only rotation/translation/scale samplers of the six cloth leg bones in the named clips change (new accessors).

    virtual_legs.py <in.glb> <out.glb> --clips Run2 [--thigh 0.7] [--calf 0.6]
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def rot_between(u, v):
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    axis = np.cross(u, v)
    s, c = np.linalg.norm(axis), float(np.clip(u @ v, -1, 1))
    if s < 1e-12:
        return np.eye(3)
    k = axis / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def slerp_m(a, b, t):
    q = glb_pose.slerp(glb_pose.matrix_quaternion(a), glb_pose.matrix_quaternion(b), t)
    return glb_pose.quaternion_matrix(q / np.linalg.norm(q))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--clips', nargs='+', required=True)
    p.add_argument('--thigh', type=float, default=1.0)
    p.add_argument('--calf', type=float, default=1.0)
    p.add_argument('--foot', type=float, default=1.0, help='share of the real foot rotation the hem keeps')
    args = p.parse_args()
    g = glb_pose.Glb(args.input)
    m = glb_pose.Model(g)
    doc = g.json
    n = [x.get('name', '') for x in doc['nodes']]
    I = {x: i for i, x in enumerate(n)}
    J = list(m.joints)
    B = {n[j]: np.linalg.inv(m.inverse_binds[k]) for k, j in enumerate(J)}
    for clip in args.clips:
        anim = doc['animations'][m.clips[clip]]
        times = np.array(m.clip_times(clip))
        out = {}
        for s in 'LR':
            th, cc, cf = I[f'Cloth_{s}_Thigh'], I[f'Cloth_{s}_Calf'], I[f'Cloth_{s}_Foot']
            Bct, Bcc, Bp = B[f'Cloth_{s}_Thigh'], B[f'Cloth_{s}_Calf'], B['B_Pelvis']
            knee_local = np.linalg.inv(Bct[:3, :3]) @ (B[f'B_{s}_Calf'][:3, 3] - Bct[:3, 3])
            rest_len = np.linalg.norm(B[f'B_{s}_Foot'][:3, 3] - B[f'B_{s}_Calf'][:3, 3])
            rows = {th: [], cc: [], cf: []}
            for t in times:
                W = m.world(m.sample(clip, float(t)))
                Wct = W[th]
                carried = (W[I['B_Pelvis']] @ np.linalg.inv(Bp) @ Bct)[:3, :3]
                R0 = Wct[:3, :3] / np.linalg.norm(Wct[:3, :3], axis=0)
                carried = carried / np.linalg.norm(carried, axis=0)
                Rt = slerp_m(carried, R0, args.thigh)
                knee = Wct[:3, 3] + Rt @ knee_local
                ankle = W[I[f'B_{s}_Foot']][:3, 3]
                # virtual ankle: between the pelvis-carried rest ankle and the real one (`--calf a`)
                rest_ankle = (W[I['B_Pelvis']] @ np.linalg.inv(Bp) @ B[f'B_{s}_Foot'])[:3, 3]
                target = rest_ankle + args.calf * (ankle - rest_ankle)
                to_ankle = target - knee
                dist = np.linalg.norm(to_ankle)
                Wcc = W[cc]
                Rc0 = Wcc[:3, :3] / np.linalg.norm(Wcc[:3, :3], axis=0)
                thigh_dir = Rt @ (np.linalg.inv(Bct[:3, :3]) @ Bcc[:3, 1])     # calf's rest axis carried by the thigh
                want = to_ankle / dist
                Rc = rot_between(Rc0[:, 1], want) @ Rc0
                ys = dist / rest_len
                Mt = np.eye(4)
                Mt[:3, :3] = Rt
                Mt[:3, 3] = Wct[:3, 3]
                Mc = np.eye(4)
                Mc[:3, :3] = Rc * np.array([1.0, ys, 1.0])[None, :]
                Mc[:3, 3] = knee
                # the hem rides on Cloth_<s>_Foot (child of the real foot): move it to the virtual ankle, keeping the
                # foot's own rotation, so the hem follows the damped virtual leg instead of the real stride
                Mf = W[cf].copy()
                Mf[:3, 3] = target
                # and its rotation between the pelvis-carried rest and the real foot's: the hem spans ~0.4 m around
                # the ankle, so the heel kick's foot pitch alone swung the whole hem into a sheet
                Rf0 = W[cf][:3, :3] / np.linalg.norm(W[cf][:3, :3], axis=0)
                Rfc = (W[I['B_Pelvis']] @ np.linalg.inv(Bp) @ B[f'Cloth_{s}_Foot'])[:3, :3]
                Mf[:3, :3] = slerp_m(Rfc / np.linalg.norm(Rfc, axis=0), Rf0, args.foot)
                for node, Mw in ((th, Mt), (cc, Mc), (cf, Mf)):
                    local = np.linalg.inv(W[m.parent[node]]) @ Mw
                    sc = np.linalg.norm(local[:3, :3], axis=0)
                    rows[node].append((local[:3, 3], glb_pose.matrix_quaternion(local[:3, :3] / sc), sc))
            out.update(rows)
        for ch in anim['channels']:
            node = ch['target']['node']
            if node not in out:
                continue
            path = ch['target']['path']
            sampler = anim['samplers'][ch['sampler']]
            keys = g.accessor(sampler['input'])[:, 0]
            pick = [int(np.argmin(np.abs(times - k))) for k in keys]
            vals = [out[node][i][{'translation': 0, 'rotation': 1, 'scale': 2}[path]] for i in pick]
            vals = np.array(vals)
            if path == 'rotation':
                for i in range(1, len(vals)):
                    if np.dot(vals[i], vals[i - 1]) < 0:
                        vals[i] = -vals[i]
            sampler['output'] = g.append_accessor(vals, 'VEC4' if path == 'rotation' else 'VEC3')
            sampler['interpolation'] = 'LINEAR'
        print(f'VLEGS {clip}: thigh {args.thigh} calf {args.calf} foot {args.foot}')
    g.write(args.output)


if __name__ == '__main__':
    main()
