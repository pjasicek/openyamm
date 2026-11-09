"""Close the two failed head exports without changing their framed design or paint references."""
import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import paint_meshy_head as painter

for name in sys.argv[sys.argv.index('--') + 1:]:
    path = P / 'work/codex_tex' / (name + '.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    obj = bpy.data.objects[name]
    before = [Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)]),
              Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])]
    if name == 'pole_7item063':
        # The skull has crossing internal sheets; a fine solid reconstruction removes those defects.
        painter.close_mesh(obj, volume_repair=True)
        decimate = obj.modifiers.new('skull_surface_budget', 'DECIMATE')
        decimate.ratio = min(1, 4000 / len(obj.data.polygons))
        decimate.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=decimate.name)
        after = [Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)]),
                 Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])]
        for vertex in obj.data.vertices:
            vertex.co = Vector([before[0][i] + (vertex.co[i] - after[0][i]) *
                                (before[1][i] - before[0][i]) / (after[1][i] - after[0][i]) for i in range(3)])
        with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=.698132, island_margin=.01)
            bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    boundary = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    remaining = [e for e in bm.edges if e.is_boundary]
    if remaining:
        assert name == 'pole_item050' and len(remaining) == 4
        verts = {v for e in remaining for v in e.verts}
        assert len(verts) == 4 and all(sum(v in e.verts for e in remaining) == 2 for v in verts)
        centre = bm.verts.new(sum((v.co for v in verts), Vector()) / 4 + Vector((0, 0, .0001)))
        for edge in remaining:
            bm.faces.new([edge.verts[0], edge.verts[1], centre])
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    from collections import Counter
    assert all(len(e.link_faces) == 2 for e in bm.edges), (name, Counter(len(e.link_faces) for e in bm.edges))
    bm.to_mesh(obj.data)
    bm.free()
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=.698132, island_margin=.01)
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    painter.pl.WORK = str(P / 'work/head_clay')
    painter.pl.export(obj, name)
    report = {'name': name, 'triangles': len(obj.data.polygons), 'framing': 'Original six-view frame retained exactly',
              'repair': 'fine volume reconstruction of crossed skull sheets' if name.endswith('063') else 'capped four-edge local hole',
              'boundary_edges_before_final_cap': len(boundary)}
    (P / 'receipts' / ('topology_repair_' + name + '.json')).write_text(json.dumps(report, indent=2) + '\n')
