"""Remove lining duplicated inside already closed fittings; preserve the connected glove/cuff lining."""
import json
from pathlib import Path

import bmesh
import bpy
import numpy as np

P = Path(__file__).resolve().parents[1]
records = {}
for path in sorted((P / 'work/codex_tex').glob('equipment_*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    obj = bpy.data.objects[path.stem]
    attribute = obj.data.attributes['inner_wall']
    inner = [v.value for v in attribute.data]
    before = np.array([v.co[:] for v in obj.data.vertices])
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    unseen = set(bm.faces)
    remove = []
    while unseen:
        seed = unseen.pop()
        part, pending = [seed], [seed]
        while pending:
            face = pending.pop()
            for edge in face.edges:
                for adjacent in edge.link_faces:
                    if adjacent in unseen:
                        unseen.remove(adjacent)
                        pending.append(adjacent)
                        part.append(adjacent)
        if all(inner[f.index] for f in part):
            assert all(e.is_manifold for f in part for e in f.edges), path.stem
            remove.extend(part)
    count = len(remove)
    if count:
        bmesh.ops.delete(bm, geom=remove, context='FACES')
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context='VERTS')
        assert all(e.is_manifold for e in bm.edges), path.stem
        bm.to_mesh(obj.data)
        after = np.array([v.co[:] for v in obj.data.vertices])
        assert np.allclose(before.min(0), after.min(0), atol=1e-6)
        assert np.allclose(before.max(0), after.max(0), atol=1e-6)
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
    bm.free()
    records[path.stem] = {'removed_hidden_triangles': count, 'remaining_triangles': len(obj.data.polygons)}
    print('HIDDEN SHELLS', path.stem, count, flush=True)
(P / 'receipts/removed_hidden_shells.json').write_text(json.dumps(records, indent=2) + '\n')
