"""Shared Blender helpers of the MM8 props batch: the MM6 outdoor props library (read only, imported from
../../../mm6_new_sorpigal_3d/props/scripts/props_lib.py) with materials read from this batch's textures/, map units,
COLOR_0 tints and piece-wise decimation. Blender Z up; every prop is built around its base centre on the ground."""
import math
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
MM6_PROPS = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal_3d', 'props', 'scripts')
sys.path.insert(0, MM6_PROPS)
import props_lib as pl  # noqa: E402
import corpse_pose as cp  # noqa: E402

pl.TEX = os.path.join(HERE, 'textures')
TEX = pl.TEX
WORK = os.path.join(HERE, 'work')
UNITS_PER_METRE = 81.7
os.makedirs(WORK, exist_ok=True)


def units(value):
    """Map units to Blender metres."""
    return value / UNITS_PER_METRE


def material(name, texture, alpha=False, extras=None):
    return pl.material(name, texture, alpha=alpha, extras=extras)


def linear(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def colour(obj, tint=(1, 1, 1), rays=48, distance=0.3, strength=0.75, floor=True, power=1.0, alpha=None):
    """Vertex occlusion (props_lib) raised to `power`, times a linear tint, into the 'Color' attribute (COLOR_0)."""
    pl.vertex_occlusion(obj, rays=rays, distance=distance, strength=strength, floor=floor, alpha=alpha)
    attr = obj.data.color_attributes['Color']
    data = np.empty(len(attr.data) * 4, np.float32); attr.data.foreach_get('color', data)
    data = data.reshape(-1, 4)
    data[:, :3] = np.power(np.clip(data[:, :3], 0, 1), power) * np.array(tint, np.float32)
    attr.data.foreach_set('color', data.ravel())


def set_colour(obj, fn):
    """COLOR_0 from a per-vertex callable fn(index, co, current rgba) -> rgba (point domain)."""
    attr = obj.data.color_attributes['Color']
    data = np.empty(len(attr.data) * 4, np.float32); attr.data.foreach_get('color', data)
    data = data.reshape(-1, 4)
    for v in obj.data.vertices:
        data[v.index] = fn(v.index, v.co, data[v.index])
    attr.data.foreach_set('color', data.ravel())


def duplicate(obj, name):
    me = obj.data.copy(); new = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(new)
    new.matrix_world = obj.matrix_world.copy()
    return new


def loose_labels(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    label = np.full(len(bm.verts), -1); count = 0
    for v in bm.verts:
        if label[v.index] >= 0:
            continue
        stack = [v]; label[v.index] = count
        while stack:
            w = stack.pop()
            for e in w.link_edges:
                o = e.other_vert(w)
                if label[o.index] < 0:
                    label[o.index] = count; stack.append(o)
        count += 1
    bm.free()
    return label, count


def delete_verts(obj, mask):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if mask[v.index]], context='VERTS')
    bm.to_mesh(obj.data); bm.free()


def drop_small(obj, min_vertices):
    label, count = loose_labels(obj)
    sizes = np.bincount(label, minlength=count)
    delete_verts(obj, sizes[label] < min_vertices)


def decimate_pieces(obj, target, minimum, keep=None):
    """Decimate every loose piece toward one shared ratio, no piece below `minimum` triangles, so the total lands
    near `target` (small bones keep a shape instead of collapsing to shards). keep(part) -> True leaves a piece
    untouched (cheap long bones whose silhouette suffers first). Returns the joined object."""
    name = obj.name
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = list(bpy.context.selected_objects)
    counts = np.array([pl.triangles(p) for p in parts], float)
    kept = np.array([bool(keep and keep(p)) for p in parts])
    budget = target - counts[kept].sum()
    ratio = 1.0
    for _ in range(40):
        total = np.minimum(counts, np.maximum(minimum, counts * ratio))[~kept].sum()
        ratio *= budget / max(total, 1)
    for part, n, k in zip(parts, counts, kept):
        goal = int(n if k else min(n, max(minimum, n * ratio)))
        if goal < n:
            for o in bpy.data.objects:
                o.select_set(o is part)
            bpy.context.view_layer.objects.active = part
            mod = part.modifiers.new('D', 'DECIMATE'); mod.ratio = goal / n; mod.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=mod.name)
    out = pl.join(name, parts)
    cp.clean(out)
    return out


