"""Blender MCP: fit original venue signs to the existing buildings in an isolated study."""
import hashlib
import importlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
VERSION = globals().get('REVIEW_VERSION', 'frontage_signs_v1')
OUTPUT = PROJECT / 'review' / VERSION
OUTPUT.mkdir(exist_ok=True)
sys.path.insert(0, str(PROJECT))
import author_frontage_signs
importlib.reload(author_frontage_signs)

previous = bpy.context.window.scene
path = PROJECT / 'author_architecture.py'
definitions, _ = path.read_text().split('\nauthor = Author()\n', 1)
namespace = {'__file__': str(path), '__name__': 'mm5_frontage_signs_study_author'}
exec(compile(definitions, str(path), 'exec'), namespace)
namespace.update({'SCENE_NAME': 'MM5 frontage signs study', 'SOURCE': OUTPUT, 'MODELS': OUTPUT / 'models'})
spec = namespace['SPEC']
spec['buildings'] = [entry for entry in spec['buildings'] if entry['id'] in ['maps', 'crafts']]
spec['gates'], spec['props'] = [], []
for key in author_frontage_signs.PALETTE.values():
    art = OUTPUT / 'art' / (key + '.png')
    spec['materials'][key] = {'path': str(art), 'sha256': hashlib.sha256(art.read_bytes()).hexdigest()}

author = namespace['Author']()
for building in spec['buildings']:
    author.building(building)

renderer = PROJECT / 'render_architecture.py'
exec(compile(renderer.read_text(), str(renderer), 'exec'), {
    '__file__': str(renderer), '__name__': '__main__', 'REVIEW_VERSION': VERSION,
    'REVIEW_SCENE': author.scene.name, 'REVIEW_SPEC': spec, 'REVIEW_SEMANTIC': author.semantic,
    'REVIEW_IDS': ['maps', 'crafts'], 'REVIEW_TERRAIN': True})
# The standard close eye view crops the left craft sign. Keep it as a close view,
# and add a wider frontal view that can establish both entrances and sign positions together.
building = next(entry for entry in spec['buildings'] if entry['id'] == 'crafts')
x, y = building['frontOrigin']
z = building['padHeight']
outward = building['frontOutward']
position = (x + outward[0] * 1600, y + outward[1] * 1600, z + 176)
target = (x, y, z + 200)
for obj in author.scene.objects:
    if obj.get('levelgen_kind') == 'bmodel':
        obj.hide_render = obj.get('assembly_id') != 'crafts'
camera = author.scene.camera
camera.location = Vector(position) / namespace['SCALE']
camera.rotation_euler = (Vector(target) / namespace['SCALE'] - camera.location).to_track_quat('-Z', 'Y').to_euler()
author.scene.render.filepath = str(OUTPUT / 'crafts_frontage_wide.png')
bpy.ops.render.render(write_still=True)
(OUTPUT / 'wide_camera.json').write_text(json.dumps({
    'position': position, 'target': target, 'lens_mm': camera.data.lens,
    'image': 'crafts_frontage_wide.png', 'status': 'Source preview; not an in-game movement/collision check.'},
    indent=2) + '\n')
for obj in author.scene.objects:
    if obj.get('levelgen_kind') == 'bmodel':
        obj.hide_render = False
(OUTPUT / 'source.json').write_text(json.dumps({
    'buildings': spec['buildings'], 'geometry': author.metadata, 'semantic': author.semantic,
    'status': 'Isolated source study; canonical source/native map unchanged; native review still required.'},
    indent=2) + '\n')
bpy.data.libraries.write(str(OUTPUT / 'study.blend'), {author.scene}, fake_user=True, compress=True)
bpy.context.window.scene = previous
print('Frontage signs source study rendered; canonical native build inputs unchanged.')
