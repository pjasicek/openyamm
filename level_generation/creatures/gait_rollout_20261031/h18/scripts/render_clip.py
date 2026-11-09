"""Filmstrip of GLB clips: side and front views at evenly spaced phases (Workbench, textured), one PNG per clip.

Blender, background: -- <in.glb> <out_prefix> <clip>[,<clip>...] [frames=8] [views=side,front] [size=260]
Writes <out_prefix>_<clip>.png: rows = views, columns = phases 0..(n-1)/n of the loop. A floor line is drawn at y = 0
(a thin dark plane edge) so contact can be judged.
"""
import bpy
import math
import os
import sys

args = sys.argv[sys.argv.index('--') + 1:]
glb, prefix, clips = args[0], args[1], args[2].split(',')
opts = dict(a.split('=', 1) for a in args[3:])
n = int(opts.get('frames', 8))
views = opts.get('views', 'side,front').split(',')
size = int(opts.get('size', 260))
attach = [p for p in opts.get('attach', '').split(';') if p]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and any(k in o.name or k in o.data.name for k in ('LOD1', 'LOD2', 'LOD3', 'Shadow')):
        o.hide_render = True
for path in attach:
    # attachments: GLB with its own copy of the armature's bone node; parent it to that bone
    node, file = path.split('=', 1)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(file))
    new = set(bpy.data.objects) - before
    for o in new:
        if o.type == 'ARMATURE':
            for child in [c for c in new if c.parent == o]:
                pass
    # simple route: parent every mesh of the attachment to the bone with its world transform at rest
    for o in new:
        if o.type == 'MESH':
            mw = o.matrix_world.copy()
            o.parent = arm
            o.parent_type = 'BONE'
            o.parent_bone = node
            bpy.context.view_layer.update()
            o.matrix_world = mw
    for o in new:
        if o.type in ('ARMATURE', 'EMPTY') and not o.children:
            pass

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
sh = scene.display.shading
sh.light = 'STUDIO'
sh.color_type = 'TEXTURE'
sh.show_shadows = False
sh.background_type = 'VIEWPORT'
sh.background_color = (0.86, 0.86, 0.84)
scene.render.resolution_x = size
scene.render.resolution_y = int(size * 1.35)
scene.render.film_transparent = False
# floor: a thin dark slab at z = 0
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.001))
floor = bpy.context.object
mat = bpy.data.materials.new('floor')
mat.diffuse_color = (0.35, 0.33, 0.3, 1)
floor.data.materials.append(mat)
cam_data = bpy.data.cameras.new('cam')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 2.3
cam = bpy.data.objects.new('cam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
# the pirates face -Y in Blender (glTF +Z); side = camera on the character's left (+X), looking -X
POSES = {'side': ((5.0, 0.0, 0.95), (math.radians(90), 0, math.radians(90))),
         'front': ((0.0, -5.0, 0.95), (math.radians(90), 0, 0)),
         'back': ((0.0, 5.0, 0.95), (math.radians(90), 0, math.radians(180))),
         'quarter': ((3.5, -3.5, 1.0), (math.radians(88), 0, math.radians(45))),
         'low': ((5.0, 0.0, 0.25), (math.radians(90), 0, math.radians(90))),
         'frontclose': ((0.0, -5.0, 0.6), (math.radians(90), 0, 0)),
         'backclose': ((0.0, 5.0, 0.6), (math.radians(90), 0, math.radians(180))),
         'quarterclose': ((3.5, -3.5, 0.6), (math.radians(90), 0, math.radians(45)))}
for clip in clips:
    act = next((a for a in bpy.data.actions if a.name == clip or a.name.startswith(clip + '_')
                or a.name.split('|')[-1] == clip), None)
    if act is None:
        raise SystemExit(f'no action for {clip}: {[a.name for a in bpy.data.actions]}')
    arm.animation_data_create()
    arm.animation_data.action = act
    if len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    fps = scene.render.fps / scene.render.fps_base
    for view in views:
        loc, rot = POSES[view]
        cam.location = loc
        cam.rotation_euler = rot
        cam_data.ortho_scale = 1.2 if view == 'low' or view.endswith('close') else 2.3
        for i in range(n):
            f = f0 + (f1 - f0) * i / n
            scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
            scene.render.filepath = f'{prefix}_{clip}__{view}__{i:02d}.png'
            bpy.ops.render.render(write_still=True)
    print('RENDER', clip, f'frames {f0}-{f1}')
