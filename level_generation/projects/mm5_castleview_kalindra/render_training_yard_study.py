"""Blender MCP: isolated practice-target fit, including the actual hall and pool."""
import importlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT=Path(__file__).resolve().parent
VERSION=globals().get('REVIEW_VERSION','training_yard_v1')
OUTPUT=PROJECT/'review'/VERSION
OUTPUT.mkdir(exist_ok=True)
sys.path.insert(0,str(PROJECT))
import author_training_yard
importlib.reload(author_training_yard)
previous=bpy.context.window.scene
path=PROJECT/'author_architecture.py'
definitions,_=path.read_text().split('\nauthor = Author()\n',1)
namespace={'__file__':str(path),'__name__':'mm5_training_yard_study_author'}
exec(compile(definitions,str(path),'exec'),namespace)
namespace.update({'SCENE_NAME':'MM5 training yard study','SOURCE':OUTPUT,'MODELS':OUTPUT/'models'})
spec=namespace['SPEC']
spec['buildings']=[b for b in spec['buildings'] if b['id']=='training']
pool=next(p for p in spec['props'] if p['id']=='training_pool')
spec['props'],spec['gates']=[],[]
height=(PROJECT/'landscape/heightmap.raw').read_bytes()
targets=author_training_yard.prepare(height)
author=namespace['Author']()
author.building(spec['buildings'][0])
namespace['author_props'].author_training_pool(author,pool,spec['palettes'][pool['palette']])
for target in targets:
    author_training_yard.author_target(author,target,author_training_yard.PALETTE)
renderer=PROJECT/'render_architecture.py'
exec(compile(renderer.read_text(),str(renderer),'exec'),{
    '__file__':str(renderer),'__name__':'__main__','REVIEW_VERSION':VERSION,
    'REVIEW_SCENE':author.scene.name,'REVIEW_SPEC':spec,'REVIEW_SEMANTIC':author.semantic,
    'REVIEW_IDS':[],'REVIEW_TERRAIN':True})
views=[('south_context',(-500,-1900,1050),(-280,-100,850),None),
       ('targets_detail',(-270,-1100,848),(-270,-360,830),None),
       ('site_plan',(0,400,8000),(0,400,0),3600)]
camera=author.scene.camera
for name,eye,target,ortho in views:
    camera.data.type='ORTHO' if ortho else 'PERSP'
    if ortho:camera.data.ortho_scale=ortho/namespace['SCALE']
    camera.location=Vector(eye)/namespace['SCALE']
    camera.rotation_euler=(Vector(target)/namespace['SCALE']-camera.location).to_track_quat('-Z','Y').to_euler()
    author.scene.render.filepath=str(OUTPUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
(OUTPUT/'source.json').write_text(json.dumps({'targets':targets,'geometry':author.metadata,
    'semantic':author.semantic,'views':views,'status':'Isolated source study; no canonical/native integration.'},indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'),{author.scene},fake_user=True,compress=True)
bpy.context.window.scene=previous
print('Training-yard source study saved; current native compile inputs unchanged.')
