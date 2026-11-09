"""Measure prepared meshes and connected components for geometry/material authoring."""
import json
from pathlib import Path

import bmesh
import bpy

project = Path(__file__).resolve().parents[1]
output = project / 'review' / 'geometry'
output.mkdir(exist_ok=True)
for path in (project / 'work/codex_tex').glob('*.blend'):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    obj = bpy.data.objects[path.stem]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    seen, components = set(), []
    for vertex in bm.verts:
        if vertex in seen:
            continue
        stack, vertices = [vertex], []
        seen.add(vertex)
        while stack:
            current = stack.pop()
            vertices.append(current)
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        components.append({'vertices': len(vertices),
                           'bounds': [[min(v.co[i] for v in vertices) for i in range(3)],
                                      [max(v.co[i] for v in vertices) for i in range(3)]]})
    obj.data.calc_loop_triangles()
    report = {'triangles': len(obj.data.loop_triangles), 'components': components,
              'boundary_edges': sum(edge.is_boundary for edge in bm.edges),
              'non_manifold_edges': sum(not edge.is_manifold for edge in bm.edges),
              'vertices': [list(vertex.co) for vertex in obj.data.vertices]}
    assert report['triangles'] > 0 and obj.data.uv_layers
    (output / f'{path.stem}.json').write_text(json.dumps(report, indent=2) + '\n')
    print(path.stem, report['triangles'], 'tris', len(components), 'components')
    bm.free()
