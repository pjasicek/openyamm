"""Filmstrip of Death frames 22-38 from viewer GLBs (side three-quarter, textured, floor line at 0):
review/death/strip_<label>.png. Usage: blender -b -P death_strip.py -- <label>=<viewer glb> [...]"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'death'); os.makedirs(out, exist_ok=True)
for item in sys.argv[sys.argv.index('--') + 1:]:
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.name == 'Icosphere':
            o.hide_render = True
    bpy.ops.mesh.primitive_plane_add(size=4); fl = bpy.context.object
    m = bpy.data.materials.new('F'); m.diffuse_color = (.25, .25, .27, 1); fl.data.materials.append(m)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); act = bpy.data.actions['Death']; rig.animation_data.action = act
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.7; c = Vector((0, 0.35, 0.45))
    cam.location = c + Vector((1, -.35, .12)).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x = sc.render.resolution_y = 300
    fps = sc.render.fps / sc.render.fps_base; f0 = act.frame_range[0]
    for i in range(22, 39):
        fr = f0 + i / 48 * fps; sc.frame_set(int(fr), subframe=fr - int(fr))
        sc.render.filepath = os.path.join(out, f'_{label}_{i:02d}.png'); bpy.ops.render.render(write_still=True)
print('STRIP done')
