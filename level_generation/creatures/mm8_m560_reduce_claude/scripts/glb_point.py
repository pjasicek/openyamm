"""Clay close-ups of GLBs at given clip frames and world points (diagnostics).
Usage: blender -b -P glb_point.py -- <label=glb,...> <name:clip:frame:x:y:z:size:dx:dy:dz;...>  -> review/glbclose/<label>_<name>_clay.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(HERE, 'review', 'glbclose')
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 20; sc.render.resolution_x = sc.render.resolution_y = 420
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.8, .78, .74)
    for spec in args[1].split(';'):
        name, clip, frame, x, y, z, size, dx, dy, dz = spec.split(':')
        a = next(q for q in bpy.data.actions if q.name.rsplit('|', 1)[-1] == clip)
        rig.animation_data.action = a
        if a.slots:
            rig.animation_data.action_slot = a.slots[0]
        sc.frame_set(int(frame)); c = Vector((float(x), float(y), float(z)))
        cam.location = c + Vector((float(dx), float(dy), float(dz))).normalized() * 3
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = float(size)
        sc.render.filepath = os.path.join(out, f'{label}_{name}_clay.png'); bpy.ops.render.render(write_still=True)
print('POINTS done')
