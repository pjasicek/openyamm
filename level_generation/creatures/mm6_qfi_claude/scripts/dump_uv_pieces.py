"""For the texture compose step: the HeadUV triangles of the head mesh's separate pieces (horns, crown spikes, fangs:
every head-part piece except the largest), every head face's HeadUV triangle (side spikes joined to the skull are
told apart by colour in compose_qfi.py) and the UVMap triangles of the body's separate pieces (breast hooks,
studs), to work/uv_pieces.json {"head_spikes": [[[u, v] x3], ...], "body_pieces": [...]}."""
import bpy, bmesh, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
q = bpy.data.objects['Queen']; me = q.data
part = np.array([p.value for p in me.attributes['part'].data])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
label = np.full(len(bm.verts), -1); sizes = []
for v in bm.verts:
    if label[v.index] >= 0:
        continue
    k = len(sizes); st = [v]; label[v.index] = k; n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0:
                label[w.index] = k; st.append(w)
    sizes.append(n)
out = {'head_spikes': [], 'body_pieces': [], 'head_faces': []}
head_main = max({label[me.polygons[i].vertices[0]] for i in np.where(part == 1)[0]}, key=lambda k: sizes[k])
body_main = max({label[me.polygons[i].vertices[0]] for i in np.where(part == 0)[0]}, key=lambda k: sizes[k])
huv = me.uv_layers['HeadUV'].data; buv = me.uv_layers['UVMap'].data
for p in me.polygons:
    k = label[p.vertices[0]]
    if part[p.index] == 1:
        out['head_faces'].append([list(huv[li].uv) for li in p.loop_indices])
    if part[p.index] == 1 and k != head_main:
        out['head_spikes'].append([list(huv[li].uv) for li in p.loop_indices])
    elif part[p.index] == 0 and k != body_main:
        out['body_pieces'].append([list(buv[li].uv) for li in p.loop_indices])
(P / 'work' / 'uv_pieces.json').write_text(json.dumps(out))
print('PIECES head spike faces', len(out['head_spikes']), 'body piece faces', len(out['body_pieces']))
