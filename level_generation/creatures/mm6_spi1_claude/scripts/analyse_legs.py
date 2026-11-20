"""Measure the Smart Topology spider: body extents and the eight legs (angle clusters around the cephalothorax),
with hip / knee (highest point) / ankle / foot per leg. Writes work/legs.json. Run in Blender on the Meshy GLB."""
import bpy, json, os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(mesh.matrix_world @ v.co) for v in mesh.data.vertices])
co[:, 2] -= co[:, 2].min()
# body midline: per-y z extent near x=0
mid = co[np.abs(co[:, 0]) < 0.03]
prof = {}
for y in np.arange(-0.5, 0.5, 0.025):
    s = mid[(mid[:, 1] >= y) & (mid[:, 1] < y + 0.025)]
    if len(s):
        prof[round(float(y), 3)] = [round(float(s[:, 2].min()), 3), round(float(s[:, 2].max()), 3)]
print('PROFILE', json.dumps(prof))
# cephalothorax centre: guess from profile (front body part), refine as centroid of verts near midline y<0
ceph = mid[(mid[:, 1] < 0.0) & (mid[:, 1] > -0.25)]
c = np.array([0.0, float(np.median(ceph[:, 1])), float(np.median(ceph[:, 2]))])
print('CEPH', c.round(3).tolist())
d = co[:, :2] - c[:2]
r = np.linalg.norm(d, axis=1)
far = r > 0.16
ang = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))  # 0 = forward (-Y), + = left (+X)
hist, edges = np.histogram(ang[far], bins=72, range=(-180, 180))
print('HIST', hist.tolist())
