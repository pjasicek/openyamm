"""Clean the five downloaded blasters and rest each on a stable supporting hull face."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import closest_point_on_tri

P = Path(__file__).resolve().parents[1]
OWN = {r['icon']: r for r in json.loads((P / 'ownership.json').read_text())}


def orient_closed_parts(bm):
    pending = set(bm.faces)
    corrected = 0
    while pending:
        seed = pending.pop()
        group, stack = {seed}, [seed]
        while stack:
            face = stack.pop()
            neighbors = {f for v in face.verts for f in v.link_faces if f in pending}
            pending -= neighbors
            group.update(neighbors)
            stack.extend(neighbors)
        edges = {e for f in group for e in f.edges}
        if any(len(e.link_faces) != 2 for e in edges):
            continue
        volume = sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)) for f in group)/6
        if volume < 0:
            bmesh.ops.reverse_faces(bm, faces=list(group))
            corrected += 1
    return corrected


def close_remaining(bm, uv, prior_uv):
    pending = {e for e in bm.edges if e.is_boundary}
    repaired = 0
    while pending:
        first = pending.pop()
        component, vertices = {first}, set(first.verts)
        while True:
            connected = {e for e in pending if any(v in vertices for v in e.verts)}
            if not connected:
                break
            component.update(connected)
            pending -= connected
            vertices.update(v for e in connected for v in e.verts)
        assert len(vertices) <= 64 and all(sum(e in component for e in v.link_edges) == 2 for v in vertices)
        ordered, previous = [next(iter(vertices))], None
        while True:
            nxt = next(e.other_vert(ordered[-1]) for e in ordered[-1].link_edges
                       if e in component and e.other_vert(ordered[-1]) != previous)
            if nxt == ordered[0]:
                break
            previous = ordered[-1]
            ordered.append(nxt)
        centre = sum((v.co for v in ordered), Vector()) / len(ordered)
        inner = [bm.verts.new(centre + (v.co-centre)*.35) for v in ordered]
        for v, old in zip(inner, ordered):
            prior_uv[v] = prior_uv[old]
        triangles = []
        for i in range(len(ordered)):
            j = (i+1) % len(ordered)
            triangles.extend([(ordered[i], ordered[j], inner[j]), (ordered[i], inner[j], inner[i])])
        left, right = 0, len(inner)-1
        while right-left > 1:
            triangles.append((inner[left], inner[left+1], inner[right]))
            left += 1
            if right-left > 1:
                triangles.append((inner[left], inner[right-1], inner[right]))
                right -= 1
        for triangle in triangles:
            face = bm.faces.new(triangle)
            for loop in face.loops:
                loop[uv].uv = prior_uv[loop.vert][0]
            repaired += 1
    return repaired


def settle(obj):
    obj.data.calc_loop_triangles()
    total = 0
    weighted = Vector()
    for tri in obj.data.loop_triangles:
        a, b, c = [obj.data.vertices[i].co for i in tri.vertices]
        volume = a.dot(b.cross(c)) / 6
        total += volume
        weighted += (a + b + c) / 4 * volume
    assert total > 0
    centre = weighted / total
    bm = bmesh.new()
    verts = [bm.verts.new(v.co) for v in obj.data.vertices]
    bmesh.ops.convex_hull(bm, input=verts, use_existing_faces=False)
    bm.normal_update()
    down = Vector((0, 0, -1))
    candidates = []
    for face in bm.faces:
        if face.normal.z >= -.65:
            continue
        a, b, c = [v.co for v in face.verts[:3]]
        projected = centre - face.normal * (centre - a).dot(face.normal)
        if (closest_point_on_tri(projected, a, b, c) - projected).length < 1e-5:
            candidates.append(face.normal.copy())
    assert candidates, 'No stable support below mass centre'
    normal = min(candidates, key=lambda n: n.angle(down))
    rotation = normal.rotation_difference(down).to_matrix()
    for v in obj.data.vertices:
        v.co = rotation @ v.co
    bm.free()
    return math.degrees(normal.angle(down))


def main():
    selected = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(OWN)
    for icon in selected:
        assert icon in OWN
        bpy.ops.wm.read_factory_settings(use_empty=True)
        source = P / 'meshy/meshy' / f'{icon}_textured_v1/model_urls_glb.glb'
        bpy.ops.import_scene.gltf(filepath=str(source))
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        assert objects
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        obj = bpy.context.object
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for v in obj.data.vertices:
            x, y, z = v.co
            v.co = (x, z, -y)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-7)
        boundary = [e for e in bm.edges if e.is_boundary]
        uv = bm.loops.layers.uv.active
        prior_uv = {v: [l[uv].uv.copy() for l in v.link_loops] for v in bm.verts}
        repairs = bmesh.ops.holes_fill(bm, edges=boundary, sides=0)['faces'] if boundary else []
        for face in repairs:
            for loop in face.loops:
                choices = prior_uv[loop.vert]
                assert choices
                loop[uv].uv = choices[0]
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        # Hole triangulation can duplicate an existing triangle; remove it before closing the small remainder.
        seen, duplicates = set(), []
        for face in bm.faces:
            key = frozenset(face.verts)
            if key in seen:
                duplicates.append(face)
            seen.add(key)
        if duplicates:
            bmesh.ops.delete(bm, geom=duplicates, context='FACES_ONLY')
        # Meshy sometimes attaches a zero-thickness triangular flap to a closed edge.
        flaps = [f for f in bm.faces if sum(e.is_boundary for e in f.edges) >= 2
                 and any(len(e.link_faces) > 2 for e in f.edges)]
        if flaps:
            bmesh.ops.delete(bm, geom=flaps, context='FACES_ONLY')
        ring_repairs = close_remaining(bm, uv, prior_uv)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        outward_parts = orient_closed_parts(bm)
        assert not any(e.is_boundary for e in bm.edges), (icon, 'unclosed holes')
        assert all(f.calc_area() > 1e-12 for f in bm.faces), (icon, 'degenerate face')
        bm.to_mesh(obj.data)
        bm.free()
        assert not obj.data.validate(verbose=True, clean_customdata=False), (icon, 'invalid mesh')
        if obj.data.has_custom_normals:
            obj.data.normals_split_custom_set([(0, 0, 0)] * len(obj.data.loops))
        angle = settle(obj)
        coords = np.array([v.co[:] for v in obj.data.vertices])
        lo, hi = coords.min(0), coords.max(0)
        coords -= [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]
        coords /= max(hi[0] - lo[0], hi[1] - lo[1])
        for v, co in zip(obj.data.vertices, coords):
            v.co = co
        for face in obj.data.polygons:
            face.use_smooth = True
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        obj.data.update()
        normals = [n.vector.copy() for n in obj.data.corner_normals]
        corrected = 0
        for face in obj.data.polygons:
            average = sum((normals[i] for i in face.loop_indices), Vector()) / len(face.loop_indices)
            if average.dot(face.normal) < .01:
                corrected += 1
                for i in face.loop_indices:
                    normals[i] = face.normal.copy()
        obj.data.normals_split_custom_set(normals)
        for m in obj.data.materials:
            m.use_backface_culling = True
        assert 100 < len(obj.data.polygons) < 15000
        assert abs(coords[:, 2].min()) < 1e-6
        assert all(0 <= value <= 1 for l in obj.data.uv_layers.active.data for value in l.uv)
        export = P / 'work/meshy' / f'{icon}_raw.glb'
        bpy.ops.export_scene.gltf(filepath=str(export), export_format='GLB', use_selection=True, export_yup=True)
        receipt = {'icon': icon, 'triangles': len(obj.data.polygons), 'support_rotation_degrees': angle,
                   'boundary_edges_repaired': len(boundary), 'closure_faces': len(repairs),
                   'nonplanar_closure_triangles': ring_repairs,
                   'duplicate_caps_removed': len(duplicates), 'zero_thickness_flaps_removed': len(flaps),
                   'inverted_closed_parts_corrected': outward_parts,
                   'corrected_corner_faces': corrected, 'dimensions': np.ptp(coords, axis=0).tolist()}
        (P / 'receipts' / f'{icon}_geometry.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print('PREPARED', icon, receipt, flush=True)


if __name__ == '__main__':
    main()
