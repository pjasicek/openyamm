"""Cut the remaining locally folded UV faces into planar charts without changing exported triangles."""
from collections import defaultdict
import json
import math

import bpy
import bmesh
from mathutils import Vector

from check_uv import intersection_area, cross
from mesh_tools import ROOT


def repair():
    objects = [o for o in bpy.data.collections['GB15 Character'].objects if o.type == 'MESH']
    triangles = []
    for obj in objects:
        uv = obj.data.uv_layers.active.data
        for poly in obj.data.polygons:
            loops = list(poly.loop_indices)
            pieces = [loops] if len(loops) == 3 else [loops[:3], [loops[0], loops[2], loops[3]]]
            for indices in pieces:
                triangles.append((obj.name, poly.index, [tuple(uv[i].uv) for i in indices]))
    cells, bad = defaultdict(list), defaultdict(set)
    tested = set()
    overlap_count = 0
    for index, (name, face, tri) in enumerate(triangles):
        for x in range(math.floor(min(p[0] for p in tri) * 128), math.floor(max(p[0] for p in tri) * 128) + 1):
            for y in range(math.floor(min(p[1] for p in tri) * 128), math.floor(max(p[1] for p in tri) * 128) + 1):
                for previous in cells[(x, y)]:
                    if (previous, index) in tested:
                        continue
                    tested.add((previous, index))
                    if intersection_area(tri, triangles[previous][2]) > 1e-10:
                        bad[name].add(face)
                        bad[triangles[previous][0]].add(triangles[previous][1])
                        overlap_count += 1
                cells[(x, y)].append(index)
    record = {'overlap_pairs_before': overlap_count, 'split_faces': {k: len(v) for k, v in bad.items()}}
    for name, indices in bad.items():
        obj = bpy.data.objects[name]
        bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
        layer = bm.loops.layers.uv.active
        selected = [bm.faces[i] for i in indices]
        targets = {f for f in selected if len(f.verts) == 3}
        result = bmesh.ops.triangulate(bm, faces=[f for f in selected if len(f.verts) > 3],
                                      quad_method='FIXED', ngon_method='BEAUTY')
        targets.update(result['faces'])
        for index, face in enumerate(targets):
            loops = list(face.loops)
            a, b, c = [loop.vert.co for loop in loops]
            ab, ac = b - a, c - a
            physical_area = ab.cross(ac).length / 2
            old_area = abs(cross(*[tuple(loop[layer].uv) for loop in loops])) / 2
            density = math.sqrt(max(old_area, 1e-10) / max(physical_area, 1e-10))
            x = ac.dot(ab.normalized())
            y = math.sqrt(max(1e-12, ac.length_squared - x * x))
            coords = [(0, 0), (ab.length, 0), (x, y)]
            for loop, coord in zip(loops, coords):
                loop[layer].uv = Vector(coord) * density + Vector((10 + index, 0))
                loop.edge.seam = True
        bm.to_mesh(obj.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, rotate_method='ANY', scale=True, margin_method='FRACTION',
                            margin=.004, shape_method='CONCAVE', merge_overlap=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    (ROOT / 'authoring/uv_repair.json').write_text(json.dumps(record, indent=2) + '\n')
    print(record)
