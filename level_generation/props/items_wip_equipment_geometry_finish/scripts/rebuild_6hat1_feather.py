"""Cloth Hat (6hat1): replace Meshy's paper-thin feather ribbon, which passes through the crown and bakes as black
streaks, with a real tapered feather seated in the band; keep the cap body unchanged and merge the two with an exact
union (touching folds separated), then rebuild the painting guides.
Usage: blender --background --python rebuild_6hat1_feather.py"""
import math
import shutil
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import codex_texture as paint  # noqa: E402
from repair_geometry import activate, apply, closed_normals  # noqa: E402
from resolve_self_intersections import intersecting_faces, separate_touching_folds  # noqa: E402

NAME = 'equipment_6hat1'
# Spine from inside the band at the back right, rising and curling outward like the HD master's feather.
SPINE = [(0.25, -0.05, 0.17), (0.29, -0.08, 0.29), (0.34, -0.11, 0.41), (0.40, -0.14, 0.51), (0.46, -0.16, 0.58),
         (0.51, -0.16, 0.61), (0.545, -0.15, 0.595)]
WIDTH = 0.13
THICKNESS = 0.02
PLANAR_DEGREES = 4
CAP_TRIANGLES = 2500


def catmull_rom(points, samples):
    points = [Vector(p) for p in points]
    points = [points[0] * 2 - points[1]] + points + [points[-1] * 2 - points[-2]]
    result = []
    for segment in range(1, len(points) - 2):
        p0, p1, p2, p3 = points[segment - 1:segment + 3]
        for k in range(samples):
            t = k / samples
            result.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    result.append(points[-2])
    return result


def feather():
    spine = catmull_rom(SPINE, 3)
    ring = 6
    vertices, faces = [], []
    for i, point in enumerate(spine):
        t = i / (len(spine) - 1)
        tangent = (spine[min(i + 1, len(spine) - 1)] - spine[max(i - 1, 0)]).normalized()
        # The vane's flat side faces between the outside of the crown and the front view.
        outward = (Vector((point.x, point.y, 0)).normalized() + Vector((0, -1, 0))).normalized()
        across = tangent.cross(outward).normalized()
        face = across.cross(tangent).normalized()
        # The quill is narrow inside the band, the vane widest at a third and tapering to the curled tip.
        width = WIDTH * (0.18 + 0.82 * math.sin(math.pi * min(1.0, 0.12 + t * 1.05)) ** 0.7) * (1 - 0.85 * t ** 3)
        thickness = THICKNESS * (1 - 0.6 * t)
        for k in range(ring):
            a = 2 * math.pi * k / ring
            # A slight central rib: the vane is thicker at the quill line than at its edges.
            rib = 1 - 0.55 * abs(math.sin(a))
            vertices.append(point + across * (width / 2) * math.cos(a) + face * (thickness / 2) * math.sin(a) * rib)
    count = len(spine)
    for i in range(count - 1):
        for k in range(ring):
            a, b = i * ring + k, i * ring + (k + 1) % ring
            faces.append((a, b, b + ring, a + ring))
    faces.append(tuple(reversed(range(ring))))
    faces.append(tuple((count - 1) * ring + k for k in range(ring)))
    data = bpy.data.meshes.new('feather')
    data.from_pydata([tuple(v) for v in vertices], [], faces)
    data.update()
    obj = bpy.data.objects.new('feather', data)
    bpy.context.collection.objects.link(obj)
    closed_normals(obj, fill=False)
    return obj


def union_clean(obj):
    """Exact self-union, merge the boolean's near-coplanar cut fans, then give touching folds separate edges."""
    modifier = obj.modifiers.new('Union', 'BOOLEAN')
    modifier.operation = 'UNION'
    modifier.solver = 'EXACT'
    modifier.operand_type = 'COLLECTION'
    modifier.collection = bpy.data.collections.new('empty_operand')
    modifier.use_self = True
    apply(obj, modifier)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(PLANAR_DEGREES), verts=list(bm.verts), edges=list(bm.edges))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-7)
    bm.to_mesh(obj.data)
    bm.free()
    return separate_touching_folds(obj)


def main():
    scene = P / 'work/codex_tex' / f'{NAME}.blend'
    backup = scene.with_name(f'{NAME}_pre_feather.blend')
    if not backup.exists():
        shutil.copy2(scene, backup)
    bpy.ops.wm.open_mainfile(filepath=str(backup))
    obj = bpy.data.objects[NAME]
    bounds = [Vector([f(v.co[i] for v in obj.data.vertices) for i in range(3)]) for f in (min, max)]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    parts, seen = [], set()
    for start in bm.faces:
        if start in seen:
            continue
        todo, group = [start], []
        seen.add(start)
        while todo:
            face = todo.pop()
            group.append(face)
            for edge in face.edges:
                for other in edge.link_faces:
                    if other not in seen:
                        seen.add(other)
                        todo.append(other)
        parts.append(group)
    assert len(parts) == 2, len(parts)
    old_feather = min(parts, key=len)
    bmesh.ops.delete(bm, geom=old_feather, context='FACES')
    bm.to_mesh(obj.data)
    bm.free()
    # The union adds cut triangles where the brim, crown and feather cross; collapse the cap first so the result
    # stays near the budget (the union then removes any crossing the collapse introduces).
    obj.data.calc_loop_triangles()
    modifier = obj.modifiers.new('Cap budget', 'DECIMATE')
    modifier.ratio = CAP_TRIANGLES / len(obj.data.loop_triangles)
    modifier.use_collapse_triangulate = True
    apply(obj, modifier)
    new = feather()
    activate(obj)
    new.select_set(True)
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = NAME
    before = intersecting_faces(obj)
    touching = union_clean(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bad = [e for e in bm.edges if not e.is_manifold]
    assert not bad, ('non-manifold feather union', len(bad), sorted({len(e.link_faces) for e in bad}))
    bm.free()
    after = intersecting_faces(obj)
    activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=.012)
    bpy.ops.object.mode_set(mode='OBJECT')
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    new_bounds = [Vector([f(v.co[i] for v in obj.data.vertices) for i in range(3)]) for f in (min, max)]
    obj.data.calc_loop_triangles()
    bpy.ops.wm.save_as_mainfile(filepath=str(scene))
    print('FEATHER', 'removed', len(old_feather), 'faces; crossing faces', before, '->', after, 'touching edges',
          touching, 'triangles', len(obj.data.loop_triangles), 'bounds', [list(b) for b in bounds], '->',
          [list(b) for b in new_bounds], flush=True)
    paint.guides(NAME)


if __name__ == '__main__':
    main()
