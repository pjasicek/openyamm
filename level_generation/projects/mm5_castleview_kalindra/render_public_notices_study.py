"""Blender MCP: isolated public notice placements; leave the compiling map unchanged."""
import hashlib
import importlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
VERSION = globals().get('REVIEW_VERSION', 'public_notices_v1')
OUTPUT = PROJECT / 'review' / VERSION
OUTPUT.mkdir(exist_ok=True)
sys.path.insert(0, str(PROJECT))
import author_public_notices
importlib.reload(author_public_notices)
previous = bpy.context.window.scene
path = PROJECT / 'author_architecture.py'
definitions, _ = path.read_text().split('\nauthor = Author()\n', 1)
namespace = {'__file__': str(path), '__name__': 'mm5_public_notices_study_author'}
exec(compile(definitions, str(path), 'exec'), namespace)
namespace.update({'SCENE_NAME': 'MM5 public notices study', 'SOURCE': OUTPUT, 'MODELS': OUTPUT / 'models'})
spec = namespace['SPEC']
spec['buildings'] = [entry for entry in spec['buildings'] if entry['id'] in author_public_notices.BOARDS]
spec['gates'], spec['props'] = [], []
for key in author_public_notices.PALETTE.values():
    art = OUTPUT / 'art' / (key + '.png')
    spec['materials'][key] = {'path': str(art), 'sha256': hashlib.sha256(art.read_bytes()).hexdigest()}
author = namespace['Author']()
for building in spec['buildings']:
    author.building(building)
renderer = PROJECT / 'render_architecture.py'
exec(compile(renderer.read_text(), str(renderer), 'exec'), {
    '__file__': str(renderer), '__name__': '__main__', 'REVIEW_VERSION': VERSION,
    'REVIEW_SCENE': author.scene.name, 'REVIEW_SPEC': spec, 'REVIEW_SEMANTIC': author.semantic,
    'REVIEW_IDS': list(author_public_notices.BOARDS), 'REVIEW_TERRAIN': True})
# Shift toward the civic display so the eye-height framing includes its full left edge.
building = next(entry for entry in spec['buildings'] if entry['id'] == 'mayor')
origin, tangent, outward = (building[key] for key in ['frontOrigin','frontTangent','frontOutward'])
position = [origin[i] - tangent[i]*200 + outward[i]*1200 for i in range(2)] + [building['padHeight']+176]
target = [origin[i] - tangent[i]*200 for i in range(2)] + [building['padHeight']+176]
for obj in author.scene.objects:
    if obj.get('levelgen_kind') == 'bmodel':
        obj.hide_render = obj.get('assembly_id') != 'mayor'
camera = author.scene.camera
camera.location = Vector(position) / namespace['SCALE']
camera.rotation_euler = (Vector(target) / namespace['SCALE']-camera.location).to_track_quat('-Z','Y').to_euler()
author.scene.render.filepath = str(OUTPUT / 'mayor_notice_frontage.png')
bpy.ops.render.render(write_still=True)
(OUTPUT / 'frontage_camera.json').write_text(json.dumps({
    'position':position,'target':target,'lens_mm':camera.data.lens,'image':'mayor_notice_frontage.png'},indent=2)+'\n')
for obj in author.scene.objects:
    if obj.get('levelgen_kind') == 'bmodel':
        obj.hide_render = False
(OUTPUT / 'source.json').write_text(json.dumps({
    'buildings': spec['buildings'], 'boards': author_public_notices.BOARDS,
    'geometry': author.metadata, 'semantic': author.semantic,
    'status': 'Isolated study; no canonical integration or native acceptance.'}, indent=2) + '\n')
bpy.data.libraries.write(str(OUTPUT / 'study.blend'), {author.scene}, fake_user=True, compress=True)
bpy.context.window.scene = previous
print('Public notices study saved; compiling source remains unchanged.')
