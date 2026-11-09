"""Gog close-ups straight from GLBs (no weld, the file's own normals), clay and textured: head front / side / three-
quarter, open mouth (Attack), right hand, right foot, tail barb, back. Every colour mesh but LOD0 hidden.
Usage: blender -b -P gog_close.py -- <label=glb,...> [spots]  -> review/close/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
SPOTS = {'head_front': ('Standing', 0, 'B_Head', .42, (0, -1, .1)), 'head_side': ('Standing', 0, 'B_Head', .42, (1, 0, .1)),
         'head_tq': ('Standing', 0, 'B_Head', .42, (.7, -.7, .25)), 'mouth': ('Attack', 'open', 'B_Head', .26, (.35, -1, .05), (0, -.08, -.08)),
         'hand': ('Standing', 0, 'B_R_Hand', .34, (-.4, -1, .2)), 'foot': ('Standing', 0, 'B_R_Foot', .40, (.5, -1, .35)),
         'tail': ('Standing', 0, 'Tail08', .55, (1, .2, .1)), 'back': ('Standing', 0, 'B_Spine1', 1.0, (.3, 1, .2)),
         'whole': ('Standing', 0, 'B_Spine', 1.95, (.6, -1, .15))}
args = sys.argv[sys.argv.index('--') + 1:]
pick = args[1].split(',') if len(args) > 1 else list(SPOTS)
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
            o.hide_render = True
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    acts = {a.name.rsplit('|', 1)[-1]: a for a in bpy.data.actions}
    def setact(n, f):
        a = acts[n]; rig.animation_data.action = a
        if getattr(a, 'slots', None):
            rig.animation_data.action_slot = a.slots[0]
        sc.frame_set(f)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    pb = rig.pose.bones
    for spot in pick:
        act, frame, b, size, d = SPOTS[spot][:5]; off = Vector(SPOTS[spot][5]) if len(SPOTS[spot]) > 5 else Vector()
        if frame == 'open':   # Attack frame with the jaw lowest relative to the head (largest head-to-chin spread)
            a = acts[act]; f0, f1 = (int(x) for x in a.frame_range); best = (-1, f0)
            jaw = 'Jaw' if 'Jaw' in pb else None
            for f in range(f0, f1 + 1):
                setact(act, f)
                dd = ((rig.matrix_world @ pb['B_Head'].tail) - (rig.matrix_world @ pb[jaw].tail)).length if jaw else 0
                best = max(best, (dd, f))
            frame = best[1] if jaw else (f0 + f1) // 2
        setact(act, frame)
        c = rig.matrix_world @ ((pb[b].head + pb[b].tail) / 2) + off
        cam.location = c + Vector(d).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
