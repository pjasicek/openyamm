import bpy, sys, math
from mathutils import Vector
glb, out, clip, frame = sys.argv[sys.argv.index('--') + 1:][:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
act = next(a for a in bpy.data.actions if a.name.startswith(clip))
rig.animation_data.action = act; bpy.context.scene.frame_set(int(frame))
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); bpy.context.scene.collection.objects.link(cam)
cam.location = (0.0, -1.6, 0.18); d = Vector((0, 0, 0.1)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 45
sc = bpy.context.scene; sc.camera = cam; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 900, 420; sc.render.filepath = out
bpy.ops.render.render(write_still=True)
