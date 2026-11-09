"""Render material IDs from reviewed equipment mesh parts, with exact guide silhouettes."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_texture as texture

project = Path(texture.HERE)
RECIPES = {
    '7item347': ('cloth', {1: 'metal'}),
    'item260': ('metal', {0: 'cloth', 2: 'gem', 3: 'gem', 4: 'gem', 10: 'gem'}),
    '6helm4': ('horn', {4: 'metal', 6: 'metal', 7: 'metal'}),
    '6helm5': ('metal', {4: 'gem'}),
    '7item098': ('metal', {}),
    '7item241': ('metal', {3: 'cloth'}),
    'item115': ('cloth', {}),
    'item256': ('cloth', {0: 'metal', 1: 'horn', 3: 'horn'}),
}


def components(mesh):
    seen, result = set(), []
    for vertex in mesh.verts:
        if vertex in seen:
            continue
        stack, group = [vertex], []
        seen.add(vertex)
        while stack:
            current = stack.pop()
            group.append(current)
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        result.append(group)
    return result


def crown_labels(obj, groups, frame, folder):
    """Use valid painted IDs to identify separate small jewel parts; retain the measured votes for review."""
    original = folder / 'before_geometry_material_ids'
    frame = json.loads((original / 'views.json').read_text())
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    votes = np.zeros((len(groups), len(texture.masks.NAMES)))
    for view, direction in texture.VIEWS.items():
        mask = texture.load_view(str(original), 'mask', view, frame.get('mask_layout', 'atlas_3x2') == 'atlas_3x2')
        guide = texture.load_rgba(str(folder / f'guide_{view}.png'))
        gx0, gx1, gy0, gy1 = texture.bbox(guide[..., 3])
        mx0, mx1, my0, my1 = texture.bbox(mask[..., 3])
        d, right, up = texture.view_frame(direction)
        for index, group in enumerate(groups):
            faces = {face for vertex in group for face in vertex.link_faces}
            for face in faces:
                normal = face.normal
                facing = normal.dot(d)
                if facing <= 0.05:
                    continue
                point = face.calc_center_median()
                if bvh.ray_cast(point + normal * 0.001 + d * 0.001, d)[0] is not None:
                    continue
                relative = point - Vector(frame['centre'])
                gx = (relative.dot(right) / frame['scale'] + 0.5) * frame['size'] - 0.5
                gy = (0.5 - relative.dot(up) / frame['scale']) * frame['size'] - 0.5
                x = int(np.clip(mx0 + (gx - gx0) / (gx1 - gx0) * (mx1 - mx0), 0, mask.shape[1] - 1))
                y = int(np.clip(my0 + (gy - gy0) / (gy1 - gy0) * (my1 - my0), 0, mask.shape[0] - 1))
                sample = mask[y, x]
                distances = np.sum((sample[:3] - texture.masks.PALETTE) ** 2, axis=-1)
                if sample[3] > 0.5 and distances.min() <= 0.501:
                    votes[index, distances.argmin()] += face.calc_area() * facing ** 2
    assert votes.sum() > 0
    return votes


labels_only = '--labels-only' in sys.argv
for icon in [arg for arg in sys.argv[sys.argv.index('--') + 1:] if arg != '--labels-only']:
    assert icon in RECIPES
    name = 'equipment_' + icon
    folder = Path(texture.PAINT) / name
    frame = json.loads((folder / 'views.json').read_text())
    backup = folder / 'before_geometry_material_ids'
    if not backup.exists():
        backup.mkdir()
        shutil.copyfile(folder / 'views.json', backup / 'views.json')
        for path in folder.glob('mask*.png'):
            shutil.copyfile(path, backup / path.name)
    bpy.ops.wm.open_mainfile(filepath=str(Path(texture.WORK) / f'{name}.blend'))
    obj = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    groups = components(bm)
    measured = json.loads((project / 'review/geometry' / f'{name}.json').read_text())['components']
    assert [len(group) for group in groups] == [group['vertices'] for group in measured], name
    votes = crown_labels(obj, groups, frame, folder) if icon == '7item098' else None
    default, overrides = RECIPES[icon]
    assignments = []
    for index, group in enumerate(groups):
        label = overrides.get(index, default)
        if votes is not None:
            label = texture.masks.NAMES[int(votes[index].argmax())] if votes[index].sum() else default
            assert label in ('metal', 'gem'), (icon, index, label)
        if icon == '7item241' and len(group) <= 8:
            label = 'gem'
        faces = {face for vertex in group for face in vertex.link_faces}
        for face in faces:
            face_label = label
            if icon == 'item115' and index == 0 and face.calc_center_median().z < 0.075:
                face_label = 'metal'
            face.material_index = texture.masks.NAMES.index(face_label)
        assignments.append({'component': index, 'vertices': len(group), 'label': label,
                            'votes': votes[index].tolist() if votes is not None else None})
    bm.to_mesh(obj.data)
    bm.free()
    indices = [face.material_index for face in obj.data.polygons]
    obj.data.materials.clear()
    for label, colour in zip(texture.masks.NAMES, texture.masks.PALETTE):
        material = bpy.data.materials.new('ID_' + label)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (*colour, 1)
        output = nodes.new('ShaderNodeOutputMaterial')
        material.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
        obj.data.materials.append(material)
    for face, index in zip(obj.data.polygons, indices):
        face.material_index = index
    assert [face.material_index for face in obj.data.polygons] == indices
    assert len(set(indices)) >= 2, (icon, 'mixed materials collapsed to one class')
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 1
    scene.render.resolution_x = scene.render.resolution_y = frame['size']
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    camera = bpy.data.objects.new('material_ID_camera', bpy.data.cameras.new('material_ID_camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = frame['scale']
    for view, direction in ([] if labels_only else texture.VIEWS.items()):
        d = Vector(direction).normalized()
        camera.location = Vector(frame['centre']) + d * frame['scale'] * 4
        camera.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < 0.9 else 'Z').to_euler()
        scene.render.filepath = str(folder / f'mask_{view}.png')
        bpy.ops.render.render(write_still=True)
    frame.update(mask_layout='individual', mask_authoring='Reviewed mesh-part materials; exact geometry silhouettes',
                 material_classes_file='geometry_material_ids.json')
    (folder / 'views.json').write_text(json.dumps(frame, indent=2) + '\n')
    receipt = {'design': name, 'source_scene_sha256': hashlib.sha256(Path(texture.WORK, name + '.blend').read_bytes()).hexdigest(),
               'assignments': assignments, 'face_classes': indices,
               'band_override': 'metal below z=0.075' if icon == 'item115' else None}
    (folder / 'geometry_material_ids.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('EXACT_MATERIAL_IDS', icon, len(groups), 'parts', flush=True)
