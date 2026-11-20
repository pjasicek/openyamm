"""Before/after floor renders of the corpse (review GLBs with the rifle joined, add_rifle.py): Death at several times
and Dead, side and front, over a floor plane at y = 0 (the actor's floor). 30 fps import.
Usage: blender -b -P floor_view.py -- <out dir> <label=glb> [...]  -> <out dir>/<label>_<clip><t>_<view>.png"""
import bpy, os, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]
SHOTS = [('Death', 1.0), ('Death', 1.6), ('Death', 2.4), ('Death', 3.43), ('Dead', 0.5)]
for item in a[1:]:
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); pl = bpy.context.object
    m = bpy.data.materials.new('Floor'); m.diffuse_color = (.25, .45, .28, 1); pl.data.materials.append(m)
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.4
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x, sc.render.resolution_y = 480, 300
    for clip, t in SHOTS:
        act = bpy.data.actions[clip]; rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        sc.frame_set(int(round(t * 30)))
        p = rig.matrix_world @ rig.pose.bones['B_Pelvis'].head; c = Vector((p.x, p.y, .45))
        for view, d in (('side', (1, 0, .04)), ('front', (0, -1, .04))):
            cam.location = c + Vector(d).normalized() * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f'{label}_{clip}{t}_{view}.png'); bpy.ops.render.render(write_still=True)
print('FLOORVIEW done')
