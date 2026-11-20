"""Blender MCP: review the proposed woodcraft setting without mutating a compiling source package."""
import importlib
import json
from pathlib import Path
import sys

import bpy

PROJECT = Path(__file__).resolve().parent
VERSION = globals().get('REVIEW_VERSION','ranger_yard_v1')
OUTPUT = PROJECT/'review'/VERSION
OUTPUT.mkdir(exist_ok=True)
sys.path.insert(0,str(PROJECT))
import author_ranger_yard
importlib.reload(author_ranger_yard)
previous = bpy.context.window.scene
path = PROJECT/'author_architecture.py'
definitions, _ = path.read_text().split('\nauthor = Author()\n',1)
namespace = {'__file__':str(path),'__name__':'mm5_ranger_study_author'}
exec(compile(definitions,str(path),'exec'),namespace)
namespace.update({'SCENE_NAME':'MM5 ranger yard study','SOURCE':OUTPUT,'MODELS':OUTPUT/'models'})
author = namespace['Author']()
height = (PROJECT/'landscape/heightmap.raw').read_bytes()
prop = author_ranger_yard.prepare(height)
spec = namespace['SPEC']
spec['buildings'], spec['gates'], spec['props'] = [], [], [prop]
author_ranger_yard.author_yard(author, prop, spec['palettes']['working_props'], height)
renderer = PROJECT/'render_architecture.py'
exec(compile(renderer.read_text(),str(renderer),'exec'),{'__file__':str(renderer),'__name__':'__main__',
    'REVIEW_VERSION':VERSION,'REVIEW_SCENE':author.scene.name,'REVIEW_SPEC':spec,
    'REVIEW_SEMANTIC':author.semantic,'REVIEW_IDS':[prop['id']],'REVIEW_TERRAIN':True})
(OUTPUT/'source.json').write_text(json.dumps({'prop':prop,'geometry':author.metadata,
    'status':'Isolated source study; not yet integrated into the map or accepted natively.'},indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'),{author.scene},fake_user=True,compress=True)
bpy.context.window.scene = previous
print('Ranger yard isolated study rendered; current native build inputs unchanged.')
