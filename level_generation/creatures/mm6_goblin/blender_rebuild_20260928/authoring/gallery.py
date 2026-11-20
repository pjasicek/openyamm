"""Render all actions in eight directions from the current portable goblin asset."""
import hashlib
import json
import math
import time
import traceback

import bpy
import numpy as np
from mathutils import Vector

from mesh_tools import ROOT
import roundtrip

OUTPUT = ROOT / 'review/complete_gallery'
SOURCE = ROOT / 'delivery/mm6_goblin_textured_rigged.glb'
VIEWS = [('front', 'Front'), ('front_right', 'Front-right'), ('right', 'Right · sword side'),
         ('back_right', 'Back-right'), ('back', 'Back'), ('back_left', 'Back-left'),
         ('left', 'Left · free hand'), ('front_left', 'Front-left')]
ACTIONS = [('standing', 'Standing', 2., 24), ('walk', 'Walk', 1., 24), ('attack', 'Attack', .75, 24),
           ('hit', 'Hit', .75, 24), ('death', 'Death', .625, 48), ('corpse', 'Corpse', 1., 24),
           ('fidget', 'Fidget', .75, 24)]


def camera_basis(view_index, elevation):
    angle = view_index * math.tau / 8
    offset = Vector((-4 * math.sin(angle), -4 * math.cos(angle), 4 * math.tan(math.radians(elevation))))
    rotation = (-offset).to_track_quat('-Z', 'Y')
    return offset, rotation, np.asarray(rotation.to_matrix().transposed())


