"""Isolated sign study using the actual author and calibrated renderer, with no active map writes."""
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(PROJECT))
import author_source_signs
import prepare_source_signs
importlib.reload(author_source_signs)
importlib.reload(prepare_source_signs)
VERSION = globals().get('REVIEW_VERSION','source_sign_study_v1')
OUTPUT = PROJECT/'review'/VERSION
OUTPUT.mkdir(exist_ok=True)
previous_scene = bpy.context.window.scene
path = PROJECT/'author_architecture.py'
definitions, _ = path.read_text().split('\nauthor = Author()\n',1)
namespace = {'__file__':str(path),'__name__':'mm5_sign_study_author'}
exec(compile(definitions,str(path),'exec'),namespace)
spec = namespace['SPEC']
for key in prepare_source_signs.FACES.values():
    svg = PROJECT/'implementation/art'/(key+'.svg')
    png = OUTPUT/(key+'.png')
    subprocess.run(['convert',str(svg),'-strip',str(png)],check=True)
    spec['materials'][key] = {'path':str(png.relative_to(ROOT)),
        'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'sourceSvg':str(svg.relative_to(ROOT)),
        'sourceSvgSha256':hashlib.sha256(svg.read_bytes()).hexdigest()}
spec['buildings'],spec['gates'] = [],[]
spec['props'] = prepare_source_signs.prepare((PROJECT/'landscape/heightmap.raw').read_bytes())
namespace.update({'SCENE_NAME':'MM5 source sign study','SOURCE':OUTPUT,'MODELS':OUTPUT/'models'})
author = namespace['Author']()
for prop in spec['props']:
    author_source_signs.author_sign(author,prop,prepare_source_signs.PALETTE)
renderer = PROJECT/'render_architecture.py'
exec(compile(renderer.read_text(),str(renderer),'exec'),{'__file__':str(renderer),'__name__':'__main__',
    'REVIEW_VERSION':VERSION,'REVIEW_SCENE':author.scene.name,'REVIEW_SPEC':spec,
    'REVIEW_SEMANTIC':author.semantic,'REVIEW_IDS':[p['id'] for p in spec['props']],'REVIEW_TERRAIN':True})
(OUTPUT/'source.json').write_text(json.dumps({'props':spec['props'],'geometry':author.metadata,
    'materials':spec['materials'],'limits':'Isolated source-sign study; active source/native map unchanged.'},indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'),{author.scene},fake_user=True,compress=True)
bpy.context.window.scene = previous_scene
print({'study':str(OUTPUT),'activeMapChanged':False})
