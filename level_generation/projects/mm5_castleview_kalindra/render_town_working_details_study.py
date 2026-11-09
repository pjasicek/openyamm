"""Blender MCP: site-specific working settings and court seating, isolated from the compiling map."""
import importlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
VERSION = globals().get('REVIEW_VERSION','town_working_details_v4')
OUTPUT = PROJECT/'review'/VERSION
OUTPUT.mkdir(exist_ok=True)
sys.path.insert(0,str(PROJECT))
import author_town_working_details
importlib.reload(author_town_working_details)
previous = bpy.context.window.scene
path = PROJECT/'author_architecture.py'
definitions,_ = path.read_text().split('\nauthor = Author()\n',1)
namespace = {'__file__':str(path),'__name__':'mm5_town_working_details_study'}
exec(compile(definitions,str(path),'exec'),namespace)
namespace.update({'SCENE_NAME':'MM5 town working details study','SOURCE':OUTPUT,'MODELS':OUTPUT/'models'})
height = (PROJECT/'landscape/heightmap.raw').read_bytes()
details = author_town_working_details.prepare(height)
spec = namespace['SPEC']
spec['buildings'] = [b for b in spec['buildings'] if b['id'] in {p['owner'] for p in details}]
fountain = next(p for p in spec['props'] if p['id']=='healing_fountain')
spec['props'],spec['gates'] = [],[]
author = namespace['Author']()
for building in spec['buildings']:
    author.building(building)
author.fountain(fountain)
for prop in details:
    author_town_working_details.author_detail(author,prop,spec['palettes']['working_props'],height)
renderer = PROJECT/'render_architecture.py'
exec(compile(renderer.read_text(),str(renderer),'exec'),{
    '__file__':str(renderer),'__name__':'__main__','REVIEW_VERSION':VERSION,
    'REVIEW_SCENE':author.scene.name,'REVIEW_SPEC':spec,'REVIEW_SEMANTIC':author.semantic,
    'REVIEW_IDS':[],'REVIEW_TERRAIN':True})
camera = author.scene.camera
views = []
for prop in details:
    for view,distance,height_offset,side in [('detail',600,220,120),('context',1300,460,380)]:
        center = Vector((*prop['frontOrigin'],prop['padHeight']+100))
        eye = center+Vector((prop['frontOutward'][0]*distance+prop['frontTangent'][0]*side,
                             prop['frontOutward'][1]*distance+prop['frontTangent'][1]*side,height_offset))
        camera.data.type = 'PERSP'
        camera.location = eye/namespace['SCALE']
        camera.rotation_euler = (center/namespace['SCALE']-camera.location).to_track_quat('-Z','Y').to_euler()
        name = prop['id']+'_'+view
        author.scene.render.filepath = str(OUTPUT/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        views.append({'name':name,'eye':list(eye),'target':list(center)})
(OUTPUT/'source.json').write_text(json.dumps({'props':details,'geometry':author.metadata,
    'semantic':author.semantic,'views':views,'status':'Isolated source study; not integrated.'},indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'),{author.scene},fake_user=True,compress=True)
bpy.context.window.scene = previous
print('Working settings and fountain seat rendered in their own study; native compile inputs unchanged.')
