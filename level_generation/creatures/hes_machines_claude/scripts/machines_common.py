"""Shared helpers for the colony and Lattice machines (Meshy Smart Topology returns).

Orientation (Blender, metres): the front (the turret's muzzle; the cell's and conduit's face in the concept's main
view) along -y (glTF +z), the base at z = 0, the yaw axis (the base's centre) at x = y = 0."""
import os

import bpy
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = ('starport_turret', 'capacitor_column', 'throne_conduit')
RAW = {n: f'meshy/{n}_st_v1/model_urls_glb.glb' for n in NAMES}
TEX_RAW = {n: f'meshy/{n}_retexture_v1/model_urls_glb.glb' for n in NAMES}
# Front direction of the raw return (Blender axes after the glTF import) -> rotation about z (degrees) to -y.
TURN = {'starport_turret': 90.0, 'capacitor_column': 0.0, 'throne_conduit': 0.0}
HEIGHT = {'starport_turret': 1.60, 'capacitor_column': 3.00, 'throne_conduit': 6.00}
# Height band (fractions of the height) whose bounding-box centre is the yaw axis: the turret's gold ring, the cell's
# base, the conduit's core (its cables trail to one side, so its base is off-centre).
CENTRE_BAND = {'starport_turret': (0.33, 0.375), 'capacitor_column': (0.0, 0.06), 'throne_conduit': (0.4, 0.7)}


def import_glb(path):
    """Fresh scene with the GLB's meshes joined into one object, transforms applied, parents cleared."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, path))
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
    return obj


def orient(obj, name, turn=None):
    """Turn the front to -y, scale to HEIGHT, the base's bottom at z = 0, the base's centre at the origin."""
    me = obj.data
    me.transform(Matrix.Rotation(np.radians(TURN[name] if turn is None else turn), 4, 'Z'))
    co = np.array([v.co[:] for v in me.vertices])
    me.transform(Matrix.Scale(HEIGHT[name] / (co[:, 2].max() - co[:, 2].min()), 4))
    co = np.array([v.co[:] for v in me.vertices])
    cx, cy = base_centre(co, CENTRE_BAND[name])
    me.transform(Matrix.Translation((-cx, -cy, -co[:, 2].min())))
    me.update()
    obj.name = me.name = name
    return obj


def base_centre(co, band):
    """x, y centre of the bounding box of the vertices in the height band (fractions of the height)."""
    z0, z1 = co[:, 2].min(), co[:, 2].max()
    low = co[(co[:, 2] >= z0 + band[0] * (z1 - z0)) & (co[:, 2] <= z0 + band[1] * (z1 - z0))]
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
