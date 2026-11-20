"""Head profile ratios of the grafted head (head rework 2026-10-30), on the head-only Smart Topology in its raw frame
(beak toward -Y, crown +Z), midline silhouette (|x| < 2 % of the head width):
- beak length: gape corner (rear end of the mouth slit) -> beak tip;
- beak base depth: the midline silhouette's height 15 % of the beak length in front of the gape corner (just ahead of
  the nasal bristles, so the forehead feathers are not counted);
- head length: gape corner -> the back of the skull (behind the dome, where the dorsal profile has dropped to 80 % of
  its height above the gape).
Usage: blender -b -P head_profile_ratios.py -- <head glb> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
P = np.array([tuple(v.co) for v in bm.verts])
slit = np.array([tuple(v.co) for v in bm.verts if v.is_boundary])
tip = P[np.argmin(P[:, 1])]
gape_y = float(np.sort(slit[:, 1])[-6:].mean())
Lb = gape_y - tip[1]
width = np.ptp(P[:, 0])
mid = P[np.abs(P[:, 0]) < 0.02 * width]


def section(y, tol):
    m = np.abs(mid[:, 1] - y) < tol
    return mid[m, 2]


zs = section(gape_y - 0.15 * Lb, 0.02 * Lb)
depth = float(zs.max() - zs.min())
zg = float(section(gape_y, 0.02 * Lb).min())
ys = np.arange(gape_y, mid[:, 1].max(), 0.005)
top = np.array([section(y, 0.004).max() if len(section(y, 0.004)) else np.nan for y in ys])
peak = int(np.nanargmax(top))
thr = zg + 0.8 * (top[peak] - zg)
back = float(next((ys[i] for i in range(peak, len(ys)) if top[i] < thr), ys[-1]))
Lh = back - gape_y
rep = {'beak_len': float(Lb), 'head_len': float(Lh), 'beak_over_head': float(Lb / Lh), 'beak_base_depth': depth,
       'depth_over_beak': depth / float(Lb), 'gape_y': gape_y, 'skull_back_y': back, 'dome_y': float(ys[peak])}
json.dump(rep, open(a[1], 'w'), indent=1)
print('RATIOS', json.dumps(rep))
