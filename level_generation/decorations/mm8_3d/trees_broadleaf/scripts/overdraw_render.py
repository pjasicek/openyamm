"""Leaf-card layer count renders (Blender, Cycles) for overdraw.py.
Args (after '--'): <id> <blend> <out dir> <frame height m>. For every LOD object (Tree, Tree_LOD1, Tree_LOD2,
Tree_LOD3) and view (eye = front, three_quarter, side; the review cameras), renders one sample per pixel, no pixel
filter: every alpha-tested card material (Leaves, LeavesFar, Moss, Impostor) becomes transparent plus an emission of
1 where its texel passes the 0.5 cutoff, so a camera ray passes through every card and sums one per surviving
fragment (no depth test between cards); opaque materials (Bark, Shell) stop the ray with zero emission, as the
engine's opaque depth prepass rejects the card fragments behind them. Writes <out>/<lod>_<view>.npy: float32 H x W x 2
(layer count, covered = film alpha or any layer)."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
sid, blend, out, frame = args[0], args[1], args[2], float(args[3])
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 1; sc.cycles.use_denoising = False; sc.cycles.seed = 0
sc.cycles.transparent_max_bounces = 256; sc.cycles.max_bounces = 0
sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 0.01
sc.render.film_transparent = True; sc.view_settings.view_transform = 'Raw'
sc.render.resolution_y = 405; sc.render.resolution_x = 360; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
sc.render.image_settings.color_mode = 'RGBA'
sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs['Strength'].default_value = 0.0
CARDS = ('Leaves', 'LeavesFar', 'Moss', 'Impostor')
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    outn = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if bsdf is None or outn is None:
        continue
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1, 1, 1, 1)
    if m.name in CARDS:
        alpha = bsdf.inputs['Alpha'].links[0].from_socket if bsdf.inputs['Alpha'].links else None
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        if alpha is not None:
            nt.links.new(alpha, clip.inputs[0])
        else:
            clip.inputs[0].default_value = 1.0
        nt.links.new(clip.outputs[0], em.inputs['Strength'])
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
        nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], outn.inputs['Surface'])
    else:
        em.inputs['Strength'].default_value = 0.0          # opaque: stops the ray, adds nothing
        nt.links.new(em.outputs[0], outn.inputs['Surface'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
CAMS = {'eye': (0.0, 1.6), 'three_quarter': (45.0, 5.5), 'side': (90.0, 1.6)}
lods = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Tree')]
scale = frame / 6.69
for o in lods:
    for x in lods:
        x.hide_render = x is not o
    for view, (yaw, height) in CAMS.items():
        d = 10.5 * scale
        cam.location = (math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, height * scale)
        cam.rotation_euler = (Vector((0, 0, frame * 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        if o.name == 'Tree_LOD3':                       # the engine turns the impostor quad toward the camera
            o.rotation_euler = (0.0, 0.0, math.radians(yaw))
        path = os.path.join(out, f'{o.name}_{view}.exr')
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path)
        px = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)[::-1]
        bpy.data.images.remove(img); os.remove(path)
        layers = px[..., 0]
        covered = ((px[..., 3] > 0.5) | (layers > 0.5)).astype(np.float32)
        np.save(os.path.join(out, f'{o.name}_{view}.npy'), np.stack([layers, covered], 2))
        print('OVERDRAW', o.name, view, round(float(layers[covered > 0].mean()), 2) if covered.any() else 0)
