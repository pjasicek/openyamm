"""Remove degenerate geometry before rigging: merge coincident vertices (1e-6 m) and delete zero-area faces and
loose vertices. work/static_v3.blend -> work/static_v4.blend (work/clean_report.json)."""
import bpy, bmesh, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/static_v3.blend'))
me = bpy.data.objects['Body'].data; before = (len(me.vertices), len(me.polygons))
bm = bmesh.new(); bm.from_mesh(me)
merged = bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
zero = [f for f in bm.faces if f.calc_area() < 1e-12]; bmesh.ops.delete(bm, geom=zero, context='FACES')
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
co = np.array([v.co[:] for v in me.vertices]); e = np.array([ed.vertices[:] for ed in me.edges])
lengths = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
report = {'before_vertices_faces': before, 'after_vertices_faces': (len(me.vertices), len(me.polygons)),
          'zero_area_faces_removed': len(zero), 'loose_vertices_removed': len(loose), 'shortest_edge_m': float(lengths.min()),
          'edges_under_1e-5': int((lengths < 1e-5).sum())}
np.save(P / 'work/rest_co_v4.npy', co)
(P / 'work/clean_report.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/static_v4.blend')); print('CLEAN', report)
