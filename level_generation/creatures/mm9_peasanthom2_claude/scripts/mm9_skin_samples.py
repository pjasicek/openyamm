"""Pairs of MM9 skin texels at the same surface point: the MM9 mesh (converted ABC, the frame the body was fitted in)
sampled at 12 barycentric points per face; each sample's position and its colour in skin A and skin B (both skins share
one UV layout). Args (Blender): <mm9 glb> <skin a png> <skin b png> <out npy>  -> rows x y z rA gA bA rB gB bB (0..1)"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
ob = max((o for o in bpy.context.scene.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
arm = ob.parent
if arm and arm.animation_data:
    arm.animation_data.action = None
me = ob.data; M = np.array(ob.matrix_world)
me.calc_loop_triangles()
uvl = me.uv_layers[0].data
imgs = []
for p in a[1:3]:
    im = bpy.data.images.load(p); W, H = im.size
    imgs.append((np.array(im.pixels[:], np.float32).reshape(H, W, im.channels)[..., :3], W, H))
rng = np.random.default_rng(1)
rows = []
for t in me.loop_triangles:
    P = np.array([me.vertices[v].co for v in t.vertices]); P = P @ M[:3, :3].T + M[:3, 3]
    U = np.array([uvl[l].uv for l in t.loops])
    for _ in range(12):
        w = rng.dirichlet([1, 1, 1]); p = w @ P; u = w @ U
        cols = []
        for px, W, H in imgs:
            x = int(np.clip((u[0] % 1.0) * W, 0, W - 1)); y = int(np.clip((u[1] % 1.0) * H, 0, H - 1))
            cols += list(px[y, x])
        rows.append(list(p) + cols)
np.save(a[3], np.array(rows, np.float32))
print('SAMPLES', len(rows))
