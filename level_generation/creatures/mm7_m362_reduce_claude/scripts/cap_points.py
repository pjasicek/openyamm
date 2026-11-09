"""Knitted-cap tip points for the LOD build (replaces the Swordsman's spike_points.py): LOD0 vertices of the cap above
REA_CAP_Z (default 1.70 m, only the cap reaches there): the highest one and, in three height bands, the outermost one in
four directions, so the coarse LODs keep the cap's curled tip and the picking height (playbook: thin top features vanish
in LOD3). Rest-pose positions read from the GLB as build_actor_lods.py sees them -> work/spike_points.json.
Usage: blender -b -P cap_points.py -- <lod0 glb>"""
import json, os, sys, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects[os.environ.get('REA_NODE', 'M362')]
v = np.array([(o.matrix_world @ x.co)[:] for x in o.data.vertices])
Z = float(os.environ.get('REA_CAP_Z', '1.70')); top = np.flatnonzero(v[:, 2] > Z)
pts = [v[top[np.argmax(v[top, 2])]]]
axis = v[top, :2].mean(0); zmax = v[top, 2].max()
for z0, z1 in ((Z, Z + (zmax - Z) / 3), (Z + (zmax - Z) / 3, Z + 2 * (zmax - Z) / 3), (Z + 2 * (zmax - Z) / 3, zmax + 1e-6)):
    band = top[(v[top, 2] >= z0) & (v[top, 2] < z1)]
    for dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if len(band):
            pts.append(v[band[np.argmax((v[band, :2] - axis) @ np.array(dv))]])
pts = np.unique(np.array(pts), axis=0)
json.dump(pts.tolist(), open(os.path.join(HERE, 'work', 'spike_points.json'), 'w'), indent=1)
print('CAP POINTS', len(pts), 'top z', round(float(zmax), 4), 'of', len(top), 'cap-top vertices')
