import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data
PARTS = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
hv = sorted({v for p in me.polygons if PARTS[part[p.index]] == 'Hand' for v in p.vertices})
co = np.array([tuple(mesh.matrix_world @ me.vertices[i].co) for i in hv])
for side, sx in (('Left', 1), ('Right', -1)):
    c = co[co[:, 0] * sx > 0]
    H = np.array(arm.matrix_world @ arm.data.bones[side + 'Hand'].head_local)
    F = np.array(arm.matrix_world @ arm.data.bones[side + 'ForeArm'].head_local)
    a = (H - F) / np.linalg.norm(H - F)
    s = (c - H) @ a
    print(side, 'wrist', H.round(3), 'forearm axis', a.round(3), 'verts', len(c), 's range', s.min().round(3), s.max().round(3))
    # cross-section component counts along s
    for t in np.arange(0.0, s.max(), 0.01):
        sl = c[np.abs(s - t) < 0.004]
        if len(sl) == 0: continue
        # cluster in the plane by single-link at 6 mm
        pts = sl - np.outer((sl - H) @ a, a)
        lab = -np.ones(len(pts), int); k = 0
        for i in range(len(pts)):
            if lab[i] >= 0: continue
            st = [i]; lab[i] = k
            while st:
                j = st.pop()
                for m in np.where((lab < 0) & (np.linalg.norm(pts - pts[j], axis=1) < 0.006))[0]:
                    lab[m] = k; st.append(m)
            k += 1
        cents = [pts[lab == q].mean(0) for q in range(k)]
        print('  s %.3f comps %d' % (t, k), ' '.join('(%+.3f,%+.3f,%+.3f)' % tuple(x) for x in cents))
