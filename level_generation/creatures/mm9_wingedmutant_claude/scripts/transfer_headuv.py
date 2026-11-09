"""Carry the HeadUV that the Meshy head retexture was painted on (work/head_v1.blend) over to a rebuilt body with the
same head geometry (rework 2026-10-30: the weight fix rebuilt graft/symmetrize; Smart UV packing is not repeatable,
so the HeadUV is copied face by face, matched by face centre, loop by vertex position).
Args: -- <uv source blend> <target blend> <out blend>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
SRC, TGT, OUT = a


def faces(me):
    hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
    return hd


bpy.ops.wm.open_mainfile(filepath=SRC)
me = bpy.data.objects['Body'].data
hd = faces(me)
uv = me.uv_layers['HeadUV'].data
src = {}
for p in me.polygons:
    if hd[p.index]:
        co = np.array([tuple(me.vertices[v].co) for v in p.vertices])
        src[tuple(np.round(co.mean(0), 5))] = (co, np.array([tuple(uv[l].uv) for l in p.loop_indices]))
bpy.ops.wm.open_mainfile(filepath=TGT)
body = bpy.data.objects['Body']; me = body.data
hd = faces(me)
if 'HeadUV' not in me.uv_layers:
    me.uv_layers.new(name='HeadUV')
uv = me.uv_layers['HeadUV'].data
keys = list(src)
ALLC = np.concatenate([v[0] for v in src.values()])
ALLU = np.concatenate([v[1] for v in src.values()])
K = np.array(keys)
n = miss = near = 0
worst = 0.0
for p in me.polygons:
    if not hd[p.index]:
        continue
    co = np.array([tuple(me.vertices[v].co) for v in p.vertices])
    k = tuple(np.round(co.mean(0), 5))
    if k not in src:                  # a seam face whose vertices were snapped onto the plane: nearest centre
        j = int(np.argmin(np.linalg.norm(K - co.mean(0), axis=1)))
        if np.linalg.norm(K[j] - co.mean(0)) > 1e-3:
            # last resort (faces reshaped by the weld): every loop takes the UV of the nearest source corner
            for li, c in zip(p.loop_indices, co):
                q = int(np.argmin(np.linalg.norm(ALLC - c, axis=1)))
                uv[li].uv = tuple(ALLU[q])
            miss += 1
            continue
        k = keys[j]; near += 1
    sco, suv = src[k]
    for li, c in zip(p.loop_indices, co):
        j = int(np.argmin(np.linalg.norm(sco - c, axis=1)))
        worst = max(worst, float(np.linalg.norm(sco[j] - c)))
        uv[li].uv = tuple(suv[j])
    n += 1
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEADUV-TRANSFER faces', n, 'by nearest centre', near, 'by nearest corner', miss, 'worst vertex match', worst)
