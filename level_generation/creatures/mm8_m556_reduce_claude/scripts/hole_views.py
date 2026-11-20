"""Close-ups of the open-edge loops (joint-ball rims, small 5-edge loops) straight from a GLB, with back-face culling
as in the engine, in rest (Fly 0) and two Attack frames; magenta background so holes read. Usage:
blender -b -P hole_views.py -- <label> <glb>  -> review/holes/<label>_<spot>_<frame>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
label, glb = sys.argv[sys.argv.index('--') + 1:][:2]
out = os.path.join(HERE, 'review', 'holes'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Wasp')
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_render = True
for m in body.data.materials:
    m.use_backface_culling = True
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 360
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.show_backface_culling = True
sc.display.shading.background_type = 'VIEWPORT'; sc.display.shading.background_color = (1, 0, 1)
sc.display.shading.color_type = 'TEXTURE'
# rest-pose centres of the open-edge loops (work/source.blend probe), six view directions each, rest pose only
LOOPS = {'shoulder_l': (0.061, -0.034, 0.584), 'midleg_l1': (0.049, 0.029, 0.519), 'midleg_l2': (0.034, 0.029, 0.527),
         'midleg_r': (-0.039, 0.029, 0.527), 'claw2_r': (-0.272, -0.072, 0.47), 'thorax': (-0.062, 0.067, 0.589),
         'forearm_r': (-0.16, 0.007, 0.518)}
DIRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
sc.frame_set(0)
for spot, c in LOOPS.items():
    c = body.matrix_world @ Vector(c)
    for k, d in enumerate(DIRS):
        cam.location = c + Vector(d) * 2
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = .09
        sc.render.filepath = os.path.join(out, f'{label}_{spot}_{k}.png'); bpy.ops.render.render(write_still=True)
print('HOLES done')
