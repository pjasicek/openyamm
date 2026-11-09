"""Execute through Blender MCP with WORLD, MAP and KIND globals; not a map exporter.

Example execute_blender_code body (replace the absolute path for your checkout):
exec(compile(open('/repo/level_generation/scripts/blender_reference_view.py').read(),
             'blender_reference_view.py', 'exec'),
     {'WORLD': 'mm8', 'MAP': 'd48', 'KIND': 'indoor', 'REPO': '/repo'})

Creates an independent scene, a textured study mesh, a separately hidden ceiling,
and fitted orthographic cameras. Saves a PNG and view metadata. The original scenes
are preserved. Lighting is neutral inspection lighting, not the OpenYAMM renderer.
"""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector

root = Path(REPO)
sys.path.insert(0, str(root / 'util'))
from map_export import parse_blv_file, parse_odm_file

path = root / 'assets_dev/worlds' / WORLD / 'maps' / (MAP + ('.blv' if KIND == 'indoor' else '.odm'))
payload = (parse_blv_file if KIND == 'indoor' else parse_odm_file)(path)['payload']
evidencePath = root / 'level_generation/evidence' / WORLD
summary = json.loads((evidencePath / (MAP+'.json')).read_text())
scene = bpy.data.scenes.new('Reference ' + WORLD + '/' + MAP)
bpy.context.window.scene = scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 12
scene.render.resolution_x = 1200
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('Inspection world ' + MAP)
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.16,.18,.22,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .7
scene.view_settings.view_transform = 'Standard'

sourceCollection = bpy.data.collections.new('Reference geometry ' + MAP)
ceilingCollection = bpy.data.collections.new('Ceilings ' + MAP + ' - study toggle')
rigCollection = bpy.data.collections.new('Study rig ' + MAP)
for collection in [sourceCollection,ceilingCollection,rigCollection]:
    scene.collection.children.link(collection)
ceilingCollection.hide_render = True
ceilingCollection.hide_viewport = True
texturePaths = {}
# Match merged development content: active world, engine, then other mounted worlds.
worldRoot = root / 'assets_dev/worlds'
packageRoots = [worldRoot / WORLD, root / 'assets_dev/engine']
packageRoots.extend(p for p in sorted(worldRoot.iterdir()) if p.is_dir() and p.name != WORLD)
for package in packageRoots:
    for category in ('terrain', 'textures'):
        folder = package / category
        if folder.exists():
            for p in sorted(folder.iterdir()):
                if p.suffix.lower() in ('.bmp', '.png'):
                    texturePaths.setdefault(p.stem.lower(), p)
materialCache = {}
missing = set()

