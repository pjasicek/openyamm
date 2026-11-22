"""Find the mouth groove on the clean body piece: per-vertex concavity (umbrella Laplacian along the normal) in the
head front region; per azimuth slice around the head axis the most concave vertex. Prints the lip polyline and writes
work/lip.json (vertex indices in clean_v1 order)."""
import bpy, os, json, math, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
m = bpy.data.objects['Toad']
bm = bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table(); bm.normal_update()
d = np.load(os.path.join(HERE, 'work', 'pieces.npz')); lab = d['label']
co = np.array([v.co[:] for v in bm.verts]); nr = np.array([v.normal[:] for v in bm.verts])
conc = np.zeros(len(co))
for v in bm.verts:
    nb = [e.other_vert(v).index for e in v.link_edges]
    if nb:
        lap = co[nb].mean(0) - co[v.index]
        conc[v.index] = lap @ nr[v.index]
# smooth the concavity a little over neighbours
c2 = conc.copy()
for v in bm.verts:
    nb = [e.other_vert(v).index for e in v.link_edges]
    c2[v.index] = 0.5 * conc[v.index] + 0.5 * conc[nb].mean()
centre = np.array([0.0, -0.55, 0.60])
cand = (lab == 0) & (co[:, 1] < -0.40) & (co[:, 2] > 0.42) & (co[:, 2] < 0.78)
rel = co - centre
az = np.degrees(np.arctan2(rel[:, 0], -rel[:, 1]))     # 0 = straight ahead, +90 = character left (+x)
lip = []
for a0 in range(-100, 101, 5):
    s = cand & (np.abs(az - a0) < 2.5) & (nr[:, 2] > -0.6)
    # outward-facing surface only: normal points away from the head axis
    s &= (nr[:, 0] * rel[:, 0] + nr[:, 1] * rel[:, 1]) > 0.2
    idx = np.where(s)[0]
    if len(idx) == 0: continue
    k = idx[np.argmax(c2[idx])]
    lip.append(int(k))
    print(f'LIP az {a0:+4d} v {k:5d} co ({co[k,0]:+.3f},{co[k,1]:+.3f},{co[k,2]:.3f}) conc {c2[k]*1000:.2f}mm')
json.dump({'lip': lip}, open(os.path.join(HERE, 'work', 'lip.json'), 'w'))
