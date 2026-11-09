"""Measure shell orientation and show which boot faces become lining."""
import json
from pathlib import Path
import sys

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_texture as texture
from thicken_trial import thicken

name = 'equipment_7item119'
bpy.ops.wm.open_mainfile(filepath=str(Path(texture.WORK) / f'{name}.blend'))
obj = bpy.data.objects[name]
bm = bmesh.new()
bm.from_mesh(obj.data)
seen, components = set(), []
for face in bm.faces:
    if face in seen:
        continue
    stack, faces = [face], []
    seen.add(face)
    while stack:
        current = stack.pop()
        faces.append(current)
        for edge in current.edges:
            for other in edge.link_faces:
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
    def volume():
        return sum(f.calc_area() * f.calc_center_median().dot(f.normal) / 3 for f in faces)
    before = volume()
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    components.append({'faces': len(faces), 'volume_before': before, 'volume_consistent': volume(),
                       'boundary_edges': sum(e.is_boundary for f in faces for e in f.edges)})
bm.free()
Path(texture.HERE, 'review/boot_shell_orientation.json').write_text(json.dumps(components, indent=2) + '\n')
obj = thicken(obj, 0.004, texture.DESIGNS[name]['lining'])
for index, material in enumerate(obj.data.materials):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1, 0, 0, 1) if index == 0 else (0, 0, 1, 1)
    output = nodes.new('ShaderNodeOutputMaterial')
    material.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
texture.pl.WORK = texture.WORK
texture.pl.export(obj, name + '_orientation_diagnostic')
