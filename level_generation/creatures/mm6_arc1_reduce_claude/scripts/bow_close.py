"""Close renders of a bow GLB (clay with cavity): upper tip, grip and limb middle, side view (bow plane).
Usage: blender -b -P bow_close.py -- <glb> <label>  -> review/props/close_<label>_<spot>.png"""
import bpy, sys, os
from mathutils import Vector
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
for o in bpy.data.objects:
    if o.type == 'MESH' and 'LOD' in o.name: o.hide_render = True
sc = bpy.context.scene; sc.render.resolution_x = sc.render.resolution_y = 500
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
o = next(o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render)
pts = [o.matrix_world @ v.co for v in o.data.vertices]
top = max(pts, key=lambda p: p.z); mid = sum(pts, Vector()) / len(pts)
spots = {'tip': (top + Vector((0, 0, -0.05)), 0.16), 'grip': (mid, 0.22), 'limb': ((top + mid) / 2, 0.3)}
for k, (t, s) in spots.items():
    cam.data.ortho_scale = s; cam.location = t + Vector((1, 0, 0)); cam.rotation_euler = (Vector((-1, 0, 0))).to_track_quat('-Z', 'Z').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', 'props', f'close_{label}_{k}.png'); bpy.ops.render.render(write_still=True)
