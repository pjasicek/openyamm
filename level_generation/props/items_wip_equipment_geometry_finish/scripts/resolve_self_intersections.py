"""Remove self-intersections left by collapse decimation of thin cloth folds (seen as tears under back-face culling).

An exact self-union keeps the outer surface and drops the parts of folds that pass through each other; the shape,
frame and silhouettes stay those of the painting guides, so the existing paintings still register. The scene is
re-unwrapped (the bake projects by world position, not by UV) and the prior scene is kept as *_pre_selfunion.blend.
Usage: blender --background --python resolve_self_intersections.py -- <icon> [...]"""
import math
import shutil
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
from repair_geometry import activate, apply  # noqa: E402


def edge_partner(edge):
    """Pair the faces of an edge where folds touch (an even number above two): sorted around the edge, the two faces
    bounding a wedge of material (normals pointing out of the wedge) belong to one fold; the better of the two
    alternating pairings wins."""
    a, b = (v.co for v in edge.verts)
    axis = (b - a).normalized()
    reference = None
    entries = []
    for face in edge.link_faces:
        d = face.calc_center_median() - a
        d = (d - axis * d.dot(axis)).normalized()
        if reference is None:
            reference, side = d, axis.cross(d)
        entries.append((math.atan2(d.dot(side), d.dot(reference)), face, d))
    entries.sort(key=lambda entry: entry[0])
    count = len(entries)
    best = None
    for start in (0, 1):
        pairs, score = [], 0.0
        for i in range(start, start + count, 2):
            (_, f, d), (_, g, e) = entries[i % count], entries[(i + 1) % count]
            # Inside a wedge of material each bounding face's normal points away from the other face.
            score -= f.normal.dot(e) + g.normal.dot(d)
            pairs.append((f, g))
        if best is None or score > best[0]:
            best = (score, pairs)
    return {face: other for f, g in best[1] for face, other in ((f, g), (g, f))}


def separate_touching_folds(obj):
    """Give each fold its own copy of the edges and vertices where it touches another (edges with 4+ faces)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    # A touching run of one edge between two merge points would keep one shared copy: give it a middle vertex.
    assert all(len(e.link_faces) % 2 == 0 for e in bm.edges), 'odd edge valence after self-union'
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if len(e.link_faces) > 2], cuts=1)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3 and any(
        len(e.link_faces) > 2 for e in f.edges)], quad_method='BEAUTY', ngon_method='BEAUTY')
    partners = {e: edge_partner(e) for e in bm.edges if len(e.link_faces) > 2}
    rebuilt = bmesh.new()
    mapping = {}
    for v in bm.verts:
        seen = set()
        for start in v.link_faces:
            if start in seen:
                continue
            todo, fan, copy = [start], [], rebuilt.verts.new(v.co)
            seen.add(start)
            while todo:
                face = todo.pop()
                mapping[face, v] = copy
                for e in face.edges:
                    if v not in e.verts:
                        continue
                    if len(e.link_faces) == 2:
                        others = [f for f in e.link_faces if f is not face]
                    else:
                        others = [partners[e][face]]
                    for other in others:
                        if other not in seen:
                            seen.add(other)
                            todo.append(other)
    faces = {}
    for face in bm.faces:
        key = frozenset(mapping[face, v] for v in face.verts)
        # Two coincident faces on the same vertex copies are a zero-thickness membrane where parts touch over an
        # area: both sides are internal, so the pair is dropped.
        if key in faces:
            faces[key] = None
        else:
            faces[key] = face
    for face in bm.faces:
        if faces[frozenset(mapping[face, v] for v in face.verts)] is face:
            rebuilt.faces.new([mapping[face, v] for v in face.verts]).smooth = face.smooth
    bm.free()
    rebuilt.to_mesh(obj.data)
    rebuilt.free()
    return len(partners)


def intersecting_faces(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    faces = set()
    for a, b in tree.overlap(tree):
        if not set(bm.faces[a].verts) & set(bm.faces[b].verts):
            faces.update((a, b))
    bm.free()
    return len(faces)


def main():
    for icon in sys.argv[sys.argv.index('--') + 1:]:
        name = 'equipment_' + icon
        scene = P / 'work/codex_tex' / f'{name}.blend'
        backup = scene.with_name(f'{name}_pre_selfunion.blend')
        if not backup.exists():
            shutil.copy2(scene, backup)
        bpy.ops.wm.open_mainfile(filepath=str(backup))
        obj = bpy.data.objects[name]
        before = intersecting_faces(obj)
        bounds_before = [tuple(min(v.co[i] for v in obj.data.vertices) for i in range(3)),
                         tuple(max(v.co[i] for v in obj.data.vertices) for i in range(3))]
        modifier = obj.modifiers.new('Resolve fold intersections', 'BOOLEAN')
        modifier.operation = 'UNION'
        modifier.solver = 'EXACT'
        modifier.operand_type = 'COLLECTION'
        modifier.collection = bpy.data.collections.new('empty_operand')
        modifier.use_self = True
        apply(obj, modifier)
        touching = separate_touching_folds(obj)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
        bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-7)
        bm.to_mesh(obj.data)
        bad = [e for e in bm.edges if not e.is_manifold]
        assert not bad, (icon, 'non-manifold after self-union', len(bad), sorted({len(e.link_faces) for e in bad}))
        bm.free()
        after = intersecting_faces(obj)
        activate(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=.012)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        obj.data.calc_loop_triangles()
        bounds_after = [tuple(min(v.co[i] for v in obj.data.vertices) for i in range(3)),
                        tuple(max(v.co[i] for v in obj.data.vertices) for i in range(3))]
        drift = max(abs(a - b) for lo, hi in zip(bounds_before, bounds_after) for a, b in zip(lo, hi))
        assert drift < 1e-3, (icon, 'self-union moved the silhouette', drift)
        bpy.ops.wm.save_as_mainfile(filepath=str(scene))
        print('SELF_UNION', icon, 'intersecting faces', before, '->', after, 'separated touching edges', touching, 'triangles',
              len(obj.data.loop_triangles), 'bounds drift', round(drift, 6), flush=True)


if __name__ == '__main__':
    main()
