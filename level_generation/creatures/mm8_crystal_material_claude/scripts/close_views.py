"""Textured close-ups of a Crystal Dragon GLB imported as is (rest pose of Standing frame 0): head, crown, neck, front and
hind legs from several angles, base colour under soft studio light (the browser/engine gloss is not reproduced; this
judges the painted texture). Usage: blender -b -P close_views.py -- <glb> <label>  -> review/close/<label>_<view>.png"""
import math, os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; glb, label = a[0], a[1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name not in ('CrystalDragon',):
        o.hide_render = True
for m in bpy.data.materials:
    if m.use_nodes:
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b:
            b.inputs['Roughness'].default_value = 0.6
            for l in list(b.inputs['Roughness'].links) + list(b.inputs['Metallic'].links):
                m.node_tree.links.remove(l)
            b.inputs['Metallic'].default_value = 0.0
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.45, .45, .48, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
for rot, e in (((50, 0, -30), 2.5), ((60, 0, 150), 1.0)):
    s = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); s.data.energy = e; sc.collection.objects.link(s)
    s.rotation_euler = tuple(math.radians(v) for v in rot)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 520
# glTF +Y up, +Z forward -> Blender +Z up, -Y forward
VIEWS = {  # name: (target in glTF coordinates, view direction from target to camera in glTF coordinates, ortho)
    'head_side': ((0, 0.68, 0.40), (1, 0.1, 0), 0.24), 'head_quarter': ((0, 0.68, 0.40), (0.7, 0.25, 0.7), 0.24),
    'head_front': ((0, 0.68, 0.40), (0, 0.15, 1), 0.24), 'crown_back': ((0, 0.74, 0.32), (0.5, 0.6, -0.6), 0.26),
    'neck_side': ((0, 0.52, 0.28), (1, 0.05, 0.1), 0.34), 'neck_front': ((0, 0.52, 0.30), (0.4, 0.1, 1), 0.34),
    'foreleg': ((0.15, 0.18, 0.25), (1, 0.2, 0.5), 0.36), 'hindleg': ((0.15, 0.18, -0.2), (1, 0.2, -0.4), 0.36),
    'body_top': ((0, 0.45, 0.0), (0.5, 1, 0.2), 0.7),
}
for name, (t, d, scale) in VIEWS.items():
    target = Vector((t[0], -t[2], t[1])); direction = Vector((d[0], -d[2], d[1])).normalized()
    cam.data.ortho_scale = scale; cam.location = target + direction * 3
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{label}_{name}.png'); bpy.ops.render.render(write_still=True)
