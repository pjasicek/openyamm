"""Per texture set UV triangles of the locked layout (work/uv_v1.blend, uv_sorc.py): the body set (u 0..0.5 of the
upload square) and the head set (u 0.5..1), each rescaled to its own 0..1 square, glTF v-down, as
work/uv_body.npz and work/uv_head.npz with `uv` (M x 3 x 2) for gutter_fill.py and `garment` / `piece` / `zcm` (rest centre height, cm) per triangle
for the compose rasters. Args: none"""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_v1.blend'))
me = bpy.data.objects['Body'].data
uvd = me.uv_layers['UVMap'].data
hs = np.zeros(len(me.polygons), np.int32); me.attributes['headset'].data.foreach_get('value', hs)
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
for name, flag, du in (('body', 0, 0.0), ('head', 1, 0.5)):
    tris, gar, pie, zc = [], [], [], []
    for p in me.polygons:
        if hs[p.index] != flag:
            continue
        uv = np.array([tuple(uvd[li].uv) for li in p.loop_indices])
        uv = np.c_[(uv[:, 0] - du) * 2, 1 - uv[:, 1] * 2]
        tris.append(uv); gar.append(gv[p.vertices[0]]); pie.append(pc[p.vertices[0]])
        zc.append(min(254, int(round(p.center.z * 100))))
    tris = np.array(tris)
    np.savez(os.path.join(HERE, 'work', f'uv_{name}.npz'), uv=tris, garment=np.array(gar), piece=np.array(pie), zcm=np.array(zc))
    print('UVSET', name, len(tris), 'tris; uv range', np.round(tris.reshape(-1, 2).min(0), 3), np.round(tris.reshape(-1, 2).max(0), 3))
