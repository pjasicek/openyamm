"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector, kdtree
a_ = sys.argv[sys.argv.index('--') + 1:]
src_blend, job, out = a_[:3]
LAYER = a_[3] if len(a_) > 3 else 'UVMap'
BARY = bool(os.environ.get('BARY'))                 # barycentric UVs within the matched source triangle          # 'HeadUV': only the head faces, fitted to their own bbox
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.abspath(job), 'model_urls_glb.glb'))
src = max((o for o in bpy.data.objects if o not in before and o.type == 'MESH'), key=lambda o: len(o.data.polygons))
S = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
T = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
polys = [p for p in me.polygons if (hd[p.index] == 1) == (LAYER == 'HeadUV')]
# the body upload is the WHOLE mesh: fit on all of it (a box of the non-head faces is shorter when the scalp is in the
# head set - goblin: 196 mm mismatch); the head upload is the head faces alone
Tsub = T if LAYER == 'UVMap' and not os.environ.get('BODY_ONLY') else T[sorted({v for p in polys for v in p.vertices})]   # BODY_ONLY: grafted head not uploaded
if os.environ.get('FIT_SPAN'):                      # pm3: the body lost its old neck top after the upload; fit on
    scale = (Tsub[:, 0].max() - Tsub[:, 0].min()) / (S[:, 0].max() - S[:, 0].min())   # the arm span, feet aligned
    off = (Tsub.max(0) + Tsub.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale
    off[2] = Tsub[:, 2].min() - S[:, 2].min() * scale
    S = S * scale + off
else:
    scale = (Tsub.max(0) - Tsub.min(0)).max() / (S.max(0) - S.min(0)).max()
    S = S * scale + ((Tsub.max(0) + Tsub.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale)
suv = src.data.uv_layers.active.data
tree = kdtree.KDTree(len(src.data.polygons))
for p in src.data.polygons:
    tree.insert(Vector(S[list(p.vertices)].mean(0)), p.index)
tree.balance()
if LAYER not in me.uv_layers:
    me.uv_layers.new(name=LAYER)
tuv = me.uv_layers[LAYER].data
worst, mism = 0.0, 0
ds = []
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d); ds.append(d)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    if BARY and len(sco) == 3:                      # interpolate inside the matched triangle: a face subdivided after
        a_, b_, c_ = (np.array(x) for x in sco)       # the upload (pf4's sculpted chest) gets midpoint UVs, not corners
        ua, ub, uc = (np.array(tuple(suv[li].uv)) for li in sp.loop_indices)
        e0, e1 = b_ - a_, c_ - a_; d00, d01, d11 = e0 @ e0, e0 @ e1, e1 @ e1; den = d00 * d11 - d01 * d01
        for li, vi in zip(p.loop_indices, p.vertices):
            e2 = T[vi] - a_; d20, d21 = e2 @ e0, e2 @ e1
            v_ = (d11 * d20 - d01 * d21) / den; w_ = (d00 * d21 - d01 * d20) / den
            bc = np.clip(np.array([1 - v_ - w_, v_, w_]), 0, None); bc /= bc.sum()
            tuv[li].uv = tuple(bc[0] * ua + bc[1] * ub + bc[2] * uc)
        continue
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
ds = np.array(ds) * 1000
print('UVTRANSFER mismatch mm p50/p99', round(float(np.median(ds)), 2), round(float(np.percentile(ds, 99)), 2), 'faces > 2 mm', int((ds > 2).sum()), '> 5 mm', int((ds > 5).sum()))
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