def triangulate(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='SHORT_EDGE')
    bm.to_mesh(obj.data); bm.free()


def ground(objects, z=0.0):
    """Move the objects together so their lowest vertex is at z."""
    zmin = min((o.matrix_world @ v.co).z for o in objects for v in o.data.vertices)
    for o in objects:
        o.location.z += z - zmin
    bpy.context.view_layer.update()


def apply_transforms(obj):
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def centre_xy(objects):
    lo, hi = pl.bounds(objects)
    for o in objects:
        o.location.x -= (lo.x + hi.x) / 2; o.location.y -= (lo.y + hi.y) / 2
    bpy.context.view_layer.update()


def smooth(obj, angle=None):
    for p in obj.data.polygons:
        p.use_smooth = True
    for name in ('sharp_edge', 'sharp_face'):           # left by the glTF import: they split the normals
        if angle is None and name in obj.data.attributes:
            obj.data.attributes.remove(obj.data.attributes[name])
    if angle is not None:
        for o in bpy.data.objects:
            o.select_set(o is obj)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def fix_winding(obj):
    """Flip every closed loose piece whose signed volume is negative (inside-out: the engine culls its front)."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    welded = bm.copy()
    bmesh.ops.remove_doubles(welded, verts=welded.verts, dist=1e-6)
    welded.verts.ensure_lookup_table()
    # pieces by connectivity over welded positions, mapped back to the original faces by face index
    welded.faces.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    seen, flips = set(), []
    for f in welded.faces:
        if f.index in seen:
            continue
        stack, piece = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); piece.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        closed = all(len(e.link_faces) == 2 for g in piece for e in g.edges)
        volume = sum(g.verts[0].co.dot(g.verts[1].co.cross(g.verts[2].co)) for g in piece
                     for _ in [0] if len(g.verts) == 3) / 6.0
        if closed and volume < 0:
            flips.extend(g.index for g in piece)
    welded.free()
    if flips:
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in flips])
        bm.to_mesh(obj.data)
    bm.free()
    return len(flips)


def export(objects, name):
    for o in objects:
        triangulate(o)
        flipped = fix_winding(o)
        if flipped:
            print('WINDING fixed', o.name, flipped, 'faces')
    path = os.path.join(WORK, f'{name}_export.glb')
    pl.export(objects, path)
    return path


# ---------------------------------------------------------------- organic shapes (carcass, carrion, trash heap)
def metaballs(name, elements, resolution=0.012, threshold=0.6):
    """Mesh from metaball elements: ('ball', centre, radius), ('capsule', a, b, radius) or
    ('ellipsoid', centre, radius, (sx, sy, sz), rotation_quaternion). Returns a mesh object (evaluated copy)."""
    from mathutils import Quaternion, Vector
    mb = bpy.data.metaballs.new(name)
    mb.resolution = resolution; mb.render_resolution = resolution; mb.threshold = threshold
    for e in elements:
        if e[0] == 'ball':
            el = mb.elements.new(type='BALL'); el.co = e[1]; el.radius = e[2]
        elif e[0] == 'capsule':
            a, b = Vector(e[1]), Vector(e[2])
            el = mb.elements.new(type='CAPSULE'); el.co = (a + b) / 2; el.radius = e[3]
            el.size_x = max((b - a).length / 2, 1e-4)
            el.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized())
        elif e[0] == 'ellipsoid':
            el = mb.elements.new(type='ELLIPSOID'); el.co = e[1]; el.radius = e[2]
            el.size_x, el.size_y, el.size_z = e[3]
            el.rotation = Quaternion(e[4]) if len(e) > 4 else Quaternion()
    meta = bpy.data.objects.new(name + '_meta', mb); bpy.context.scene.collection.objects.link(meta)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(meta.evaluated_get(depsgraph), depsgraph=depsgraph)
    bpy.data.objects.remove(meta); bpy.data.metaballs.remove(mb)
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    return obj


def displace(obj, amplitude, scale, seed=0, flatten_below=None):
    """Move vertices along their normals by Perlin noise (lumpy flesh, heaped debris)."""
    from mathutils import Vector, noise as mnoise
    offset = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    for v in obj.data.vertices:
        n = mnoise.noise(v.co / scale + offset) + 0.5 * mnoise.noise(v.co / (scale * 0.4) + offset * 2)
        v.co += v.normal * amplitude * n
        if flatten_below is not None and v.co.z < flatten_below:
            v.co.z = max(v.co.z, 0.0)
    obj.data.update()


def box_uv(obj, tile, seed=0):
    """Box projection texture coordinates (the dominant normal axis of each face), tile metres per texture repeat,
    a per-axis offset so the faces of different axes do not show the same texels."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uv = me.uv_layers[0].data
    offsets = [(0.13 + seed * 0.31, 0.57), (0.71, 0.29 + seed * 0.17), (0.41, 0.83)]
    for poly in me.polygons:
        n = poly.normal; axis = int(np.argmax(np.abs([n.x, n.y, n.z])))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            a, b = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][axis]
            uv[li].uv = (a / tile + offsets[axis][0], b / tile + offsets[axis][1])


