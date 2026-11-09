"""Remove detached cube-like fibre islands from the cloth-only Traveler's Cloak."""
import json
from pathlib import Path
import shutil

import bmesh
import bpy

project = Path(__file__).resolve().parents[1]
name = 'equipment_item122'
path = project / 'work/codex_tex' / f'{name}.blend'
backup = project / 'work/repairs' / f'{name}_before_fibre_cleanup.blend'
assert not backup.exists(), 'The recorded fibre cleanup already ran'
shutil.copy2(path, backup)
bpy.ops.wm.open_mainfile(filepath=str(path))
obj = bpy.data.objects[name]
bm = bmesh.new()
bm.from_mesh(obj.data)
seen, discarded = set(), []
for vertex in bm.verts:
    if vertex in seen:
        continue
    stack, component = [vertex], []
    seen.add(vertex)
    while stack:
        current = stack.pop()
        component.append(current)
        for edge in current.link_edges:
            other = edge.other_vert(current)
            if other not in seen:
                seen.add(other)
                stack.append(other)
    if len(component) <= 8:
        discarded.extend(component)
assert discarded and len(discarded) < len(bm.verts)
bmesh.ops.delete(bm, geom=discarded, context='VERTS')
bm.to_mesh(obj.data)
bm.free()
obj.data.calc_loop_triangles()
report = {'removed_vertices': len(discarded), 'remaining_triangles': len(obj.data.loop_triangles),
          'reason': 'Plain cloth has no hardware: retain the two large cloth/fold components; remove detached cube-like islands.',
          'backup': str(backup.relative_to(project))}
(project / 'review/traveler_fibre_cleanup.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('TRAVELER_FIBRES_CLEANED', report, flush=True)
