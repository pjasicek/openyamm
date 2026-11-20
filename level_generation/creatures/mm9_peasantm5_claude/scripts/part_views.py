"""Close-up renders of a runtime GLB around named joints at given clip frames (texture pass 2026-10-30: Yrsa's shoes
at bind and in Hit, from the side and from below; usable for any part).

Args: -- <glb> <out png> <clip:frame48[,...]> <joint[,joint...]> [views: side,oside,front,back,below,below_side,q34,
       above34,above34r,front_low] [half width m]
       [xray | magenta]
`bind` as the clip renders the rest pose. Writes <out>.list (row names) for compare_rows.py. One row per clip:frame,
one column per view; the camera looks at the mean of the joints' world positions (orthographic, half width default
0.25 m). Workbench, the GLB's own textures; `xray` renders the whole model see-through instead (shape only);
`magenta` keeps the textures on a magenta background (holes and culled back faces show as magenta).
"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items, joints = a[0], a[1], a[2].split(','), a[3].split(',')
views = (a[4] if len(a) > 4 else 'side,front,below').split(',')
half = float(a[5]) if len(a) > 5 else 0.25
xray = len(a) > 6 and a[6] == 'xray'
magenta = len(a) > 6 and a[6] == 'magenta'     # see-through check: background shows as pure magenta
parts = len(a) > 6 and a[6] == 'parts'         # mm9_peasantm7: head+hands material red, body material grey (where is skin?)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'SINGLE' if xray else ('MATERIAL' if parts else 'TEXTURE')
if parts:
    for m in bpy.data.materials:
        m.diffuse_color = (0.85, 0.1, 0.1, 1) if 'Head' in m.name else (0.6, 0.6, 0.6, 1)
sh.show_backface_culling = not xray            # as the game: single-sided materials cull their back faces
if xray:
    sh.show_xray = True
    sh.xray_alpha = 0.35
sc.render.resolution_x = sc.render.resolution_y = 420
sc.world = bpy.data.worlds.new('W'); sc.world.color = (1.0, 0.0, 1.0) if magenta else (0.55, 0.58, 0.62)
sc.render.fps = 48
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'
cd.ortho_scale = 2 * half
# front = -Y (glb_frames.py convention), side = +X; below looks up from under the joint, slightly from the front
DIRS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'side': (1, 0, 0), 'oside': (-1, 0, 0), 'q34': (0.57, -0.82, 0),
        'below': (0, -0.35, -1), 'below_side': (0.6, 0, -1),
        'above34': (-0.45, -0.75, 0.55), 'above34r': (0.45, -0.75, 0.55), 'front_low': (0, -1, -0.25)}
tiles = []
tmp = os.path.join(os.path.dirname(os.path.abspath(out)), '_part_views_tmp')
os.makedirs(tmp, exist_ok=True)
for it in items:
    clip, f = it.split(':')
    if rig.animation_data is None:
        rig.animation_data_create()
    if clip == 'bind':
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        act = bpy.data.actions[clip] if clip in bpy.data.actions else \
            next(x for x in bpy.data.actions if x.name.startswith(clip))
        rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        t = float(f) / 48.0                    # glTF import keys at 24 fps: map 48 fps frames to seconds
        sc.frame_set(int(t * 24), subframe=(t * 24) % 1.0)
    bpy.context.view_layer.update()
    c = sum((rig.matrix_world @ rig.pose.bones[j].head for j in joints), Vector()) / len(joints)
    row = []
    for v in views:
        d = Vector(DIRS[v]).normalized()        # camera position offset from the target
        cam.location = c + d * 3.0
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        p = os.path.join(tmp, f'{len(tiles)}_{len(row)}.png')
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        row.append(p)
    tiles.append((it, row))
import numpy as np
imgs = []
for it, row in tiles:
    ims = []
    for p in row:
        im = bpy.data.images.load(p)
        px = np.array(im.pixels[:]).reshape(im.size[1], im.size[0], 4)[::-1]
        ims.append(px)
    imgs.append(np.concatenate(ims, 1))
sheet = np.concatenate(imgs, 0)
h, w = sheet.shape[:2]
img = bpy.data.images.new('sheet', w, h, alpha=True)
img.pixels.foreach_set(sheet[::-1].ravel().astype(np.float32))
img.filepath_raw = out; img.file_format = 'PNG'; img.save()
open(out + '.list', 'w').write('\n'.join(it + '\t' + '\t'.join(r) for it, r in tiles))   # compare_rows.py
print('PART_VIEWS', out, [t[0] for t in tiles], views)
