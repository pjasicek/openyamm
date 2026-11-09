import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = L.rest_coords(body); lab = L.loose_parts(body.data)
shell = int(np.bincount(lab[co[:, 2] > 0.5]).argmax()) if False else None
# shell: part containing the nose tip (most forward vertex above 0.4)
cand = np.where((co[:, 2] > 0.40) & (co[:, 2] < 0.47))[0]
shell = lab[cand[np.argmin(co[cand, 1])]]
hair = lab[np.argmax(co[:, 2])]
xc = -0.0101
S = np.where(lab == shell)[0]
for z0 in np.arange(0.38, 0.52, 0.02):
    s = S[(co[S, 2] >= z0) & (co[S, 2] < z0 + 0.02)]
    for side in (-1, 1):
        q = s[np.sign(co[s, 0] - xc) == side]
        lat = np.abs(co[q, 0] - xc)
        top = q[np.argsort(-lat)[:4]]
        print(f'EAR z {z0:.2f} side {side:+d} lat max {lat.max():.3f} p80 {np.percentile(lat,80):.3f} top', [(round(abs(co[i,0]-xc),3), round(co[i,1],3)) for i in top])
H = np.where(lab == hair)[0]
for z0 in np.arange(0.38, 0.52, 0.02):
    s = H[(co[H, 2] >= z0) & (co[H, 2] < z0 + 0.02) & (co[H, 1] > -0.06) & (co[H, 1] < 0.06)]
    for side in (-1, 1):
        q = s[np.sign(co[s, 0] - xc) == side]
        if len(q): lat = np.abs(co[q, 0] - xc); print(f'HAIR z {z0:.2f} side {side:+d} lat min {lat.min():.3f} max {lat.max():.3f}')
