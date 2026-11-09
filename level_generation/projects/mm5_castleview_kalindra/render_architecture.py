"""Blender prototype views at documented, repeatable physical camera settings."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT))
from author_props import ground_at
REVIEW = PROJECT / 'review' / globals().get('REVIEW_VERSION', 'architecture_v2')
REVIEW.mkdir(parents=True, exist_ok=True)
SCALE = 128
scene = bpy.data.scenes[globals().get('REVIEW_SCENE','MM5 Castleview architecture')]
bpy.context.window.scene = scene
spec = globals()['REVIEW_SPEC'] if 'REVIEW_SPEC' in globals() else json.loads(
    (PROJECT / 'implementation/architecture.json').read_text())
ids = globals().get('REVIEW_IDS', ['guild', 'forge', 'training', 'monks_n', 'bank', 'healing_fountain'])
for obj in list(scene.objects):
    if obj.get('levelgen_kind') == 'review':
        bpy.data.objects.remove(obj, do_unlink=True)


def review_object(name, data):
    obj = bpy.data.objects.new('REVIEW_' + name, data)
    obj['levelgen_kind'] = 'review'
    scene.collection.objects.link(obj)
    return obj


sun_data = bpy.data.lights.new('MM5 prototype sunlight', 'SUN')
sun_data.energy = 2.2
sun_data.angle = math.radians(12)
sun = review_object('sun', sun_data)
sun.rotation_euler = (math.radians(30), math.radians(-25), math.radians(-35))
scene.world = bpy.data.worlds.new('MM5 prototype neutral world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.44, .51, .62, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
floor_mesh = bpy.data.meshes.new('MM5 review floor')
floor_mesh.from_pydata([(-32,-32,0),(32,-32,0),(32,32,0),(-32,32,0)], [], [(0,1,2,3)])
floor = review_object('floor', floor_mesh)
mat = bpy.data.materials.new('MM5 neutral review ground')
mat.diffuse_color = (.19,.23,.14,1)
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.19,.23,.14,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1
floor_mesh.materials.append(mat)
camera = review_object('camera', bpy.data.cameras.new('MM5 calibrated camera'))
camera.data.lens = 35
camera.data.clip_end = 2000
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1100
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
scene.render.film_transparent = False
report = []
semantic = globals()['REVIEW_SEMANTIC'] if 'REVIEW_SEMANTIC' in globals() else json.loads(
    (PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())


def terrain_review():
    floor.hide_render=True
    heights=(PROJECT/'landscape/heightmap.raw').read_bytes()
    vertices=[((c*512-32768)/SCALE,(32768-r*512)/SCALE,heights[r*128+c]*32/SCALE)
              for r in range(128) for c in range(128)]
    faces=[]
    for r in range(127):
        for c in range(127):
            i=r*128+c
            faces.extend([(i,i+128,i+1),(i+129,i+1,i+128)])
    mesh=bpy.data.meshes.new('MM5 actual heightfield review')
    mesh.from_pydata(vertices,[],faces)
    mesh.materials.append(mat)
    review_object('heightfield',mesh)


if globals().get('REVIEW_TERRAIN',False):
    terrain_review()


def native_preview(record):
    art = record['nativeArt']
    radius, height = record['visualRadius']/SCALE, record['visualHeight']/SCALE
    mesh = bpy.data.meshes.new('MM5 native scenery review')
    mesh.from_pydata([(-radius,0,0),(radius,0,0),(radius,0,height),(-radius,0,height)], [], [(0,1,2,3)])
    layer = mesh.uv_layers.new()
    for datum, uv in zip(layer.data, [(0,0),(1,0),(1,1),(0,1)]):
        datum.uv = uv
    obj = review_object(record['id'], mesh)
    obj.location = Vector(record['position'])/SCALE
    material = bpy.data.materials.new('MM5 native '+record['name'])
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    texture = nodes.new('ShaderNodeTexImage')
    path = PROJECT.parents[1]/'catalogues/outdoor_decorations'/art['path']
    texture.image = bpy.data.images.load(str(path), check_existing=True)
    texture.interpolation = 'Closest'
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = 1
    links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    mix = nodes.new('ShaderNodeMixShader')
    links.new(texture.outputs['Alpha'], mix.inputs[0])
    links.new(nodes.new('ShaderNodeBsdfTransparent').outputs[0], mix.inputs[1])
    links.new(shader.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes.get('Material Output').inputs[0])
    mesh.materials.append(material)
    return obj


for entry in spec['buildings'] + semantic['props'] + spec['gates'] + semantic.get('bridges',[]):
    if entry['id'] not in ids:
        continue
    for obj in scene.objects:
        if obj.get('levelgen_kind') == 'bmodel':
            obj.hide_render = obj.get('assembly_id') != entry['id']
    x, y = entry['frontOrigin']
    z = entry['padHeight']
    outward = entry['frontOutward']
    tangent = entry['frontTangent']
    native_objects = [native_preview(record) for record in entry.get('nativeScenery', [])]
    floor.location = Vector((x,y,z-1))/SCALE
    views = [('oblique',1600,1000,1100,256), ('eye',1000,0,176,176)]
    if entry['id'] == 'forge':
        views.append(('rear_yard',-2200,-1000,900,192))
        views.append(('equipment',-1184,600,220,112))
    if entry['id']=='joe':
        views=[('oblique',650,450,430,144),('counter',420,0,176,80)]
    if entry['id']=='puzzle':
        views.append(('storage_roofs',-2800,1900,2200,384))
    if entry['id']=='tower':
        views=[('oblique',5200,3200,3400,1280),('eye',2400,0,176,1400)]
    if entry['id']=='western':
        views=[('oblique',4200,3000,3600,1280),('eye',4200,0,176,1280),
               ('roof',-512,128,2608,2580)]
    if entry['id'] in ['dreyfus','justine','yog','kramer']:
        views=[('oblique',1000,750,750,176),('eye',900 if entry['id']=='yog' else 640,0,176,128),
               ('rear_yard',-entry['localFootprint'][1]-600,650,420,160)]
    if entry.get('entranceGeometry'):
        views=[('oblique',900,650,800,200),('eye',1000,0,176,192),
               ('rear_yard',-1100,700,600,192)]
    if entry['id']=='sewer_out':
        views=[('oblique',1300,1000,900,128),('eye',1000,0,176,128),
               ('rear_yard',-1000,800,600,128)]
    if entry['id']=='skyrope':
        views=[('eye',1400,320,176,420),('side',0,1400,176,420),('upper_anchor',240,420,800,672)]
    if entry['id']=='kalindra':
        views=[('oblique',6500,4800,4800,1536),('eye',6500,0,176,1536),
               ('court',-352,-448,176,96),('court_return',-1400,128,176,200),
               ('keep_door',-1152,128,176,160),('rear',-9000,-5000,3800,1792)]
    if entry['id']=='temple':
        views=[('oblique',2200,1500,1600,384),('eye',1400,0,176,384),
               ('apse',-2500,1300,1400,384)]
    if entry['id'] in ['ruby','emerald','sapphire','diamond']:
        views=[('oblique',1050,700,760,224),('eye',640,0,176,176),
               ('sorting_yard',-entry['localFootprint'][1]-400,450,300,96)]
    if entry['id'] in ['reger','luna','vespar']:
        views=[('oblique',900,650,650,192),('eye',640,0,176,176),
               ('side_yard',-entry['localFootprint'][1]*.65,650,300,128)]
    if entry['id']=='luna_altar':
        views=[('oblique',450,320,420,112),('eye',400,0,176,112)]
    if entry.get('kind')=='town sewer grate':
        views=[('oblique',320,240,320,8),('eye',320,0,176,8)]
    if entry.get('kind')=='town chest':
        views=[('oblique',360,260,300,72),('eye',320,0,176,72)]
    if entry.get('kind')=='source well':
        views=[('oblique',650,550,420,192),('eye',800,0,176,216)]
    if entry.get('kind')=='source sign':
        views=[('oblique',500,340,340,176),('eye',640,0,176,192),('rear',-600,240,240,176)]
    if entry.get('kind')=='source shrine':
        views=[('oblique',1200,800,800,320),('eye',1500,0,176,320),('rear',-1400,700,400,320)]
    if entry.get('kind')=='message bottle':
        views=[('oblique',240,180,200,24),('eye',320,0,176,24),('rear',-260,160,160,24)]
    if entry.get('kind')=='melon patch':
        views=[('oblique',500,360,440,16),('eye',520,0,176,16)]
    if entry.get('kind')=='source wreck':
        views=[('oblique',1400,1100,1100,288),('eye',960,0,176,280),
               ('approach',1600,240,176,320),('side',0,1800,400,288)]
    if entry.get('kind')=='barbarian camp':
        views=[('oblique',1400,1100,1100,128),('eye',1000,0,176,96),('rear',-1500,600,480,128)]
    if entry.get('kind')=='closed pyramid':
        views=[('oblique',950,700,700,192),('eye',800,0,176,192),('rear',-900,500,400,192)]
    if entry.get('surfaces'):
        views=[('oblique',1500,1800,1600,0),('start_landing',650,0,176,0),
               ('end_landing',-entry['length']-750,450,320,0),
               ('supports',-entry['length']*.5,700,32,-32)]
    if entry['id'] in ['herbalist','keeper']:
        views.append(('rear_yard',-entry['localFootprint'][1]-550,-450,420,128))
        views.append(('side_yard',-entry['localFootprint'][1]*.75,700,250,128))
    if entry['id'] == 'healing_fountain':
        views = [('oblique',800,600,700,96), ('eye',650,0,176,96)]
    elif entry['id']=='training_pool':
        views = [('oblique',900,700,600,0),('north_step',-700,250,176,0)]
    elif entry.get('sourceRecord'):
        views = [('oblique',500,350,400,96), ('eye',500,0,176,96)]
    if entry.get('kind') == 'gate':
        views = [('oblique',2300,1800,2000,768), ('eye',1400,0,176,640),
                 ('passage',-850,0,176,512)]
    for kind, distance, side, eye, target_height in views:
        if globals().get('REVIEW_VIEWS') and kind not in globals()['REVIEW_VIEWS']:
            continue
        position = (x + outward[0]*distance + tangent[0]*side,
                    y + outward[1]*distance + tangent[1]*side, z+eye)
        if kind=='eye' and globals().get('REVIEW_TERRAIN',False):
            height=(PROJECT/'landscape/heightmap.raw').read_bytes()
            position=(*position[:2],ground_at(height,position)+eye)
        target_depth = (entry['length']*.5 if entry.get('surfaces') and kind in ['oblique','supports'] else
                        entry['length'] if kind=='end_landing' else
                        0 if kind=='start_landing' or entry.get('kind') in
                        ['town sewer grate','town chest','source well','source sign','source shrine','message bottle',
                         'melon patch','source wreck','barbarian camp','closed pyramid']
                        or entry['id'] in ['healing_fountain','training_pool','luna_altar'] else
                        1184 if kind=='equipment' else
                        960 if kind=='court' else 0 if kind=='court_return' else
                        1536 if kind=='keep_door' else
                        2800 if kind=='rear' else
                        864 if kind=='roof' else 1200 if kind=='storage_roofs' else
                        1000 if kind=='apse' else
                        entry['localFootprint'][1]*.75 if kind in ['rear_yard','side_yard','sorting_yard'] else 200)
        target_side=(-192 if entry['id']=='western' and kind=='roof' else
                     384 if entry['id']=='kalindra' and kind=='court' else
                     128 if entry['id']=='kalindra' and kind=='keep_door' else 0)
        target = (x-outward[0]*target_depth+tangent[0]*target_side,
                  y-outward[1]*target_depth+tangent[1]*target_side,z+target_height)
        camera.location = Vector(position)/SCALE
        camera.rotation_euler = (Vector(target)/SCALE-camera.location).to_track_quat('-Z','Y').to_euler()
        for obj in native_objects:
            direction = camera.location-obj.location
            obj.rotation_euler[2] = math.atan2(direction.y,direction.x)+math.pi/2
        path = REVIEW / (entry['id'] + '_' + kind + '.png')
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        report.append({'assembly':entry['id'],'view':kind,'position':position,'target':target,
                       'lens_mm':35,'sensor_width_mm':camera.data.sensor_width,'image':path.name,
                       'ground':('actual native heightfield; neutral material for geometry review'
                                 if globals().get('REVIEW_TERRAIN',False) else
                                 'neutral review plane; not final native terrain')})
    for obj in native_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
for obj in scene.objects:
    if obj.get('levelgen_kind') == 'bmodel':
        obj.hide_render = False
if globals().get('REVIEW_WALLS', False):
    if not globals().get('REVIEW_TERRAIN',False):
        terrain_review()
    for kind,position,target in [
            ('curtain_overview',(15000,-20000,17000),(-2704,-500,1000)),
            ('south_context',(-5000,-10500,3400),(-2304,-5600,1300)),
            ('west_context',(-13000,-1600,3200),(-8400,768,1300))]:
        camera.location=Vector(position)/SCALE
        camera.rotation_euler=(Vector(target)/SCALE-camera.location).to_track_quat('-Z','Y').to_euler()
        path=REVIEW/(kind+'.png')
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        report.append({'assembly':'town_wall','view':kind,'position':position,'target':target,
                       'image':path.name,'ground':'actual native heightfield; neutral material for geometry review'})
camera_path = REVIEW / 'cameras.json'
previous = json.loads(camera_path.read_text()) if camera_path.exists() else []
previous = [r for r in previous if r['assembly'] not in ids]
camera_path.write_text(json.dumps(previous + report,indent=2)+'\n')
print({'rendered':len(report),'directory':str(REVIEW)})
