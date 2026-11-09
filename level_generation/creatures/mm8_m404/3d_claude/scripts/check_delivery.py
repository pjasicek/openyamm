"""Check shipped-file structure and every animation's LOD0 contacts; coarser LODs get switch-distance review."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Matrix
p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/warrior_finished.blend'))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
bpy.context.view_layer.update()
ids = [v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value == 1]
adjacent = {i: set() for i in ids}
for edge in body.data.edges:
    a, b = edge.vertices
    if a in adjacent and b in adjacent:
        adjacent[a].add(b)
        adjacent[b].add(a)
seeds = []
remaining = set(ids)
while remaining:
    todo, group = [next(iter(remaining))], set()
    while todo:
        i = todo.pop()
        if i in group:
            continue
        group.add(i)
        todo.extend(adjacent[i] - group)
    remaining -= group
    if len(group) < 3:
        continue
    center = sum((body.data.vertices[i].co for i in group), start=body.data.vertices[next(iter(group))].co * 0) / len(group)
    index = min(group, key=lambda i: (body.data.vertices[i].co - center).length_squared)
    seeds.append(list(body.data.vertices[index].co))
config = json.loads((p / 'uv_ready.gates.json').read_text())
config['regions']['mantle'] = {'component_seeds': seeds}
config['regions']['loincloth'] = {'weights': ['B_Loincloth'], 'weight_min': .5}
config['props'][0]['file'] = 'export/mm8_m404_sword.glb'
for hand in config['props'][0]['hands']:
    if hand['side'] == 'R':
        hand['intervals'] = {'Death': [[0, .35]], 'Dead': []}
(p / 'delivery.gates.json').write_text(json.dumps(config, indent=2))
sys.path.insert(0, str(Path('level_generation/creatures/claude_shared/gates').resolve()))
import run_gates as gates
all_meshes = gates.load_meshes
gates.load_meshes = lambda glb: [m for m in all_meshes(glb) if m.label.endswith('/colour0')]
sys.argv = ['run_gates.py', '--', str(p / 'export/mm8_m404.glb'), '--config', str(p / 'delivery.gates.json'),
            '--out', str(p / 'review/delivery_gates')]
gates.main()
