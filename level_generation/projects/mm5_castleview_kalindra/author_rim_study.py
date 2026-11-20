"""Author original descending rock and explicit space-boundary faces in an isolated Blender scene."""
import hashlib
import json
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT/'review'/globals().get('REVIEW_VERSION', 'rim_geometry_study_v5')
plan = json.loads((OUTPUT/'plan.json').read_text())
previous_scene = bpy.context.window.scene
path = PROJECT/'author_architecture.py'
definitions, _ = path.read_text().split('\nauthor = Author()\n', 1)
namespace = {'__file__': str(path), '__name__': 'mm5_rim_study_author'}
exec(compile(definitions, str(path), 'exec'), namespace)
spec = namespace['SPEC']
rock = ROOT/'assets_dev/worlds/mm8/textures/RCTYL.bmp'
spec['materials']['rctyl'] = {'path': str(rock.relative_to(ROOT)),
                            'sha256': hashlib.sha256(rock.read_bytes()).hexdigest()}
water = ROOT/'assets_dev/worlds/mm8/textures/WtrTyl.bmp'
spec['materials']['wtrtyl'] = {'path': str(water.relative_to(ROOT)),
                             'sha256': hashlib.sha256(water.read_bytes()).hexdigest()}
namespace.update({'SCENE_NAME': 'MM5 world rim geometry study', 'SOURCE': OUTPUT, 'MODELS': OUTPUT/'models'})
author = namespace['Author']()
import importlib
import world_rim
importlib.reload(world_rim)
overrides = world_rim.author_rim(author, plan)
author.save()
(OUTPUT/'face_overrides.json').write_text(json.dumps(overrides, indent=2)+'\n')
(OUTPUT/'materials.json').write_text(json.dumps({k: spec['materials'][k] for k in ['rctyl', 'wtrtyl']}, indent=2)+'\n')
bpy.context.window.scene = previous_scene
print({'rimModels': len(author.metadata['bmodels']), 'boundaryFaces': len(plan['edges']),
       'spillFaces': len(overrides)-len(plan['edges']), 'canonicalMapChanged': False})
