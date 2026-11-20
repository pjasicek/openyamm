"""Shared helpers for the Custodian (Blender, metres). Orientation: the eye faces -y (the actor's front; glTF +z), up
+z, the creature's left +x; the SPHERE's centre at x = y = 0. Scale: the sphere 2.4 m across (concept brief: the
Terminator Unit body at x1.8). The raw return's eye direction is found by RAW_FACING (degrees about z to turn it to -y)."""
import os

import bpy
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = 'meshy/custodian_st_v1/model_urls_glb.glb'
RAW_FACING = float(os.environ.get('CUST_TURN', '0'))
SPHERE_D = 2.4


def path(*parts):
    return os.path.join(HERE, *parts)


def import_raw():
    """Fresh scene with the raw return joined into one object 'Custodian', turned by RAW_FACING, transforms applied
    (not yet scaled or centred: see normalise)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path(RAW))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    for o in list(bpy.context.scene.objects):
        if o is not obj:
            bpy.data.objects.remove(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.data.transform(Matrix.Rotation(np.radians(RAW_FACING), 4, 'Z'))
    obj.name = obj.data.name = 'Custodian'
    return obj


def component_labels(bm):
    bm.verts.ensure_lookup_table()
    labels = np.full(len(bm.verts), -1, int)
    current = 0
    for v in bm.verts:
        if labels[v.index] >= 0:
            continue
        stack = [v]; labels[v.index] = current
        while stack:
            w = stack.pop()
            for e in w.link_edges:
                u = e.other_vert(w)
                if labels[u.index] < 0:
                    labels[u.index] = current; stack.append(u)
        current += 1
    return labels
