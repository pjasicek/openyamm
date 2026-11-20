"""Align the head-only Meshy model (meshy/head_model_v1, review 3) to our head: a similarity transform (scale, rotation,
translation). Start: scale from (hood top - nose tip) heights, nose tips coincide. Then ICP with scale: our front face
skin vertices (head faces, piece 0, in front of the ear line, chin to brow) against the model surface (nearest points),
trimmed to the 80 % closest pairs. Writes work/face_align.json (4x4 matrix model -> ours, rms mm) and renders an
overlay (ours grey, model wire) for the gate. Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
CO = np.array([tuple(v.co) for v in me.vertices])
head_v = sorted({i for p in me.polygons if hd[p.index] for i in p.vertices if pv[i] == 0})
H = CO[head_v]
face = H[(H[:, 1] < -0.06) & (H[:, 2] > 1.49) & (H[:, 2] < 1.62)]
our_nose = face[np.argmin(face[:, 1])]
our_top = CO[pv == 3][:, 2].max()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', 'head_model_v1', 'model_urls_glb.glb'))
hm = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
bpy.context.view_layer.update()
MC = np.array([tuple(hm.matrix_world @ v.co) for v in hm.data.vertices])
mtop = MC[:, 2].max()
band = MC[(MC[:, 2] > mtop - 0.75 * (mtop - MC[:, 2].min()) * 0.6) & (MC[:, 2] < mtop - 0.25)]
m_nose = band[np.argmin(band[:, 1])]
s = (our_top - our_nose[2]) / (mtop - m_nose[2])
T = np.eye(4); T[:3, :3] *= s; T[:3, 3] = our_nose - s * m_nose
print('INIT scale', round(s, 4), 'model nose', m_nose.round(3), 'our nose', our_nose.round(3))
tris = []
me_m = hm.data; me_m.calc_loop_triangles()
P0 = MC
faces_m = [tuple(t.vertices) for t in me_m.loop_triangles]


def umeyama(A, B):
    """similarity transform taking A onto B (least squares)."""
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb
    U, S, Vt = np.linalg.svd(b.T @ a / len(A))
    D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ D @ Vt; sc = np.trace(np.diag(S) @ D) / (a ** 2).sum(1).mean()
    M = np.eye(4); M[:3, :3] = sc * R; M[:3, 3] = mb - sc * R @ ma
    return M


for it in range(40):
    Pm = (T[:3, :3] @ P0.T).T + T[:3, 3]
    tree = BVHTree.FromPolygons([Vector(p) for p in Pm], faces_m)
    near = []; d = []
    for p in face:
        loc, n, i, dist = tree.find_nearest(Vector(p))
        near.append(tuple(loc)); d.append(dist)
    near = np.array(near); d = np.array(d)
    keep = d < np.percentile(d, 80)
    # model points (in current placement) -> our points: update T by the correction mapping near -> face
    C = umeyama(near[keep], face[keep])
    T = C @ T
    rms = float(np.sqrt((d[keep] ** 2).mean()))
    if it % 10 == 0 or it == 39:
        print('ICP', it, 'rms mm', round(rms * 1000, 2), 'median mm', round(float(np.median(d)) * 1000, 2))
json.dump({'matrix': T.tolist(), 'rms_mm': rms * 1000, 'median_mm': float(np.median(d)) * 1000},
          open(os.path.join(HERE, 'work', 'face_align.json'), 'w'), indent=1)
# overlay render
hm.matrix_world = Matrix(T.tolist()) @ hm.matrix_world
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in (body, hm):
        o.hide_render = True
scene = bpy.context.scene; common.workbench_clay(scene)
hm.show_wire = True
common.render_views(os.path.join(HERE, 'review', 'face_align'), 1.55, 0.3, views=('front', 'left'), resolution=(600, 600))
print('ALIGNED')
