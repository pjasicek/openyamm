from pathlib import Path
import json
import bpy
import bmesh
from collections import Counter
from mathutils import Matrix

root = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root / 'source/walking_demon_master.blend'))
scene = bpy.context.scene
body = next(o for o in scene.objects if o.type == 'MESH' and o.get('material_role') == 'body')
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
for owner in scene.objects:
    for item in (owner, owner.data.shape_keys if owner.type == 'MESH' else None):
        if item and item.animation_data:
            item.animation_data.action = None
            for track in item.animation_data.nla_tracks:
                track.mute = True
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
mesh = body.data
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
remaining = set(bm.verts)
components = []
while remaining:
    queue = [next(iter(remaining))]
    component = set()
    while queue:
        vertex = queue.pop()
        if vertex in component:
            continue
        component.add(vertex)
        queue.extend(edge.other_vert(vertex) for edge in vertex.link_edges)
    remaining -= component
    ids = [v.index for v in component]
    groups = Counter()
    for index in ids:
        for group in mesh.vertices[index].groups:
            groups[body.vertex_groups[group.group].name] += group.weight
    components.append({'vertices': len(ids), 'faces': len({f for v in component for f in v.link_faces}),
        'bounds': [[min(v.co[k] for v in component) for k in range(3)], [max(v.co[k] for v in component) for k in range(3)]],
        'weights': groups.most_common(8), 'vertex_ids': ids})
report = {'scene': scene.name, 'objects': [{'name': o.name, 'type': o.type, 'role': o.get('material_role'),
    'parent': o.parent.name if o.parent else None, 'matrix': [list(row) for row in o.matrix_world],
    'vertices': len(o.data.vertices) if o.type == 'MESH' else None} for o in scene.objects],
    'body': body.name, 'rig': rig.name, 'materials': [m.name for m in mesh.materials],
    'components': sorted(components, key=lambda c: -c['vertices']),
    'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None,
        'head': list(b.head_local), 'tail': list(b.tail_local), 'deform': b.use_deform} for b in rig.data.bones],
    'actions': [{'name': t.name, 'strips': [{'action': s.action.name, 'range': list(s.action.frame_range)} for s in t.strips]} for t in rig.animation_data.nla_tracks]}
(root / 'work/source_inspection.json').write_text(json.dumps(report, indent=2) + '\n')
print('INSPECT', report['scene'], body.name, len(mesh.vertices), len(mesh.polygons), len(rig.data.bones))
for component in report['components']:
    print('COMP', component['vertices'], component['bounds'], component['weights'][:3])
bm.free()
