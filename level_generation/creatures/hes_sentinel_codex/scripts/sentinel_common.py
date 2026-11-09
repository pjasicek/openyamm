"""Shared helpers for the v2 (Meshy) turrets: import and orient the Smart Topology returns, connected components.

Orientation (Blender, metres): the barrels point along -y (the actor's front; glTF +z), the mount's bottom at z = 0,
the yaw axis (the turning ring's centre) at x = y = 0. HEIGHT is the whole turret's height with its mount."""
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = {'sentinel': 'meshy/sentinel_geometry_v1/model_urls_glb.glb'}
TURN = {'sentinel': -90.0}
HEIGHT = {'sentinel': 1.60}


def import_raw(name):
    """Fresh scene with the raw return joined into one object `name`, oriented, scaled, the base at z = 0 and the
    yaw axis at the origin (the centre of the ring's top band, found by ring_centre). Transforms applied."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, RAW[name]))
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
    me = obj.data
    co = np.array([v.co[:] for v in me.vertices])
    me.transform(Matrix.Rotation(np.radians(TURN[name]), 4, 'Z'))
    co = np.array([v.co[:] for v in me.vertices])
    scale = HEIGHT[name] / (co[:, 2].max() - co[:, 2].min())
    me.transform(Matrix.Scale(scale, 4))
    co = np.array([v.co[:] for v in me.vertices])
    cx, cy = ring_centre(co)
    me.transform(Matrix.Translation((-cx, -cy, -co[:, 2].min())))
    me.update()
    obj.name = me.name = name
    return obj


def ring_centre(co):
    """x, y centre of the pedestal: the middle of the bounding box of the vertices in the lowest 6 % of the height
    (the base plate / plinth), which is centred under the ring on both returns."""
    z0, z1 = co[:, 2].min(), co[:, 2].max()
    low = co[co[:, 2] < z0 + 0.06 * (z1 - z0)]
    return (low[:, 0].min() + low[:, 0].max()) / 2, (low[:, 1].min() + low[:, 1].max()) / 2


def component_labels(bm):
    """Connected component index per vertex of a bmesh."""
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
