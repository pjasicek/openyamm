"""Review the closed pyramid in a separate scene before copying its one donor bitmap into MM5."""
import importlib
import json
import sys
from pathlib import Path

import bpy

PROJECT=Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT))
import prepare_pyramid
import author_pyramid
for module in [prepare_pyramid,author_pyramid]:importlib.reload(module)
VERSION=globals().get('REVIEW_VERSION','pyramid_study_v1')
OUTPUT=PROJECT/'review'/VERSION
OUTPUT.mkdir(exist_ok=True)
previous_scene=bpy.context.window.scene
path=PROJECT/'author_architecture.py'
definitions,_=path.read_text().split('\nauthor = Author()\n',1)
namespace={'__file__':str(path),'__name__':'mm5_pyramid_study_author'}
exec(compile(definitions,str(path),'exec'),namespace)
spec=namespace['SPEC'];spec['buildings'],spec['gates']=[],[]
spec['materials']['mm5pyrst']=prepare_pyramid.material()
spec['props']=prepare_pyramid.prepare((PROJECT/'landscape/heightmap.raw').read_bytes())
namespace.update({'SCENE_NAME':'MM5 closed pyramid study','SOURCE':OUTPUT,'MODELS':OUTPUT/'models'})
author=namespace['Author']()
for prop in spec['props']:author_pyramid.author_pyramid(author,prop,prepare_pyramid.PALETTE)
renderer=PROJECT/'render_architecture.py'
exec(compile(renderer.read_text(),str(renderer),'exec'),{'__file__':str(renderer),'__name__':'__main__',
    'REVIEW_VERSION':VERSION,'REVIEW_SCENE':author.scene.name,'REVIEW_SPEC':spec,'REVIEW_SEMANTIC':author.semantic,
    'REVIEW_IDS':[p['id'] for p in spec['props']],'REVIEW_TERRAIN':True})
(OUTPUT/'source.json').write_text(json.dumps({'props':spec['props'],'geometry':author.metadata,
    'materials':{k:spec['materials'][k] for k in prepare_pyramid.PALETTE.values()},
    'limits':'Isolated source study; active source and runtime unchanged.'},indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'),{author.scene},fake_user=True,compress=True)
bpy.context.window.scene=previous_scene
print({'study':str(OUTPUT),'activeMapChanged':False})
