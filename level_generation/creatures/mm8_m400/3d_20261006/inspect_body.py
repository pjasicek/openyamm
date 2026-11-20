import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'meshy/body_geometry_v1/model_urls_glb.glb'
OUT = ROOT / 'body_review_v1'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
points = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
height = hi.z - lo.z
for o in meshes:
    o.location.z -= lo.z
    o.location *= 1.7 / height
    o.scale *= 1.7 / height
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.select_set(False)
    o.name = 'Lizardman_Body'
report = {'input': str(SOURCE), 'authoring_height_m': 1.7, 'objects': []}
for o in meshes:
    bm = bmesh.new(); bm.from_mesh(o.data)
    remaining = set(bm.verts); components = []
    while remaining:
        seen = {remaining.pop()}
        stack = list(seen)
        while stack:
            current = stack.pop()
            for edge in current.link_edges:
                v = edge.other_vert(current)
                if v in remaining:
                    remaining.remove(v); seen.add(v); stack.append(v)
        components.append({'vertices':len(seen), 'bounds':[[min(v.co[i] for v in seen) for i in range(3)], [max(v.co[i] for v in seen) for i in range(3)]]})
    report['objects'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'components':components,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'uv_layers':[u.name for u in o.data.uv_layers]})
    bm.free()
(OUT/'mesh_inspection.json').write_text(json.dumps(report,indent=2))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640; scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('Review_World')
scene.world.color = (.22,.22,.22)
scene.view_settings.view_transform = 'Standard'
bpy.ops.object.camera_add()
camera = bpy.context.object; camera.name = 'Review_Camera'
camera.data.type = 'ORTHO'; camera.data.ortho_scale = 1.95
scene.camera = camera
for location, energy, size in [((3,-4,5),350,4),((-3,-2,3),220,4),((1,3,4),280,3)]:
    bpy.ops.object.light_add(type='AREA',location=location)
    light=bpy.context.object; light.data.energy=energy; light.data.shape='DISK'; light.data.size=size
    light.rotation_euler=(Vector((0,0,.85))-light.location).to_track_quat('-Z','Y').to_euler()
for mode in ('textured','clay'):
    if mode=='clay':
        scene.render.engine='BLENDER_WORKBENCH'
        scene.display.shading.light='STUDIO'; scene.display.shading.color_type='SINGLE'
        scene.display.shading.single_color=(.6,.6,.6)
        scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=True
        scene.display.shading.background_type='WORLD'
    for name, direction in [('front',(0,-5,0)),('quarter',(-3,-5,.1)),('profile',(-5,0,0)),('back',(0,5,0))]:
        center=Vector((0,0,.85)); camera.location=center+Vector(direction)
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/f'{mode}_{name}.png')
        bpy.ops.render.render(write_still=True)
    for name,center,scale in [('head',(0,-.05,1.48),.6),('hands',(0,0,.85),1.15),('feet',(0,0,.18),.6)]:
        center=Vector(center); camera.data.ortho_scale=scale; camera.location=center+Vector((0,-5,0))
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/f'{mode}_{name}.png'); bpy.ops.render.render(write_still=True)
    camera.data.ortho_scale=1.95
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'body_v1.blend'))
print(json.dumps(report),flush=True)
