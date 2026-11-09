"""Eye centres of the installed bloodsucker (rest pose): head faces of the reduction's Cand_45 (installed body UVs)
whose tier-A texel is the bright orange eye spot, one cluster per side -> work/eyes.json."""
import bpy, json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRE = os.path.dirname(HERE)
bpy.ops.wm.open_mainfile(filepath=os.path.join(CRE, 'mm6_bld_reduce_claude', 'work', 'ladder.blend'))
mesh = bpy.data.objects['Cand_45']
img = bpy.data.images.load(os.path.join(CRE, 'mm6_bld_claude', 'textures', 'bld_a_basecolor_graded.png'))
W, H = img.size
px = np.array(img.pixels[:]).reshape(H, W, 4)
gi = {g.name: g.index for g in mesh.vertex_groups}
head = {gi['Head'], gi['Neck2']}
uv = mesh.data.uv_layers.active.data
hits = []
for p in mesh.data.polygons:
    w = np.mean([sum(g.weight for g in mesh.data.vertices[v].groups if g.group in head) for v in p.vertices])
    if w < 0.5:
        continue
    for li in p.loop_indices:
        u, v = uv[li].uv
        r, g, b, _ = px[min(int(v * H), H - 1), min(int(u * W), W - 1)]
        if r > 0.6 and r > g + 0.12 and r > b + 0.1:
            hits.append(tuple(mesh.data.vertices[mesh.data.loops[li].vertex_index].co))
hits = np.array(hits)
eyes = []
for side in (1, -1):
    s = hits[hits[:, 0] * side > 0.005]
    if len(s):
        eyes.append({'centre': s.mean(0).round(4).tolist(), 'spread': float(np.linalg.norm(s - s.mean(0), axis=1).max().round(4)), 'n': len(s)})
json.dump(eyes, open(os.path.join(HERE, 'work', 'eyes.json'), 'w'), indent=1)
print('EYES', eyes)
