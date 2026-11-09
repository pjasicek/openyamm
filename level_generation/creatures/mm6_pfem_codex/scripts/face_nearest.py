"""Face colour by nearest surface point (review 3 follow-up: the ray-cast bake missed or hit the wrong surface where our
face geometry differs from the head model's - mouth folds, nostrils, temples - and left shards and holes). For every
head-set skin texel (work/uvraster_HeadUV.npz: piece 0, front, inside the face ellipse) the nearest point on the placed
head model (work/face_align.json) gives a UV in the model's layout; its base colour is sampled bilinearly. Writes
work/near_face_color.png (black elsewhere) and work/near_face_dist.npy (mm, for the compose step's mask).
Args: none"""
import bpy, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, *p)
FC, FR = (-0.007, 1.493), (0.085, 0.080)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=W('meshy', 'head_model_v1', 'model_urls_glb.glb'))
hm = next(o for o in bpy.data.objects if o.type == 'MESH')
T = Matrix(json.load(open(W('work', 'face_align.json')))['matrix'])
bpy.context.view_layer.update()
M = T @ hm.matrix_world
me = hm.data; me.calc_loop_triangles()
V = [M @ v.co for v in me.vertices]
tris = list(me.loop_triangles)
tree = BVHTree.FromPolygons(V, [tuple(t.vertices) for t in tris])
uvl = me.uv_layers.active.data
img = bpy.data.images.load(W('meshy', 'head_model_v1', 'texture_urls_0_base_color.png'))
iw, ih = img.size
px = np.array(img.pixels[:], np.float32).reshape(ih, iw, 4)[..., :3]          # bottom-up rows, linear? (sRGB file)
R = np.load(W('work', 'uvraster_HeadUV.npz')); hp, hpos = R['piece'], R['pos']
N = hp.shape[0]
ef = np.hypot((hpos[..., 0] - FC[0]) / FR[0], (hpos[..., 2] - FC[1]) / FR[1])
sel = (hp == 1) & (hpos[..., 1] < -0.035) & (ef < 1.2)
out = np.zeros((N, N, 3), np.float32); dist = np.full((N, N), 1e9, np.float32)
ys, xs = np.nonzero(sel)
for y, x in zip(ys, xs):
    p = Vector(hpos[y, x].tolist())
    loc, n, fi, d = tree.find_nearest(p, 0.03)
    if loc is None:
        continue
    t = tris[fi]; a, b, c = (V[i] for i in t.vertices)
    # barycentric of loc in (a, b, c)
    v0, v1, v2 = b - a, c - a, loc - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-18:
        continue
    w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
    uv = uvl[t.loops[0]].uv * w0 + uvl[t.loops[1]].uv * w1 + uvl[t.loops[2]].uv * w2
    fx = uv.x * iw - 0.5; fy = uv.y * ih - 0.5
    x0 = int(math.floor(fx)) % iw; y0 = int(math.floor(fy)) % ih; x1 = (x0 + 1) % iw; y1 = (y0 + 1) % ih
    tx, ty = fx - math.floor(fx), fy - math.floor(fy)
    col = (px[y0, x0] * (1 - tx) * (1 - ty) + px[y0, x1] * tx * (1 - ty) + px[y1, x0] * (1 - tx) * ty + px[y1, x1] * tx * ty)
    out[y, x] = col; dist[y, x] = d * 1000
o = bpy.data.images.new('near_face_color', N, N, alpha=True)
rgba = np.concatenate([out, np.ones((N, N, 1), np.float32)], -1)[::-1]        # image rows top-down -> Blender bottom-up
o.pixels = rgba.ravel().tolist()
o.filepath_raw = W('work', 'near_face_color.png'); o.file_format = 'PNG'; o.save()
np.save(W('work', 'near_face_dist.npy'), dist)
print('NEARFACE texels', len(ys), 'median dist mm', round(float(np.median(dist[sel & (dist < 1e8)])), 2))