def material(name):
    key = name.lower()
    if key in materialCache:
        return materialCache[key]
    mat = bpy.data.materials.new('Reference_' + WORLD + '_' + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 1
    if key in texturePaths:
        image = bpy.data.images.load(str(texturePaths[key]),check_existing=True)
        if KIND == 'outdoor' and (globals().get('DECORATION_REVIEW') or globals().get('STUDY_VIEWS')):
            # Decode keyed shore overlays over a native water frame for this study.
            water_entries = [v for v in summary['terrain']['palette'].values()
                             if v['flags'] & 2 and v.get('preview_texture') in texturePaths]
            terrain_keys = {v['texture'].lower() for v in summary['terrain']['palette'].values()}
            if water_entries and key in terrain_keys:
                pixels = np.array(image.pixels[:],dtype=np.float32).reshape(-1,4)
                keyed = ((pixels[:,0]>.97)&(pixels[:,1]<.03)&(pixels[:,2]>.97)) | \
                        ((pixels[:,0]<.03)&(pixels[:,1]>.97)&(pixels[:,2]>.97))
                if keyed.any():
                    water = bpy.data.images.load(str(texturePaths[water_entries[0]['preview_texture']]),check_existing=True)
                    water_pixels = np.array(water.pixels[:],dtype=np.float32).reshape(water.size[1],water.size[0],4)
                    rows = np.arange(image.size[1])*water.size[1]//image.size[1]
                    cols = np.arange(image.size[0])*water.size[0]//image.size[0]
                    base = water_pixels[rows[:,None],cols[None,:]].reshape(-1,4)
                    pixels[keyed] = base[keyed]
                    composed = bpy.data.images.new('Native keyed shore '+WORLD+' '+key,
                                                  width=image.size[0],height=image.size[1])
                    composed.pixels.foreach_set(pixels.ravel());image = composed
        texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image = image
        texture.interpolation = 'Closest'
        texture.extension = 'REPEAT'
        mat.node_tree.links.new(texture.outputs['Color'],bsdf.inputs['Base Color'])
        size = tuple(image.size)
    else:
        bsdf.inputs['Base Color'].default_value = (1,0,1,1)
        size = (256,256)
        missing.add(key)
    materialCache[key] = (mat,size)
    return mat,size

def makeMesh(name, records, target):
    verts, faces, uvs, faceMaterials = [],[],[],[]
    for points,texture,coordinates in records:
        if len(points)<3:
            continue
        start = len(verts)
        verts.extend(points)
        faces.append(tuple(range(start,start+len(points))))
        uvs.extend(coordinates)
        faceMaterials.append(material(texture)[0])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj = bpy.data.objects.new(name,mesh)
    target.objects.link(obj)
    slots = {}
    for i,mat in enumerate(faceMaterials):
        if mat.name not in slots:
            slots[mat.name] = len(mesh.materials)
            mesh.materials.append(mat)
        mesh.polygons[i].material_index = slots[mat.name]
    uvLayer = mesh.uv_layers.new(name='Source UV')
    for loop,uv in zip(uvLayer.data,uvs):
        loop.uv = uv
    return obj

allPoints = []
if KIND == 'indoor':
    visibleRecords, ceilingRecords = [],[]
    sourceVertices = [tuple(v[a]/128 for a in 'xyz') for v in payload['vertices']]
    allPoints.extend(sourceVertices)
    for face in payload['faces']:
        if face['is_portal'] or face['attributes'] & 0x2000:
            continue
        params = face['face_param'] or {}
        texture = face['texture_name']
        mat,size = material(texture)
        points = [sourceVertices[i] for i in face['vertex_indices']]
        uv = [((u+params.get('texture_delta_u',0))/size[0],1-(v+params.get('texture_delta_v',0))/size[1])
              for u,v in zip(face['texture_us'],face['texture_vs'])]
        (ceilingRecords if face['facet_type'] in (5,6) else visibleRecords).append((points,texture,uv))
    makeMesh('Reference floors and walls',visibleRecords,sourceCollection)
    makeMesh('Reference ceiling',ceilingRecords,ceilingCollection)
else:
    records = []
    terrain = summary['terrain']
    palette = terrain['palette']
    for y in range(127):
        for x in range(127):
            corners = [(x,y),(x+1,y),(x,y+1),(x+1,y+1)]
            points = [((gx-64)*4,(64-gy)*4,payload['height_map'][gy*128+gx]/4) for gx,gy in corners]
            info = palette[str(payload['tile_map'][y*128+x])]
            texture = info.get('preview_texture',info['texture'])
            # Match the runtime's anti-diagonal split and upward-facing normals.
            records.append(([points[i] for i in (0,2,1)],texture,[(0,1),(0,0),(1,1)]))
            records.append(([points[i] for i in (1,2,3)],texture,[(1,1),(0,0),(1,0)]))
            allPoints.extend(points)
    makeMesh('Native ODM heightfield preview',records,sourceCollection)
    records = []
    for model in payload['bmodels']:
        vertices = [tuple(v[a]/128 for a in 'xyz') for v in model['vertices']]
        allPoints.extend(vertices)
        for face in model['faces']:
            if face['attributes']&0x2000:
                continue
            mat,size = material(face['texture_name'])
            uv = [((u+face['texture_delta_u'])/size[0],1-(v+face['texture_delta_v'])/size[1])
                  for u,v in zip(face['texture_us'],face['texture_vs'])]
            records.append(([vertices[i] for i in face['vertex_indices']],face['texture_name'],uv))
    makeMesh('Original BModels',records,sourceCollection)

lo = Vector(tuple(min(p[i] for p in allPoints) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in allPoints) for i in range(3)))
center = (lo+hi)/2
extent = max(hi.x-lo.x,hi.y-lo.y,10)
camData = bpy.data.cameras.new('Study camera ' + MAP)
camData.type = 'ORTHO'
camData.clip_end = extent*20
camera = bpy.data.objects.new(camData.name,camData)
rigCollection.objects.link(camera)
camera.location = center + Vector((.65,-.9,1.4))*extent
camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera = camera
inverseRotation = camera.rotation_euler.to_quaternion().inverted()
projected = [inverseRotation@(Vector(p)-center) for p in allPoints]
width = max(p.x for p in projected)-min(p.x for p in projected)
height = max(p.y for p in projected)-min(p.y for p in projected)
aspect = scene.render.resolution_x/scene.render.resolution_y
camData.ortho_scale = max(width,height*aspect)*1.14
lightData = bpy.data.lights.new('Neutral inspection sun','SUN')
lightData.energy = 2
lightData.angle = .2
light = bpy.data.objects.new(lightData.name,lightData)
rigCollection.objects.link(light)
light.rotation_euler = (.3,-.4,-.5)
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.shading.type = 'MATERIAL'
        area.spaces.active.overlay.show_overlays = False
scene.render.filepath = str(evidencePath / (MAP+'_blender.png'))
if globals().get('DECORATION_REVIEW'):
    exec(compile((root/'level_generation/scripts/blender_decoration_views.py').read_text(),
                 'blender_decoration_views.py','exec'),globals())
elif globals().get('STUDY_VIEWS'):
    output = Path(OUTPUT_DIRECTORY)
    output.mkdir(parents=True, exist_ok=True)
    for view in STUDY_VIEWS:
        camera.location = Vector(view['position']) / 128
        target = Vector(view['target']) / 128
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale = view['scale'] / 128
        scene.render.filepath = str(output / (view['id']+'.png'))
        bpy.ops.render.render(write_still=True)
    (output/(MAP+'_views.json')).write_text(json.dumps(dict(source=str(path.relative_to(root)),
        views=STUDY_VIEWS, missing_textures=sorted(missing),
        limitations='Native terrain/BModels; inspection lighting, no actors or decoration sprites.'),indent=2)+'\n')
else:
    bpy.ops.render.render(write_still=True)
if not globals().get('DECORATION_REVIEW') and not globals().get('STUDY_VIEWS'):
    (evidencePath/(MAP+'_blender.json')).write_text(json.dumps({
    'source':str(path.relative_to(root)), 'kind':KIND,
    'view':'ceiling-free isometric' if KIND=='indoor' else 'heightfield and BModel isometric',
    'camera_position':list(camera.location),'camera_target':list(center),
    'scale_game_units_per_blender_unit':128,'missing_textures':sorted(missing),
    'limitations':'Inspection lighting; no actors, decoration billboards, gameplay state, or animated water compositing'
    },indent=2)+'\n')
print('Rendered',WORLD,MAP,'missing textures:',sorted(missing))
