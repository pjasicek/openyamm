"""Per-domain UV raster (piece, rest position, normal, dominant bone, coverage) at 2048 (from mm8_m492_claude)."""
import bpy,sys,os,numpy as np
from pathlib import Path
HERE=str(Path(__file__).resolve().parents[1]);N=2048
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'work/textured_master.blend'))
for layer,slot in [('body',0),('head',1),('wings',2)]:
    b = bpy.data.objects['Body']; me = b.data
    co = np.array([tuple(v.co) for v in me.vertices])
    pv = np.zeros(len(co), np.int32); me.attributes['part'].data.foreach_get('value', pv)
    hd = np.array([f.material_index for f in me.polygons])
    names = [g.name for g in b.vertex_groups]
    dom = np.array([max(v.groups, key=lambda e: e.weight).group if len(v.groups) else -1 for v in me.vertices])
    uv = me.uv_layers.active.data
    piece = np.full((N, N), -1, np.int32); pos = np.zeros((N, N, 3), np.float32); bone = np.full((N, N), -1, np.int32)
    normal = np.zeros((N,N,3),np.float32); oral=np.zeros((N,N),bool); coverage=np.zeros((N,N),np.uint16)
    want_head = layer == 'head'
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        if hd[t.polygon_index] != slot:
            continue
        L = list(t.loops); V = list(t.vertices)
        P = np.array([tuple(uv[l].uv) for l in L]) * N
        x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, bb, c = P
        den = (bb[1] - c[1]) * (a[0] - c[0]) + (c[0] - bb[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((bb[1] - c[1]) * (xs - c[0]) + (c[0] - bb[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not m.any():
            continue
        iy = (N - 1 - (ys[m] - 0.5)).astype(int); ix = (xs[m] - 0.5).astype(int)    # image rows top-down
        piece[iy, ix] = pv[V[0]]
        inside=(w0>=1e-5)&(w1>=1e-5)&(w2>=1e-5)
        oy=(N-1-(ys[inside]-.5)).astype(int);ox=(xs[inside]-.5).astype(int);coverage[oy,ox]+=1
        normal[iy, ix] = me.polygons[t.polygon_index].normal[:]
        pos[iy, ix] = (w0[m, None] * co[V[0]] + w1[m, None] * co[V[1]] + w2[m, None] * co[V[2]])
        bone[iy, ix] = dom[V[np.argmax([w0[m].mean(), w1[m].mean(), w2[m].mean()])]]
    np.savez_compressed(os.path.join(HERE, 'work', f'uvraster_{layer}.npz'), piece=piece, pos=pos, bone=bone, normal=normal,
                        bone_names=np.array(names),oral=oral,coverage=coverage)
    print('RASTER', layer, N, 'covered', round(float((piece >= 0).mean()), 3), 'pieces', sorted(set(np.unique(piece)) - {-1}))
