"""Import the Smart Topology GLB, normalise (1.578 m, soles z=0, faces -Y) and split into named parts."""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

NAMES = {4175: 'Body', 1387: 'Skirt', 910: 'Hair', 167: 'Belt', 87: 'Buckle', 106: 'MouthInner'}


def load(path):
    common.clear_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
    obj = next(o for o in bpy.data.objects if o.type == 'MESH')
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    co = np.array([tuple(v.co) for v in obj.data.vertices])
    s = 1.578 / (co[:, 2].max() - co[:, 2].min())
    obj.scale = (s, s, s)
    obj.location = (-(co[:, 0].max() + co[:, 0].min()) / 2 * s, -(co[:, 1].max() + co[:, 1].min()) / 2 * s, -co[:, 2].min() * s)
    bpy.ops.object.transform_apply(location=True, scale=True)
    obj.data.materials.clear()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = {}
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        c = np.array([tuple(v.co) for v in o.data.vertices])
        n = len(c)
        if n in NAMES:
            name = NAMES[n]
        elif n == 428:
            name = 'LegLeft' if c[:, 0].mean() > 0 else 'LegRight'
        elif n in (94, 91):
            name = 'EyeLeft' if c[:, 0].mean() > 0 else 'EyeRight'
        else:
            name = 'Junk'
        o.name = name; o.data.name = name
        for p in o.data.polygons:
            p.use_smooth = True
        parts.setdefault(name, []).append(o)
    return parts
