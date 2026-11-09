import json
from pathlib import Path
import bpy
import bmesh

p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/st_v2_parts.blend'))
report = []
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    remaining = {e for e in bm.edges if e.is_boundary}
    while remaining:
        seed = remaining.pop()
        component, todo = {seed}, [seed]
        while todo:
            edge = todo.pop()
            for v in edge.verts:
                for neighbor in v.link_edges:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        todo.append(neighbor)
        points = {v for e in component for v in e.verts}
        report.append({'part': obj.name, 'edges': len(component),
                       'lo': [min(v.co[k] for v in points) for k in range(3)],
                       'hi': [max(v.co[k] for v in points) for k in range(3)],
                       'closed': all(sum(e in component for e in v.link_edges) == 2 for v in points)})
    bm.free()
(p / 'work/body_boundaries.json').write_text(json.dumps(report, indent=2) + '\n')
print('BOUNDARIES', json.dumps(report))
