"""Review Joe's existing stall and planned absence notice without changing active geometry."""
import json
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parent
VERSION = globals().get('REVIEW_VERSION', 'joe_notice_study_v1')
OUTPUT = PROJECT/'review'/VERSION
OUTPUT.mkdir(parents=True, exist_ok=True)
previous_scene = bpy.context.window.scene
path = PROJECT/'author_architecture.py'
definitions, _ = path.read_text().split('\nauthor = Author()\n', 1)
namespace = {'__file__': str(path), '__name__': 'mm5_joe_study_author'}
exec(compile(definitions, str(path), 'exec'), namespace)
spec = namespace['SPEC']
spec['buildings'] = [b for b in spec['buildings'] if b['id'] == 'joe']
spec['props'], spec['gates'] = [], []
namespace.update({'SCENE_NAME': 'MM5 Joe notice study', 'SOURCE': OUTPUT, 'MODELS': OUTPUT/'models'})
author = namespace['Author']()
author.building(spec['buildings'][0])
renderer = PROJECT/'render_architecture.py'
exec(compile(renderer.read_text(), str(renderer), 'exec'), {
    '__file__': str(renderer), '__name__': '__main__', 'REVIEW_VERSION': VERSION,
    'REVIEW_SCENE': author.scene.name, 'REVIEW_SPEC': spec, 'REVIEW_SEMANTIC': author.semantic,
    'REVIEW_IDS': ['joe'], 'REVIEW_TERRAIN': True,
})
(OUTPUT/'source.json').write_text(json.dumps({
    'building': spec['buildings'][0], 'geometry': author.metadata, 'semantic': author.semantic,
    'limits': 'Isolated source study; native appearance and click review remain required.',
}, indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'), {author.scene}, fake_user=True, compress=True)
bpy.context.window.scene = previous_scene
print({'study': str(OUTPUT), 'activeGeometryChanged': False})
