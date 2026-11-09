"""Shared helpers for the Harvester (Meshy route, after hes_turrets_claude/scripts/turret_common.py): import and
orient the Smart Topology return, connected components.

Orientation (Blender, metres): the drill points along -y (the actor's front; glTF +z), the tracks' bottom at z = 0,
x = y = 0 at the centre of the footprint (the bounding box of the lowest vertices). LENGTH is the whole machine's
length, drill tip to sprayer."""
import os

import bpy
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = 'meshy/harvester_st_v1/model_urls_glb.glb'
TURN = 90.0          # the raw return's drill points along -x (Blender, after the glTF import)
LENGTH = 9.8


def import_raw():
    """Fresh scene with the raw return as one object `harvester`, oriented, scaled, transforms applied."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, RAW))
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
    me.transform(Matrix.Rotation(np.radians(TURN), 4, 'Z'))
    co = np.array([v.co[:] for v in me.vertices])
    me.transform(Matrix.Scale(LENGTH / (co[:, 1].max() - co[:, 1].min()), 4))
    co = np.array([v.co[:] for v in me.vertices])
    z0 = co[:, 2].min()
    low = co[co[:, 2] < z0 + 0.04 * (co[:, 2].max() - z0)]
    cx, cy = (low[:, 0].min() + low[:, 0].max()) / 2, (low[:, 1].min() + low[:, 1].max()) / 2
    me.transform(Matrix.Translation((-cx, -cy, -z0)))
    me.update()
    obj.name = me.name = 'harvester'
    return obj


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
