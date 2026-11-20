"""Audit the read-only copied Smart Topology scenes and render six local painting guides."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import codex_texture as texture

reports = {}
only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
for name, design in texture.DESIGNS.items():
    if design['family'] != 'gauntlets':
        continue
    if only and name not in only:
        continue
    source = P / 'references/prepared_scenes' / f'{name}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    obj = bpy.data.objects.get(name)
    if obj is None:
        meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        assert len(meshes) == 1, name
        obj = meshes[0]
        obj.name = name
    if name in ('equipment_gontlet2', 'equipment_item128'):
        obj.data.transform(Matrix.Rotation(math.pi, 4, 'Y'))
        design['export_rest_x_degrees'] = -90
        registry = json.loads((P / 'designs.json').read_text())
        registry[name]['export_rest_x_degrees'] = -90
        (P / 'designs.json').write_text(json.dumps(registry, indent=2) + '\n')
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    boundary = sum(e.is_boundary for e in bm.edges)
    nonmanifold = sum(not e.is_manifold for e in bm.edges)
    junctions = [e for e in bm.edges if len(e.link_faces) > 2]
    if junctions:
        # Some generated plate seams share one edge between three panels; split panels before adding thickness.
        bmesh.ops.split_edges(bm, edges=junctions)
    assert all(e.is_manifold or e.is_boundary for e in bm.edges), name
    bm.to_mesh(obj.data)
    bm.free()
    if boundary or junctions:
        # Raw Meshy cuffs end in a zero-thickness shell; retain the opening with an inner wall and rim.
        extent = max(max(v.co[i] for v in obj.data.vertices) - min(v.co[i] for v in obj.data.vertices)
                     for i in range(3))
        bpy.context.view_layer.objects.active = obj
        obj.data.materials.clear()
        for label in ('Outer shell', 'Leather lining'):
            obj.data.materials.append(bpy.data.materials.new(label))
        modifier = obj.modifiers.new('Real cuff lining and rim', 'SOLIDIFY')
        modifier.solidify_mode = 'NON_MANIFOLD'
        modifier.thickness = extent * .008
        modifier.offset = -1
        modifier.use_even_offset = False
        modifier.thickness_clamp = .5
        modifier.nonmanifold_thickness_mode = 'FIXED'
        modifier.material_offset = 1
        modifier.material_offset_rim = 0
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    interior = obj.data.attributes.new('inner_wall', 'BOOLEAN', 'FACE')
    for polygon in obj.data.polygons:
        interior.data[polygon.index].value = polygon.material_index == 1
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bad = [e for e in bm.edges if not e.is_manifold]
    assert not bad, (name, len(bad), [(len(e.link_faces), [list(v.co) for v in e.verts]) for e in bad[:8]])
    assert all(f.calc_area() > 1e-10 for f in bm.faces), name
    reports[name] = {'triangles': len(bm.faces), 'boundary_edges': boundary,
                     'nonmanifold_edges': nonmanifold, 'copied_prepared_scene': True}
    bm.to_mesh(obj.data)
    bm.free()
    # Re-centre once after basis correction, before the common guide framing is recorded.
    low = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    high = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for vertex in obj.data.vertices:
        vertex.co -= shift
    # The selected Troll anatomy edit invalidates its previous UV layout.
    if boundary or junctions or name == 'equipment_item128':
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(island_margin=.015)
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/codex_tex' / f'{name}.blend'))
    texture.guides(name)
    target = P / 'receipts/gauntlet_geometry.json'
    previous = json.loads(target.read_text()) if target.exists() else {}
    target.write_text(json.dumps(previous | reports, indent=2) + '\n')
    print('AUDITED', name, reports[name], flush=True)