def inside_mask(obj, shells, margin=0.0):
    """Per-vertex: inside any of the closed shell objects (nearest-surface normal test)."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(s, depsgraph) for s in shells]
    out = np.zeros(len(obj.data.vertices), bool)
    for v in obj.data.vertices:
        p = obj.matrix_world @ v.co
        for t in trees:
            loc, normal, _, dist = t.find_nearest(p)
            if loc is not None and (p - loc).dot(normal) < -margin:
                out[v.index] = True; break
    return out


def drop_hidden_pieces(obj, shells, fraction=0.97):
    """Delete loose pieces with at least `fraction` of their vertices inside the shells (bones buried in flesh)."""
    inside = inside_mask(obj, shells)
    label, count = loose_labels(obj)
    share = np.bincount(label, weights=inside, minlength=count) / np.maximum(np.bincount(label, minlength=count), 1)
    delete_verts(obj, (share >= fraction)[label])
    return int((share >= fraction).sum())


def tint_material(obj, name, tint):
    """Multiply COLOR_0 (point domain) by a linear tint on the vertices of the faces using material `name`."""
    index = next(i for i, m in enumerate(obj.data.materials) if m and m.name.split('.')[0] == name)
    verts = {v for p in obj.data.polygons if p.material_index == index for v in p.vertices}
    attr = obj.data.color_attributes['Color']
    data = np.empty(len(attr.data) * 4, np.float32); attr.data.foreach_get('color', data)
    data = data.reshape(-1, 4)
    idx = np.array(sorted(verts))
    data[idx, :3] *= np.array(tint, np.float32)
    attr.data.foreach_set('color', data.ravel())


def slice_top(obj, fraction, seed=0, tilt=0.15):
    """Torn, sliced flesh: vertices above a tilted, noisy plane at `fraction` of the object's height are pressed
    down onto it, so a lump gets a flat cut face with ragged edges instead of a round top."""
    from mathutils import Vector, noise as mnoise
    co = np.array([v.co[:] for v in obj.data.vertices])
    lo, hi = co.min(0), co.max(0)
    rng = np.random.default_rng(seed)
    gx, gy = rng.uniform(-tilt, tilt, 2)
    centre = (lo + hi) / 2
    size = np.ptp(co, 0).max()
    for v in obj.data.vertices:
        p = v.co
        cut = lo[2] + (hi[2] - lo[2]) * fraction + gx * (p.x - centre[0]) + gy * (p.y - centre[1])
        cut += 0.03 * size * mnoise.noise(p / (size * 0.15) + Vector((seed, 0, 0)))
        if p.z > cut:
            p.z = cut + (p.z - cut) * 0.08
    obj.data.update()
