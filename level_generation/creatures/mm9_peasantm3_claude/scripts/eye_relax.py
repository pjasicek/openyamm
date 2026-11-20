"""Relax the eye-socket plate of the head shell into the surrounding face (face fix, 2026-11-01; user: "2 eyebrows? and
like weird eye area?"). Meshy's head carries a recessed, flat plate round each eye, outlined by a step at the brows and
temples; lit from above it reads as a light goggle with a dark outline whatever the paint (checked with flat normal maps
and with the repainted albedo). One ellipse over both eyes (centre x 0, z 0.80; semi-axes 7.8 x 5 cm, env EYE_ELLIPSE=a,b,zc; the front of the face;
the nose bridge |x| < 1.3 cm below z 0.805 held fixed): the vertices are moved toward the membrane (harmonic) surface spanned by the ring outside the ellipse (Jacobi,
ITER passes, ring fixed), with weight 1 inside 65 % of the ellipse easing to 0 at its edge, times STRENGTH. Positions only: UVs, weights and topology are unchanged.
Args (Blender): <in blend> <out blend> [strength 0.85] [iterations 300]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
STR = float(a[2]) if len(a) > 2 else 0.85
ITER = int(a[3]) if len(a) > 3 else 300
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
hd = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# head shell only: the largest head part (the eyeball cups and hair are separate loose parts)
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
CO = np.array([v.co[:] for v in bm.verts])
face_v = {v.index for f in bm.faces if hd[f.index] for v in f.verts}
import os
SHELL_Z = float(os.environ.get('SHELL_Z', 0.75)); YF = float(os.environ.get('Y_FRONT', -0.04))   # PeasantDM2: 0.40, -0.08
shell_part = np.bincount([comp[i] for i in face_v if CO[i, 2] > SHELL_Z and CO[i, 1] < min(YF, -0.06)]).argmax()


def ss(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


x, y, z = CO[:, 0], CO[:, 1], CO[:, 2]
w = np.zeros(len(CO))
inside = np.zeros(len(CO), bool)
import os
A, B, ZC = (float(v) for v in os.environ.get('EYE_ELLIPSE', '0.078,0.05,0.80').split(','))
r = np.sqrt((x / A) ** 2 + ((z - ZC) / B) ** 2)
nose = (np.abs(x) < 0.013) & (z < ZC + 0.005)          # the nose bridge and nose stay (fixed, like the ring)
inside = (r < 1.0) & (y < YF) & (comp == shell_part) & ~nose
w = np.where(inside, ss((1.0 - r) / 0.35), 0)
idx = np.nonzero(inside)[0]
# biharmonic fill (2026-11-01, r14): a harmonic (membrane) fill left the region a flat plane that caught the viewer's
# light as a bright patch with a crease at its edge; the bilaplacian keeps the surrounding face's slope across the edge.
# Two rings outside the region stay fixed; gradient steps on |L^2 x|^2 (Jacobi-style, step 0.1).
ring1 = {e.other_vert(bm.verts[i]).index for i in idx for e in bm.verts[i].link_edges} - set(idx.tolist())
act = list(set(idx.tolist()) | ring1)
nbr = {i: [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges] for i in act}
H = CO.copy()
mode = os.environ.get('EYE_FILL', 'biharmonic')
for it in range(ITER):
    if mode == 'harmonic':
        H[idx] = np.array([H[nbr[i]].mean(0) for i in idx])
        continue
    L = np.zeros_like(H)
    for i in act:
        L[i] = H[nbr[i]].mean(0) - H[i]
    for i in idx:
        LL = L[nbr[i]].mean(0) - L[i]
        H[i] -= 0.25 * LL
P = CO + (H - CO) * (w * STR)[:, None]
moved = np.linalg.norm(P - CO, axis=1)
for i in idx:
    bm.verts[i].co = P[i]
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('EYERELAX', json.dumps({'verts': int(len(idx)), 'strength': STR, 'iterations': ITER,
                             'max_move_mm': round(float(moved.max()) * 1000, 2), 'mean_move_mm': round(float(moved[idx].mean()) * 1000, 2)}))
