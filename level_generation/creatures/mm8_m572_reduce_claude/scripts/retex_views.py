"""Matched close-ups of a tier-baked viewer GLB for the retexture check: clay (workbench studio, no cavity: shows the
stored normals) and textured (Eevee, fixed sun). Views follow the creature's own forward axis (Head - body bone).
Usage: blender -b -P retex_views.py -- <glb> <out dir> <label> <modes clay,tex> <body bone> <wing bone L> <wing bone R> <foot bone> <tail bone>"""
import math, os, sys, bpy
import numpy as np
from mathutils import Vector
glb, out, label, modes, BODY, WL, WR, FOOT, TAIL = sys.argv[sys.argv.index('--') + 1:][:9]
modes = modes.split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('Icosphere' in o.name or 'Flame' in o.name):
        o.hide_render = True
acts = {a.name.rsplit('|', 1)[-1]: a for a in bpy.data.actions}
pb = rig.pose.bones
def setact(name, f):
    a = acts[name]; rig.animation_data.action = a
    if getattr(a, 'slots', None): rig.animation_data.action_slot = a.slots[0]
    sc.frame_set(f)
mid = lambda n: rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2)
# open-mouth frame: Attack frame with the largest Head-tail to Jaw-tail distance
a = acts['Attack']; f0, f1 = (int(x) for x in a.frame_range); best = (0, f0)
for f in range(f0, f1 + 1):
    setact('Attack', f); dd = ((rig.matrix_world @ pb['Head'].tail) - (rig.matrix_world @ pb['Jaw'].tail)).length
    best = max(best, (dd, f))
OPEN = best[1]
IDLE = 'Standing' if 'Standing' in acts else 'Fly'
setact(IDLE, 0)
fwd = mid('Head') - mid(BODY); fwd.z = 0; fwd.normalize(); right = fwd.cross(Vector((0, 0, 1))).normalized(); up = Vector((0, 0, 1))
D = lambda f, r, u: (fwd * f + right * r + up * u).normalized()
headlen = (rig.matrix_world @ pb['Head'].tail - rig.matrix_world @ pb['Head'].head).length
H = max(.16, headlen * 3.2)
SPOTS = [('head_front', IDLE, 0, 'Head', H, D(1, 0, .15)), ('head_side', IDLE, 0, 'Head', H, D(0, 1, .1)),
         ('head_q34', IDLE, 0, 'Head', H, D(.7, -.7, .3)), ('mouth_open', 'Attack', OPEN, 'Head', H * 1.1, D(.35, .9, .2)),
         ('neck_join', IDLE, 0, 'Head', H * 2.2, D(-.2, 1, .25)), ('flank_r', IDLE, 0, BODY, .55, D(0, 1, .05)),
         ('flank_l', IDLE, 0, BODY, .55, D(0, -1, .05)), ('belly', IDLE, 0, BODY, .55, D(.2, .3, -1)),
         ('wing_top', IDLE, 0, WL, .6, D(-.1, -.3, 1)), ('wing_under', IDLE, 0, WR, .6, D(.1, .3, -1)),
         ('feet', IDLE, 0, FOOT, .22, D(.5, .8, .1)), ('tail', IDLE, 0, TAIL, .45, D(-.3, 1, .4))]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 20
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.2
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.36, .36, .4, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 360
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.8, .78, .74); sh.show_cavity = False
os.makedirs(out, exist_ok=True)
for spot, act, f, bone, size, dv in SPOTS:
    setact(act, f); c = mid(bone)
    cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    for mode in modes:
        sc.render.engine = 'BLENDER_WORKBENCH' if mode == 'clay' else 'BLENDER_EEVEE'
        sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png'); bpy.ops.render.render(write_still=True)
print('RETEXVIEWS', label, 'open frame', OPEN, [s[0] for s in SPOTS])
