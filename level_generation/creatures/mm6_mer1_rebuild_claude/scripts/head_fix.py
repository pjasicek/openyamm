"""After finish_mer.py (UVs frozen; positions only): (1) prune_hidden.py left the head skin under the cap with a saw-tooth top edge, and
between its teeth and the cap's rim the dark inside of the cap showed (teeth over the forehead in the viewer). The skin's open top-edge
vertices (part 2, above SKIN_Z) are lifted 1.5 cm above the cap's lowest rim point at their angle and drawn 6 % toward the head axis, so the
edge sits inside the cap. (2) The eyeballs' corners poke through the lids as blue-grey specks: each eyeball (a small closed part 2 piece)
is shrunk about its centre by EYE_S. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
RIM_R, EYE_S = 0.022, 0.93
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.faces.layers.int['part']
SKIN_Z = 0.725                    # above the eyes (their lid openings are skin boundaries too, at z <= 0.712)
capv = np.array([tuple(v.co) for v in bm.verts if any(f[pl] == 3 for f in v.link_faces)])
cang = np.degrees(np.arctan2(capv[:, 0], capv[:, 1] - 0.03))
edge = [v for v in bm.verts if v.co.z > (SKIN_Z if v.co.y < 0.0 else 0.66) and any(f[pl] == 2 for f in v.link_faces) and
        any(e.is_boundary for e in v.link_edges) and all(f[pl] == 2 for f in v.link_faces)]
raised = 0; mx = 0.0
for v in edge:
    a_ = np.degrees(np.arctan2(v.co.x, v.co.y - 0.03))
    m = np.abs((cang - a_ + 180) % 360 - 180) < 15
    if not m.any(): continue
    zt = float(capv[m, 2].min()) + 0.015
    if v.co.z < zt < v.co.z + 0.035:          # only the teeth just under the rim
        mx = max(mx, zt - v.co.z); v.co.z = zt; raised += 1
        v.co.x *= 0.94; v.co.y = 0.03 + (v.co.y - 0.03) * 0.94
rim = edge
# eyeballs: connected components of part-2 faces whose size is under 4 cm
seen = set(); eyes = 0
for f in bm.faces:
    if f[pl] != 2 or f.index in seen: continue
    comp = []; st = [f]; seen.add(f.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.edges:
            for y in e.link_faces:
                if y[pl] == 2 and y.index not in seen: seen.add(y.index); st.append(y)
    vs = list({v for x in comp for v in x.verts}); Q = np.array([tuple(v.co) for v in vs])
    if np.ptp(Q, 0).max() < 0.04 and len(comp) > 20:
        c = Q.mean(0)
        for v in vs: v.co = Vector((c + (np.array(tuple(v.co)) - c) * EYE_S).tolist())
        eyes += 1
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEADFIX rim verts', len(rim), 'raised', raised, 'max cm', round(mx * 100, 2), 'eyeballs', eyes)
