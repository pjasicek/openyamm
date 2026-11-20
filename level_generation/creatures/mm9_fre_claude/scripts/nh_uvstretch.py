"""Pass 7: UV stretch (singular-value ratio) p50/p90/p99 of the face front and of all faces, and the face front's area spread. Args: <head_uv npz>"""
import sys
import numpy as np
d = np.load(sys.argv[1]); uv, tri, co, face, fp = d['uv'], d['tri'], d['co'], d['face'], d['fpiece']
def st(fs):
    out = []; ar = []
    for t in tri[fs]:
        p = co[t]; u = uv[t]; e1 = p[1] - p[0]; e2 = p[2] - p[0]; n = np.cross(e1, e2)
        if np.linalg.norm(n) < 1e-14: continue
        x = e1 / np.linalg.norm(e1); y = np.cross(n / np.linalg.norm(n), x)
        P = np.array([[e1 @ x, e2 @ x], [e1 @ y, e2 @ y]]); U = np.array([u[1] - u[0], u[2] - u[0]]).T
        if abs(np.linalg.det(P)) < 1e-14: continue
        s = np.linalg.svd(U @ np.linalg.inv(P), compute_uv=False)
        if s[1] > 0: out.append(s[0] / s[1]); ar.append(s[0] * s[1])
    ar = np.sqrt(np.array(ar)); return np.percentile(out, [50, 90, 99]).round(2), (np.percentile(ar, 90) / np.percentile(ar, 10)).round(2)
print('face front stretch p50/90/99, density p90/p10', *st(face & (fp == 0))); print('all', *st(np.ones(len(tri), bool)))
