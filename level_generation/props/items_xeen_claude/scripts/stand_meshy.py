"""Stands a Meshy Smart Topology item (route meshy, lane S) the way build_xeen.py leaves its standing items (the jar,
the bell): Blender Z up, the front toward -Y (Meshy faces its master's camera), lowest point at 0, origin at the centre
of the footprint, longest horizontal side = the design's length (classify.py: a standing item takes the icon's width).
Cleaned to the modelling guidelines: welded, degenerate faces dissolved, loose shards below `min_part` faces removed
(Meshy's slivers), closed parts with a negative signed volume reversed (outward normals, the winding check's rule),
triangulated. Writes work/procedural/<d>.glb, which codex_texture.py prep unwraps like a procedural build (designs.json
`geometry: meshy_st`).
`hair_cap` (design_overrides.yml): Meshy's yarn hair came as a cloud of loose shards (slivers, half of them open sheets
the engine's back-face culling would hole): the shards are removed and the scalp they covered gets one solid lumpy cap
instead (the head's faces under the shards, subdivided once, pushed out to where the shards were with noise,
closed by an inner copy just under the scalp and a rim), which the paint carries as yarn.
Usage: blender --background --python stand_meshy.py -- <design> [...]"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCEDURAL = os.path.join(HERE, 'work', 'procedural')
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))


def islands(bm):
    seen, result = set(), []
    for face in bm.faces:
        if face.index in seen:
            continue
        stack, island = [face], []
        seen.add(face.index)
        while stack:
            current = stack.pop()
            island.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
        result.append(island)
    return result


def hair_cap(bm, cap, height):
    """Replaces the shard islands above cap['above'] x height (at most cap['max_faces'] faces each) by a cap."""
    bm.verts.index_update()
    bm.faces.index_update()
    shards = [island for island in islands(bm) if len(island) <= cap['max_faces']
              and min(v.co.z for face in island for v in face.verts) > cap['above'] * height]
    shard_faces = {face for island in shards for face in island}
    tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts],
                                [[v.index for v in face.verts] for face in shard_faces])
    bm.normal_update()
    reach, distance = cap['reach'], {}

    def scalp(face):
        # Above the shards' lowest point, and the face (front half, below the brow) stays bare.
        centre = face.calc_center_median()
        return face not in shard_faces and centre.z >= cap['above'] * height \
            and not (centre.z < cap['brow'] * height and face.normal.y < 0)
    for face in bm.faces:
        centre = face.calc_center_median()
        if not scalp(face):
            continue
        hit = tree.ray_cast(centre + face.normal * 0.01, face.normal, reach)
        if hit[0] is not None:
            distance[face] = hit[3]
    # Close pinholes: a face with two hair neighbours is hair too.
    for _ in range(2):
        for face in [f for f in bm.faces if f not in distance and scalp(f)]:
            if sum(1 for e in face.edges for other in e.link_faces if other in distance) >= 2:
                distance[face] = sorted(distance.values())[len(distance) // 2]
    patch = bmesh.new()
    copies = {}
    for face in distance:
        for v in face.verts:
            if v not in copies:
                copies[v] = patch.verts.new(v.co)
        patch.faces.new([copies[v] for v in face.verts])
    lift = {copies[v]: sum(distance[f] for f in v.link_faces if f in distance) /
            sum(1 for f in v.link_faces if f in distance) for v in copies}
    bmesh.ops.subdivide_edges(patch, edges=patch.edges[:], cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(patch, faces=patch.faces[:])
    patch.normal_update()
    # A closed shell: the lifted lumpy outer surface, an inner copy sunk just under the scalp, and a rim between them.
    shell, outer, inner = bmesh.new(), {}, {}
    for v in patch.verts:
        base = lift.get(v)
        if base is None:   # a subdivision vertex: the mean of its original neighbours
            near = [lift[e.other_vert(v)] for e in v.link_edges if e.other_vert(v) in lift]
            base = sum(near) / len(near) if near else cap['thickness']
        base = min(max(base * 0.85, cap['thickness'] * 0.6), cap['thickness'] * 1.2)
        lumps = 0.3 * noise.noise(v.co * cap['frequency']) + 0.2 * noise.noise(v.co * cap['frequency'] * 3.1)
        outer[v] = shell.verts.new(v.co + v.normal * base * (1 + lumps))
        inner[v] = shell.verts.new(v.co - v.normal * 0.4)
    for face in patch.faces:
        ring = list(face.verts)
        shell.faces.new([outer[v] for v in ring])
        shell.faces.new([inner[v] for v in reversed(ring)])
        for a, b in zip(ring, ring[1:] + ring[:1]):
            if len(patch.edges.get((a, b)).link_faces) == 1:
                shell.faces.new([outer[b], outer[a], inner[a], inner[b]])
    patch.free()
    bmesh.ops.triangulate(shell, faces=shell.faces[:])
    if sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)) for f in shell.faces) < 0:
        bmesh.ops.reverse_faces(shell, faces=shell.faces[:])
    mesh = bpy.data.meshes.new('hair_cap')
    shell.to_mesh(mesh)
    shell.free()
    bmesh.ops.delete(bm, geom=list(shard_faces), context='FACES')
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return len(shard_faces), len(distance)


def stand(design):
    entry = DESIGNS[design]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', 'meshy', f'{design}_st_v1', 'model_urls_glb.glb'))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bm = bmesh.new()
    for obj in meshes:
        part = bmesh.new()
        part.from_mesh(obj.data)
        part.transform(obj.matrix_world)
        mesh = bpy.data.meshes.new('part')
        part.to_mesh(mesh)
        part.free()
        bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.faces.index_update()
    removed, flipped = 0, 0
    for island in islands(bm):
        closed = all(edge.is_manifold for face in island for edge in face.edges)
        if len(island) < entry.get('min_part', 0):
            removed += len(island)
            bmesh.ops.delete(bm, geom=island, context='FACES')
        elif closed:
            # The winding check's rule: a closed part's signed volume must be positive (normals outward).
            volume = sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)) for f in island) / 6
            if volume < 0:
                bmesh.ops.reverse_faces(bm, faces=island)
                flipped += len(island)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    points = [v.co for v in bm.verts]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    scale = entry['length'] / max(hi.x - lo.x, hi.y - lo.y)
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in bm.verts:
        v.co = (v.co - shift) * scale
    cap = entry.get('hair_cap')
    if cap:
        removed_hair, capped = hair_cap(bm, cap, (hi.z - lo.z) * scale)
        removed += removed_hair
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
        print('HAIR CAP', design, removed_hair, 'shard faces removed,', capped, 'scalp faces capped')
    mesh = bpy.data.meshes.new(design)
    bm.to_mesh(mesh)
    bm.free()
    for obj in list(bpy.context.scene.objects):
        bpy.data.objects.remove(obj)
    obj = bpy.data.objects.new(design, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(entry.get('smooth_angle', 40)))
    mesh.calc_loop_triangles()
    size = (hi - lo) * scale
    os.makedirs(PROCEDURAL, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(PROCEDURAL, f'{design}.glb'), export_format='GLB',
                              use_selection=False, export_apply=True)
    report = {'triangles': len(mesh.loop_triangles), 'size': [round(v, 1) for v in size],
              'removed_shard_faces': removed, 'flipped_faces': flipped}
    print('STOOD', design, json.dumps(report))
    return report


def main():
    designs = sys.argv[sys.argv.index('--') + 1:]
    path = os.path.join(PROCEDURAL, 'built.json')
    reports = json.load(open(path)) if os.path.exists(path) else {}
    for design in designs:
        reports[design] = stand(design)
    with open(path, 'w') as handle:
        json.dump(reports, handle, indent=1, sort_keys=True)


main()
