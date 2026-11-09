"""Inspect the original camp setting and its native fire thumbnail without changing the active map."""
import importlib
import json
import sys
from pathlib import Path

import bpy

PROJECT=Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT))
import native_scenery
import prepare_barbarian_camp
import author_barbarian_camp
for module in [native_scenery,prepare_barbarian_camp,author_barbarian_camp]:importlib.reload(module)
VERSION=globals().get('REVIEW_VERSION','barbarian_camp_study_v1')
OUTPUT=PROJECT/'review'/VERSION
OUTPUT.mkdir(exist_ok=True)
previous_scene=bpy.context.window.scene
path=PROJECT/'author_architecture.py'
definitions,_=path.read_text().split('\nauthor = Author()\n',1)
namespace={'__file__':str(path),'__name__':'mm5_barbarian_camp_study_author'}
exec(compile(definitions,str(path),'exec'),namespace)
spec=namespace['SPEC'];spec['buildings'],spec['gates']=[],[]
height=(PROJECT/'landscape/heightmap.raw').read_bytes()
spec['props']=prepare_barbarian_camp.prepare(height)
namespace.update({'SCENE_NAME':'MM5 barbarian camp study','SOURCE':OUTPUT,'MODELS':OUTPUT/'models'})
author=namespace['Author']()
for prop in spec['props']:author_barbarian_camp.author_camp(author,prop,prepare_barbarian_camp.PALETTE,height)
renderer=PROJECT/'render_architecture.py'
exec(compile(renderer.read_text(),str(renderer),'exec'),{'__file__':str(renderer),'__name__':'__main__',
    'REVIEW_VERSION':VERSION,'REVIEW_SCENE':author.scene.name,'REVIEW_SPEC':spec,'REVIEW_SEMANTIC':author.semantic,
    'REVIEW_IDS':[p['id'] for p in spec['props']],'REVIEW_TERRAIN':True})
(OUTPUT/'source.json').write_text(json.dumps({'props':spec['props'],'geometry':author.metadata,
    'limits':'Isolated source study; fire uses a static native frame. Runtime animation, light and placeholder remain unverified.'},indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'),{author.scene},fake_user=True,compress=True)
bpy.context.window.scene=previous_scene
print({'study':str(OUTPUT),'activeMapChanged':False})
