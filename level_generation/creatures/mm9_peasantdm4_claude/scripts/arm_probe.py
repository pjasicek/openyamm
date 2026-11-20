#!/usr/bin/env python3
"""Arm and hand gate on a runtime GLB (humanoid playbook "Arm and hand gate" items 5 and 7; user review 2026-10-30:
Forad's right hand buried in the torso in Talk and Bow, Yrsa's hand into the body in Fidget).

Every clip at the viewer's 48 fps (glb_pose, linear keys as the engine/viewer play them):
- contacts: forearm and hand/finger vertices of each arm against the rest of the body (every face not on that arm).
  Inside test as g6_contacts.py: the nearest surface sample (3 per face + centroid, face normal) and the point lies
  behind it within a 45 deg cone, depth <= 6 cm. Reports the worst depth (cm) and its frame, and the number of frames
  with a hand vertex more than 1 cm inside;
- finger stretch: edge length / rest over edges with both ends on the hand or fingers (p99, max);
- wrist: hand rotation relative to the forearm, change from rest (max deg);
- finger chain count per hand (joints weighted on that hand), as a check that the five chains exist.
Usage: arm_hand_gate.py <glb> <out json> --side L=<token> --side R=<token> [--outer-only] [--exact] [--hand-names Hand,...]
       [--forearm Forearm] [--arm-names Clavicle,UpperArm,Forearm,Hand,...]
Token: a substring identifying the side in joint names (' L ' for 'Bip01 L Hand', '_L_' for 'B_L_Hand')."""
import argparse, json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from detached_parts_audit import closest_on_triangles

ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('out')
ap.add_argument('--side', action='append', required=True)
ap.add_argument('--hand-names', default='Hand,Finger,Thumb,Index,Middle,Ring,Pinky')
ap.add_argument('--forearm', default='Forearm')
ap.add_argument('--arm-names', default='Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky,Twist')
ap.add_argument('--fps', type=float, default=48.0)
ap.add_argument('--clips', default='')
ap.add_argument('--outer-only', action='store_true', help='test against outer body faces only (outer_surface.py)')
ap.add_argument('--exact', action='store_true', help='signed distance to the nearest triangle instead of the sparse '
                'samples (2026-10-30: on Yrsa\'s large skirt faces a sample a facet away read a clear hand as 6 cm inside)')
o = ap.parse_args()
glb = Glb(Path(o.glb)); model = Model(glb)
names = [n.get('name') for n in glb.json['nodes']]
idx = {n: i for i, n in enumerate(names)}
prim = model.primitives[0]
jn = [names[j] for j in model.joints]
# all primitives of the first mesh (body + head material) form one surface
P = model.primitives
tri_all, off = [], 0
dom_all, wsum_all = [], []
USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
for pr in [P[k] for k in USE]:
    tri_all.append(pr['triangles'] + off); off += len(pr['positions'])
    dom_all.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tri_all); dom = np.concatenate(dom_all)
hand_keys = o.hand_names.split(','); arm_keys = o.arm_names.split(',')
sides = dict(s.split('=', 1) for s in o.side)


def joints_of(tok, keys):
    return [j for j in jn if tok in j and any(k in j for k in keys)]


SID = {}
for s, tok in sides.items():
    hj = joints_of(tok, hand_keys); fj = joints_of(tok, [o.forearm]); aj = joints_of(tok, arm_keys)
    hv = np.isin(dom, hj); fv = np.isin(dom, fj); av = np.isin(dom, aj)
    body_f = ~(av[tris].any(1))
    he = np.unique(np.sort(np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), axis=1), axis=0)
    he = he[hv[he[:, 0]] & hv[he[:, 1]]]
    chains = sorted({j for j in hj if not j.endswith('Hand')})
    SID[s] = dict(hv=np.where(hv)[0], fv=np.where(fv)[0], body_f=np.where(body_f)[0], he=he, chains=chains)


def posed(clip, t):
    w = model.world(model.sample(clip, float(t)) if clip else {})
    sp = model.skinned_positions(w)
    out = [sp[k][0] for k in USE]
    return w, np.concatenate(out)


rw, rest = posed(None, 0)
if o.outer_only:                                    # a vest lining or the skin under a flap is not a surface to be inside of
    from outer_surface import outer_faces
    for d in SID.values():
        d['body_f'] = d['body_f'][outer_faces(rest, tris, d['body_f'])]
BARY = np.array([[1 / 3, 1 / 3, 1 / 3], [0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6]])


def exact_depth(pts, X, faces):
    """depth (m, up to 6 cm) behind the nearest triangle of `faces`, by its face normal"""
    T = X[tris[faces]]
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=min(40, len(T)))
    near = near.reshape(len(pts), -1)
    q, _ = closest_on_triangles(np.repeat(pts, near.shape[1], 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, near.shape[1], 0) - q, axis=1).reshape(near.shape)
    best = d.argmin(1)
    rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    return np.where((side < 0) & (d[rows, best] <= 0.06), -side, 0.0)


def inside_depth(pts, X, faces):
    if o.exact:
        return exact_depth(pts, X, faces)
    T = X[tris[faces]]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    S = np.einsum('kb,fbc->fkc', BARY, T).reshape(-1, 3); N = np.repeat(n, len(BARY), 0)
    d, i = cKDTree(S).query(pts, distance_upper_bound=0.06)
    ok = np.isfinite(d)
    dep = np.zeros(len(pts))
    v = pts[ok] - S[i[ok]]
    behind = np.einsum('ij,ij->i', v, N[i[ok]]) < -0.7 * d[ok]
    dep[np.where(ok)[0][behind]] = d[ok][behind]
    return dep


def rot(m):
    u, _, vt = np.linalg.svd(m[:3, :3]); return u @ vt


def angle(a, b):
    r = a.T @ b; return float(np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1))))



import os
clip=os.environ['PCLIP']; fr=int(os.environ['PFRAME']); s=os.environ['PSIDE']; d=SID[s]
w,X=posed(clip, fr/o.fps)
for nm,vs in (('hand',d['hv']),('forearm',d['fv'])):
    pts=X[vs]; T=X[tris[d['body_f']]]
    a_,b_,c_=T[:,0],T[:,1],T[:,2]
    n=np.cross(b_-a_,c_-a_); n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
    dep=exact_depth(pts,X,d['body_f'])
    order=np.argsort(-dep)[:5]
    cent=(a_+b_+c_)/3; tree=cKDTree(cent)
    for i in order:
        if dep[i]<=0: break
        _,f=tree.query(pts[i]); F=d['body_f'][f]
        print('PROBE',nm,'vert',vs[i],'depth_cm',round(dep[i]*100,2),'joint',dom[tris[F][0]],dom[tris[F][1]],'at',np.round(pts[i],3))
