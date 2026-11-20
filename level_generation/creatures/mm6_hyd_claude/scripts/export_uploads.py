"""Meshy retexture uploads from work/hd_atlas.blend (uv_atlas.py): texturing/hyd_body_upload.glb (part 0) and
texturing/hyd_head<k>_upload.glb (part k), each with only its 'Upload' UVs (0..1). A head is turned about Z so its
snout's horizontal direction is -Y (the creature front) and centred, so its four reference views are plain front/left/
back/right; texturing/head_frames.json records the turn. Also renders grey shape guides of every head for the Codex
head turnaround (references_heads/h<k>/shape_<view>.png, 1024², transparent).
  blender --background work/hd_atlas.blend --python scripts/export_uploads.py"""
import bpy, bmesh, json, math, os
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'texturing'); os.makedirs(OUT, exist_ok=True)
rig = json.load(open(os.path.join(HERE, 'work', 'rig.json')))
src = bpy.data.objects['Hydra']
part = np.zeros(len(src.data.polygons), int); src.data.attributes['part'].data.foreach_get('value', part)
frames = {}
VIEWS = {'front': (0, -1, 0), 'left': (1, 0, 0), 'back': (0, 1, 0), 'right': (-1, 0, 0)}   # camera positions


def piece(k):
    me = src.data.copy(); o = bpy.data.objects.new(f'Part{k}', me); bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if part[f.index] != k], context='FACES')
    bm.to_mesh(me); bm.free()
    me.uv_layers.remove(me.uv_layers['UVMap']); me.uv_layers['Upload'].name = 'UVMap'
    for a in [a for a in me.attributes if a.name == 'part']:
        me.attributes.remove(a)
    me.materials.clear()
    mat = bpy.data.materials.new(f'Part{k}'); me.materials.append(mat)
    return o


def export(o, path):
    for x in bpy.context.view_layer.objects:
        x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_texcoords=True, export_normals=True, export_materials='PLACEHOLDER')


src.hide_render = True
body = piece(0); export(body, os.path.join(OUT, 'hyd_body_upload.glb')); body.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.62, 0.62, 0.62); sh.show_cavity = True
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 1024
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
for k in range(1, 6):
    J = np.array(rig['chains'][k]['joints'])
    fwd = J[-1] - J[-2]; yaw = math.atan2(fwd[0], -fwd[1])         # angle from -Y to the snout's horizontal direction
    o = piece(k)
    co = np.array([tuple(v.co) for v in o.data.vertices]); centre = (co.min(0) + co.max(0)) / 2
    m = Matrix.Rotation(-yaw, 4, 'Z') @ Matrix.Translation(-Vector(centre))
    o.data.transform(m); o.data.update()
    frames[k] = {'yaw_radians': yaw, 'centre': centre.round(5).tolist()}
    export(o, os.path.join(OUT, f'hyd_head{k}_upload.glb'))
    co = np.array([tuple(v.co) for v in o.data.vertices]); size = float((co.max(0) - co.min(0)).max())
    d = os.path.join(HERE, 'references_heads', f'h{k}'); os.makedirs(d, exist_ok=True)
    for name, pos in VIEWS.items():
        p = Vector(pos); cam.location = p * 3; cam.data.ortho_scale = size * 1.45
        cam.rotation_euler = (-p).to_track_quat('-Z', 'Z' if abs(p.z) < 0.9 else 'Y').to_euler()
        sc.render.filepath = os.path.join(d, f'shape_{name}.png'); bpy.ops.render.render(write_still=True)
    o.hide_render = True
    print('HEAD', k, 'triangles', sum(len(p.vertices) - 2 for p in o.data.polygons), 'yaw', round(math.degrees(yaw), 1))
json.dump(frames, open(os.path.join(OUT, 'head_frames.json'), 'w'), indent=1)
print('EXPORTED uploads')
