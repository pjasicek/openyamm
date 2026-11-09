"""Isolated roofed-well material/geometry study using the project's actual authoring class."""
import importlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT))
import author_source_wells
import prepare_source_wells
importlib.reload(author_source_wells)
importlib.reload(prepare_source_wells)
OUTPUT = PROJECT/'review'/globals().get('REVIEW_VERSION','source_well_study_v1')
OUTPUT.mkdir(exist_ok=True)
previous_scene = bpy.context.window.scene
# Load definitions only; the study owns a separate scene and output directory.
path = PROJECT/'author_architecture.py'
definitions, _ = path.read_text().split('\nauthor = Author()\n',1)
namespace = {'__file__':str(path),'__name__':'mm5_well_study_author'}
exec(compile(definitions,str(path),'exec'),namespace)
namespace.update({'SCENE_NAME':'MM5 roofed well study','SOURCE':OUTPUT,'MODELS':OUTPUT/'models'})
author = namespace['Author']()
scene = author.scene
height = (PROJECT/'landscape/heightmap.raw').read_bytes()
placed = globals().get('REVIEW_PLACEMENTS',False)
props = prepare_source_wells.prepare(height)
if not placed:
    props = [dict(props[0])]
    props[0].update({'frontOrigin':[0,0],'frontOutward':[0,-1],'frontTangent':[1,0],'padHeight':0,
                     'foundation':{'skirtBottomZ':-24}})
for prop in props:
    author_source_wells.author_well(author,prop,prepare_source_wells.PALETTE)

ground_mesh = bpy.data.meshes.new('MM5 well study ground')
if placed:
    vertices = [((c*512-32768)/128,(32768-r*512)/128,height[r*128+c]*32/128)
                for r in range(128) for c in range(128)]
    faces = []
    for r in range(127):
        for c in range(127):
            i = r*128+c
            faces.extend([(i,i+128,i+1),(i+129,i+1,i+128)])
else:
    vertices,faces = [(-100,-100,0),(100,-100,0),(100,100,0),(-100,100,0)],[(0,1,2,3)]
ground_mesh.from_pydata(vertices,[],faces)
ground = bpy.data.objects.new('MM5 well study ground',ground_mesh)
scene.collection.objects.link(ground)
material = bpy.data.materials.new('MM5 well study neutral ground')
material.diffuse_color = (.19,.23,.14,1)
ground_mesh.materials.append(material)
scene.world = bpy.data.worlds.new('MM5 well study world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.44,.51,.62,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
sun = bpy.data.objects.new('MM5 well study sun',bpy.data.lights.new('MM5 well study sun','SUN'))
scene.collection.objects.link(sun)
sun.data.energy = 2.2
sun.rotation_euler = (math.radians(30),math.radians(-25),math.radians(-35))
camera = bpy.data.objects.new('MM5 well study camera',bpy.data.cameras.new('MM5 well study camera'))
scene.collection.objects.link(camera)
camera.data.lens = 35
camera.data.clip_end = 2000
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x,scene.render.resolution_y = 1100,760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
views = []
from author_props import ground_at
for prop in props:
    for label,local_position,target_height in [('eye',(0,-800,176),216),
                                               ('oblique',(550,-650,420),192),
                                               ('rear',(450,550,300),192)]:
        if placed and label=='rear':continue
        x,y,z = local_position
        position = [prop['frontOrigin'][i]+prop['frontTangent'][i]*x-prop['frontOutward'][i]*y
                    for i in range(2)]
        position.append((ground_at(height,position) if placed and label=='eye' else prop['padHeight'])+z)
        target = prop['frontOrigin']+[prop['padHeight']+target_height]
        image_name = (prop['id']+'_' if placed else '')+label+'.png'
        camera.location = Vector(position)/128
        camera.rotation_euler = (Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath = str(OUTPUT/image_name)
        bpy.ops.render.render(write_still=True)
        views.append({'image':image_name,'position':position,'target':target})
(OUTPUT/'views.json').write_text(json.dumps({'status':'Isolated template study; inspect images before acceptance',
    'views':views,'props':props,'nativeHeightfield':placed,
    'limits':'Isolated study with neutral ground; active map and native context are unchanged.'},indent=2)+'\n')
bpy.data.libraries.write(str(OUTPUT/'study.blend'),{scene},fake_user=True,compress=True)
bpy.context.window.scene = previous_scene
print({'study':str(OUTPUT),'views':len(views),'activeMapChanged':False})
