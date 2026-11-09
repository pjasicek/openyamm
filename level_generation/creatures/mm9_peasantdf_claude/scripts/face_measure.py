"""Face width per height: our head skin shell vs MM9's face skin (diagnosis for the r6 temples/cheeks review). MM9 skin
faces are picked by their skin texel colour (warm hue, moderate saturation) on the MM9 skin; both front halves only
(Blender y < 0.0). Args: <blend> <mm9 glb> <mm9 skin png> <fit json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; M = body.matrix_world
move = Vector([x / 100.0 for x in json.load(open(a[3]))['joint_moves_xyz_cm']['Bip01 Head']])
me = body.data
hd = np.zeros(len(me.polygons), int); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), int); me.attributes['hand'].data.foreach_get('value', hn)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = {}; k = 0
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = k; st.append(o)
    k += 1
cnt = np.bincount(list(comp.values())); big = int(cnt.argmax())
ours = np.array([tuple(M @ me.vertices[i].co) for p in me.polygons if hd[p.index] and not hn[p.index]
                 for i in p.vertices if comp[bm.verts[i]] == big])
ex = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=a[1])
mm = max((o for o in bpy.data.objects if o not in ex and o.type == 'MESH'), key=lambda o: len(o.data.vertices))
img = bpy.data.images.load(a[2]); W_, H_ = img.size
px = np.empty(W_ * H_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H_, W_, 4)
uv = mm.data.uv_layers.active.data
pts = []
for p in mm.data.polygons:
    u = sum((uv[l].uv for l in p.loop_indices), Vector((0, 0))) / len(p.loop_indices)
    r, g, b = px[int((u.y % 1) * H_) % H_, int((u.x % 1) * W_) % W_, :3]
    mx, mn = max(r, g, b), min(r, g, b); s = (mx - mn) / max(mx, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    if 8 < hue < 35 and 0.2 < s < 0.6 and mx > 0.45:
        pts += [tuple(mm.matrix_world @ mm.data.vertices[i].co + move) for i in p.vertices]
mmp = np.array(pts)
cx = float(np.median(ours[:, 0]))
for z in (0.48, 0.46, 0.44, 0.42, 0.40, 0.38, 0.36):
    o = ours[(np.abs(ours[:, 2] - z) < 0.01) & (ours[:, 1] < 0.0)]; m = mmp[(np.abs(mmp[:, 2] - z) < 0.012) & (mmp[:, 1] < 0.0)]
    f = lambda q: round(float(np.abs(q[:, 0] - cx).max()), 3) if len(q) else None
    print('FACEW', z, 'ours', f(o), 'mm9', f(m), 'ours front y', round(float(o[:, 1].min()), 3) if len(o) else None,
          'mm9 front y', round(float(m[:, 1].min()), 3) if len(m) else None)
