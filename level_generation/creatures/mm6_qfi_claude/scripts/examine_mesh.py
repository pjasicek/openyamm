"""Mesh audit of work/step0.blend: every connected piece with its size and place, a colour-by-piece render and head /
hand close-ups. Writes work/pieces.json and review/examine_*.png."""
import bpy, bmesh, sys, json, math, colorsys
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step0.blend'))
ob = bpy.data.objects['Queen']
me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
label = np.full(len(bm.verts), -1)
pieces = []
for v in bm.verts:
    if label[v.index] >= 0:
        continue
    k = len(pieces); stack = [v]; label[v.index] = k; ids = []
    while stack:
        x = stack.pop(); ids.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0:
                label[w.index] = k; stack.append(w)
    pieces.append(ids)
co = np.array([tuple(v.co) for v in bm.verts])
info = []
for k, ids in enumerate(pieces):
    c = co[ids]
    info.append({'piece': k, 'verts': len(ids), 'centre': c.mean(0).round(3).tolist(),
                 'size': (c.max(0) - c.min(0)).round(3).tolist()})
info.sort(key=lambda r: -r['verts'])
(P / 'work' / 'pieces.json').write_text(json.dumps({'pieces': info, 'labels': label.tolist()}))
for r in info[:60]:
    print('PIECE', json.dumps(r))
# colour by piece (vertex colours -> attribute shown in workbench)
attr = me.color_attributes.new('piece', 'BYTE_COLOR', 'POINT')
rng = np.random.default_rng(3)
cols = {k: colorsys.hsv_to_rgb(rng.random(), 0.7, 0.95) for k in range(len(pieces))}
main = info[0]['piece']
for i in range(len(me.vertices)):
    c = (0.8, 0.8, 0.8) if label[i] == main else cols[label[i]]
    attr.data[i].color = (*c, 1.0)
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'VERTEX'
common.render_views(str(P / 'review' / 'examine_pieces'), 1.2, 2.6, views=('front', 'left', 'back'), resolution=(600, 900))
head_z = co[:, 2].max() - 0.3
common.render_views(str(P / 'review' / 'examine_head'), head_z, 0.75, views=('front', 'left', 'three_quarter'),
                    resolution=(600, 600))
for side, x in (('L', 1), ('R', -1)):
    hv = co[(co[:, 0] * x > 0.45)]
    c = hv.mean(0)
    common.render_views(str(P / 'review' / f'examine_hand{side}'), float(c[2]), 0.45, views=('front', 'left'),
                        resolution=(500, 500), target=(float(c[0]), float(c[1])))