def prepare():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    roundtrip.import_latest(SOURCE, OUTPUT / 'roundtrip_validation.json')
    scene = bpy.data.scenes['GB15 Export validation']
    scene.render.resolution_x = scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.compression = 30
    scene.eevee.taa_render_samples = 64
    bpy.data.objects['GB15 Ground'].hide_render = False
    scene.camera.data.type = 'ORTHO'
    meshes = [obj for obj in scene.objects if obj.type == 'MESH' and obj.name != 'GB15 Ground']
    actions, boxes = [], {}
    for name, label, duration, fps in ACTIONS:
        count = 1 if name == 'corpse' else round(duration * fps) + (1 if name == 'death' else 0)
        frames = [1 + index * 48 // fps for index in range(count)]
        actions.append({'id': name, 'label': label, 'duration': duration, 'fps': fps, 'frames': frames,
                        'frame_count': count, 'end_hold': .75 if name == 'death' else 0})
        boxes[name] = []
        for frame in frames:
            roundtrip.activate_import(name, frame)
            graph = bpy.context.evaluated_depsgraph_get()
            corners = []
            for obj in meshes:
                evaluated = obj.evaluated_get(graph)
                corners.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
            boxes[name].append(np.asarray(corners))
    groups = [('upright', ['standing', 'walk', 'attack', 'hit', 'fidget'], 10),
              ('fall', ['death'], 20), ('prone', ['corpse'], 35)]
    cameras, bounds = {}, {}
    for group, names, elevation in groups:
        points = np.concatenate([np.concatenate(boxes[name]) for name in names])
        low, high = points.min(axis=0), points.max(axis=0)
        center = np.array([0., (low[1] + high[1]) / 2, (low[2] + high[2]) / 2])
        extent = max(np.abs((points - center) @ camera_basis(index, elevation)[2].T)[:, :2].max()
                     for index in range(8))
        scale = math.ceil(extent * 2 * 1.09 * 100) / 100
        for name in names:
            cameras[name] = {'target': center.tolist(), 'scale': scale, 'elevation': elevation, 'group': group}
            bounds[name] = {}
            for index, (view, label) in enumerate(VIEWS):
                basis = camera_basis(index, elevation)[2]
                projected = np.concatenate([(box - center) @ basis.T for box in boxes[name]])
                minimum = float((.5 - np.abs(projected[:, :2]) / scale).min())
                assert minimum >= .04, (name, view, minimum)
                bounds[name][view] = {'minimum_frame_margin': minimum}
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    previous = OUTPUT / 'manifest.json'
    if previous.exists():
        assert json.loads(previous.read_text())['source_sha256'] == source_hash, 'Gallery source changed; use a new folder.'
    revision = json.loads((ROOT / 'delivery/manifest.json').read_text())['revision']
    manifest = {'revision': revision, 'source': '../../delivery/' + SOURCE.name,
                'source_sha256': source_hash, 'resolution': [960, 960], 'triangles': 12916,
                'views': [{'id': name, 'label': label, 'azimuth': index * 45} for index, (name, label) in enumerate(VIEWS)],
                'actions': actions, 'cameras': cameras, 'framing': bounds, 'clips': []}
    for action in actions:
        for view, label in VIEWS:
            folder = 'frames/' + revision + '/' + action['id'] + '/' + view
            (OUTPUT / folder).mkdir(parents=True, exist_ok=True)
            manifest['clips'].append({'action': action['id'], 'view': view, 'folder': folder,
                                      'video': 'videos/' + revision + '__' + action['id'] + '__' + view + '.mp4',
                                      'poster': folder + '/000.png', 'frame_count': action['frame_count']})
    (OUTPUT / 'videos').mkdir(exist_ok=True)
    previous.write_text(json.dumps(manifest, indent=2) + '\n')
    (OUTPUT / 'gallery-data.js').write_text('window.GOBLIN_GALLERY = ' + json.dumps(manifest) + ';\n')
    (OUTPUT / 'framing_validation.json').write_text(json.dumps({
        'status': 'pass', 'method': 'Evaluated mesh bounds at every rendered action pose, in all eight cameras.',
        'source_sha256': source_hash, 'fixed_camera_within_each_clip': True, 'views_mirrored': False,
        'cameras': cameras, 'clip_margins': bounds}, indent=2) + '\n')
    print('Prepared', len(manifest['clips']), 'clips;', sum(a['frame_count'] for a in actions) * 8, 'frames;', cameras)


def start(preflight=False):
    manifest = json.loads((OUTPUT / 'manifest.json').read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == manifest['source_sha256']
    scene = bpy.data.scenes['GB15 Export validation']
    actions = {item['id']: item for item in manifest['actions']}
    tasks = []
    for clip in manifest['clips']:
        action = actions[clip['action']]
        view_index = next(index for index, view in enumerate(manifest['views']) if view['id'] == clip['view'])
        indices = range(action['frame_count'])
        if preflight:
            if (clip['action'], clip['view']) not in [('walk', 'front'), ('attack', 'right'),
                                                     ('death', 'front_right'), ('corpse', 'back_left')]:
                continue
            indices = sorted({0, action['frame_count'] // 2, action['frame_count'] - 1})
        for index in indices:
            path = OUTPUT / clip['folder'] / (str(index).zfill(3) + '.png')
            if not path.exists():
                tasks.append((clip['action'], view_index, action['frames'][index], path))
    total, started = len(tasks), time.monotonic()
    status = OUTPUT / ('preflight_status.json' if preflight else 'status.json')
    status.write_text(json.dumps({'state': 'queued', 'remaining': total, 'total': total}))
    def step():
        try:
            if not tasks:
                status.write_text(json.dumps({'state': 'complete', 'rendered': total,
                                             'elapsed_seconds': time.monotonic() - started}))
                return None
            action, view_index, frame, path = tasks.pop(0)
            camera = manifest['cameras'][action]
            offset, rotation, basis = camera_basis(view_index, camera['elevation'])
            roundtrip.activate_import(action, frame)
            scene.camera.location = Vector(camera['target']) + offset
            scene.camera.rotation_euler = rotation.to_euler()
            scene.camera.data.ortho_scale = camera['scale']
            scene.render.filepath = str(path)
            status.write_text(json.dumps({'state': 'rendering', 'action': action,
                                         'view': manifest['views'][view_index]['id'], 'frame': frame,
                                         'remaining': len(tasks), 'total': total,
                                         'elapsed_seconds': time.monotonic() - started}))
            bpy.ops.render.render(write_still=True)
            return .03
        except Exception:
            status.write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None
    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', total, 'preflight renders' if preflight else 'gallery renders')
