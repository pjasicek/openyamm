"""Author exact pilot helmet masks from its separate horn meshes; no generated alpha holes."""
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_texture as texture

name = 'equipment_item110'
folder = Path(texture.PAINT) / name
frame = json.loads((folder / 'views.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(Path(texture.WORK) / f'{name}.blend'))
obj = bpy.data.objects[name]
obj.data.materials.clear()
for label, colour in [('metal', (1, 0, 0, 1)), ('horn', (1, 1, 0, 1)), ('leather', (0, 1, 0, 1))]:
    material = bpy.data.materials.new(label)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = colour
    output = nodes.new('ShaderNodeOutputMaterial')
    material.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
    obj.data.materials.append(material)
bm = bmesh.new()
bm.from_mesh(obj.data)
seen, horns, bands = set(), 0, 0
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
    xs, zs = [v.co.x for v in vertices], [v.co.z for v in vertices]
    horn = len(vertices) > 100 and min(zs) > 0.35 and (min(xs) < -0.49 or max(xs) > 0.49)
    leather = len(vertices) == 112 and min(zs) > 0.39 and max(zs) < 0.56
    horns += int(horn)
    bands += int(leather)
    for v in vertices:
        for face in v.link_faces:
            face.material_index = 1 if horn else (2 if leather else 0)
assert horns == 2 and bands == 1, 'Review changed helmet component bounds before authoring masks'
bm.to_mesh(obj.data)
bm.free()
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.render.resolution_x = scene.render.resolution_y = frame['size']
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
camera = bpy.data.objects.new('mask_camera', bpy.data.cameras.new('mask_camera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = frame['scale']
for view, direction in texture.VIEWS.items():
    d = Vector(direction).normalized()
    camera.location = Vector(frame['centre']) + d * frame['scale'] * 4
    camera.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < 0.9 else 'Z').to_euler()
    scene.render.filepath = str(folder / f'mask_{view}.png')
    bpy.ops.render.render(write_still=True)
frame['mask_layout'] = 'individual'
frame['mask_authoring'] = 'Exact mesh materials: two horn components, one leather brow-band component; helmet/visor/mail and studs metal'
(folder / 'views.json').write_text(json.dumps(frame, indent=2) + '\n')
print('EXACT_HELMET_MASKS: two horn components, one leather brow band, iron body/visor/mail and metal studs')
