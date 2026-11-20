"""Close renders of the main head and the creature's left arm head (bind pose), for the Codex head brief (shape
renders of our own head geometry; textured renders of the MM9 model) and for the before/after sheet.

Args: <.glb or .blend> <out dir> <prefix> <mode> [size]
mode: tex (textured, whole model), grey (whole model, grey), shape (a .blend with the 'head' face attribute: only that
head's faces, grey; the exact shape Meshy will paint). Camera framing comes from the bones, so every input gets the
same cameras. Views per head: front, q34 (main: from the creature's right front; arm: from its outer front), profile
(the creature's LEFT side, snout to image left), back (from behind and above)."""
import bpy, bmesh, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, PRE, MODE = a[:4]
SIZE = int(a[4]) if len(a) > 4 else 768
os.makedirs(OUT, exist_ok=True)
if SRC.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=SRC)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == 'ARMATURE')
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
for o in sc.objects:
    if o.type == 'MESH' and o.name.startswith('Icosphere'):
        o.hide_render = True
J = lambda n: rig.matrix_world @ rig.data.bones[n].head_local
HEADS = {
    'main': (J('Xhead') * 0.5 + J('Xhjaw') * 0.5 + Vector((0, -0.05, 0.12)), 1.75, 1,
             {'front': (0, -1, 0.15), 'q34': (-0.75, -1, 0.3), 'profile': (1, 0, 0.05), 'back': (0, 1, 0.25)}),
    'arm': (J('Xahead01') * 0.6 + J('Xajaw01') * 0.4 + Vector((0, 0.05, 0.0)), 0.95, 2,
            {'front': (0, -1, 0.1), 'q34': (0.75, -1, 0.3), 'profile': (1, 0, 0.05), 'back': (0, 1, 0.6)}),
}
body = None
if MODE == 'shape':
    body = next(o for o in sc.objects if o.type == 'MESH' and 'head' in o.data.attributes)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'TEXTURE' if MODE == 'tex' else 'SINGLE'
sh.single_color = (0.62, 0.62, 0.6)
sh.show_backface_culling = False
sh.show_cavity = MODE != 'tex'
sc.render.resolution_x = sc.render.resolution_y = SIZE
sc.render.film_transparent = MODE == 'shape'
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
orig = body.data.copy() if body else None
for hn, (c, scale, hid, views) in HEADS.items():
    if body:
        body.data = orig.copy()
        bm = bmesh.new(); bm.from_mesh(body.data)
        hl = bm.faces.layers.int['head']
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] != hid], context='FACES')
        bm.to_mesh(body.data); bm.free()
    cd.ortho_scale = scale
    for vn, d in views.items():
        d = Vector(d).normalized()
        cam.location = c + d * 10
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, f'{PRE}_{hn}_{vn}.png')
        bpy.ops.render.render(write_still=True)
print('HEADS', PRE)
