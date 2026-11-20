"""Identical-camera stills for the texture quality pass (2026-10-30): one labelled row per variant, columns face front,
face 3/4, left hand, right hand, torso (body texture close-up), full body front and full body 3/4. Rest pose
(Standing frame 0), Workbench studio light with the GLB's own textures (as glb_frames.py).

Args (Blender): <out png> <variant> [<variant> ...]
variant = <label>@<glb>[@<image substring>=<png>[@...]]: overrides replace every material image whose name contains
the substring (a grade candidate, a raw Meshy colour or a density heatmap on the same model).
Writes <out> and <out>.list (row labels, for compare_rows.py)."""
import bpy, sys, os
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
OUT, VARIANTS = a[0], a[1:]
S = 400
VIEWS = ('face', 'face34', 'handL', 'handR', 'torso', 'front', 'q34')
rows, labels = [], []
tmp = os.path.join(os.path.dirname(os.path.abspath(OUT)), '_texpass_shots_tmp')
os.makedirs(tmp, exist_ok=True)
for vi, var in enumerate(VARIANTS):
    parts = var.split('@')
    label, glb, overrides = parts[0], parts[1], dict(p.split('=', 1) for p in parts[2:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = any(t in o.name for t in ('LOD', 'Shadow'))
    for key, path in overrides.items():
        img = bpy.data.images.load(path)
        for im in list(bpy.data.images):
            if key in im.name and im is not img:
                im.user_remap(img)
    if 'Standing' in bpy.data.actions:
        rig.animation_data_create()
        rig.animation_data.action = bpy.data.actions['Standing']
        act = bpy.data.actions['Standing']
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
    sc = bpy.context.scene
    sc.frame_set(0)
    bpy.context.view_layer.update()
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'TEXTURE'
    sc.render.resolution_x = sc.render.resolution_y = S
    sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.55, 0.58, 0.62)
    cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam)
    sc.camera = cam
    cd.type = 'ORTHO'
    pb = rig.pose.bones
    W = lambda b: rig.matrix_world @ b.head
    head = next(b for b in pb if b.name.endswith(' Head') and 'Finger' not in b.name)
    spine = next(b for b in pb if b.name.endswith('Spine2'))
    P = np.array([tuple(W(b)) for b in pb])
    lo, hi = P.min(0) - 0.12, P.max(0) + 0.12
    lo[2] = min(lo[2], 0.0)
    hgt = hi[2] - lo[2]
    row = []
    for v in VIEWS:
        if v in ('face', 'face34'):
            tgt = W(head) + Vector((0, 0, 0.06))
            d = Vector((0, -1, 0)) if v == 'face' else Vector((0.7, -0.7, 0)).normalized()
            cd.ortho_scale = 0.34
        elif v.startswith('hand'):
            tok = ' L ' if v == 'handL' else ' R '
            hb = next(b for b in pb if tok in b.name and b.name.endswith('Hand'))
            p, q = rig.matrix_world @ hb.head, rig.matrix_world @ hb.tail
            tgt = p + (q - p).normalized() * 0.06
            d = Vector((0, -1, 0.25)).normalized()
            cd.ortho_scale = 0.30
        elif v == 'torso':
            tgt = W(spine)
            d = Vector((0.35, -1, 0)).normalized()
            cd.ortho_scale = 0.62
        else:
            tgt = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2] + hgt * 0.5))
            d = Vector((0, -1, 0.07)).normalized() if v == 'front' else Vector((0.6, -0.8, 0.07)).normalized()
            cd.ortho_scale = max(hgt, hi[0] - lo[0], hi[1] - lo[1]) * 1.05
        cam.location = tgt + d * 4.0
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        fn = os.path.join(tmp, f'{vi}_{len(row)}.png')
        sc.render.filepath = fn
        bpy.ops.render.render(write_still=True)
        row.append(fn)
    rows.append(row)
    labels.append(label)
tiles = []
for row in rows:
    ims = []
    for p in row:
        im = bpy.data.images.load(p)
        ims.append(np.array(im.pixels[:]).reshape(im.size[1], im.size[0], 4)[::-1])
    tiles.append(np.concatenate(ims, 1))
sheet = np.concatenate(tiles, 0)
h, w = sheet.shape[:2]
img = bpy.data.images.new('sheet', w, h, alpha=True)
img.pixels.foreach_set(sheet[::-1].ravel().astype(np.float32))
img.filepath_raw = OUT; img.file_format = 'PNG'; img.save()
open(OUT + '.list', 'w').write('\n'.join(l + '\t' + '\t'.join(r) for l, r in zip(labels, rows)))
print('TEXPASS_SHOTS', OUT, labels, VIEWS)
