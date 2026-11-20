"""Blender: frond-card overdraw of one palm. Every Leaves fragment that passes the alpha cutoff (texel alpha > 0.5) is
a Cycles transparent layer that multiplies the light by 0.8; everything else (bark, texels under the cutoff) is fully
transparent, so with one ray per pixel through 512 transparent bounces and a white background the pixel value is
0.8^n: n = alpha-tested leaf layers along that ray, with no depth test (every layer counts, as in the GPU's
fragment work before early-z rejects any). Orthographic views framed on LOD0 as render_review.py does: front,
three-quarter and side. Writes work/<id>/layers_<object>_<view>.npy (layer count per pixel, float32) and
work/<id>/layers.json (mean and 95th percentile over covered pixels, coverage). Usage: -- <id> [blend] [res]"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc
args = sys.argv[sys.argv.index('--') + 1:]
SID = args[0]
W = pc.work(SID)
blend = args[1] if len(args) > 1 else os.path.join(W, 'export.blend')
RES = int(args[2]) if len(args) > 2 else 400
ATTEN = 0.8
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 1; sc.cycles.use_denoising = False; sc.cycles.use_adaptive_sampling = False
sc.cycles.transparent_max_bounces = 512; sc.cycles.max_bounces = 512
sc.cycles.diffuse_bounces = sc.cycles.glossy_bounces = sc.cycles.transmission_bounces = sc.cycles.volume_bounces = 0
sc.cycles.filter_width = 0.01; sc.cycles.seed = 0
sc.cycles.min_transparent_bounces = 512; sc.cycles.min_light_bounces = 512     # no Russian roulette: it would end deep rays (black)
sc.render.film_transparent = False
sc.render.resolution_x = sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
sc.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('White'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (1, 1, 1, 1); bg.inputs['Strength'].default_value = 1.0
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    clear = nt.nodes.new('ShaderNodeBsdfTransparent'); clear.inputs['Color'].default_value = (1, 1, 1, 1)
    if m.name.startswith('Leaves') and bsdf is not None and bsdf.inputs['Base Color'].links:
        tex = bsdf.inputs['Base Color'].links[0].from_node
        layer = nt.nodes.new('ShaderNodeBsdfTransparent'); layer.inputs['Color'].default_value = (ATTEN, ATTEN, ATTEN, 1)
        cut = nt.nodes.new('ShaderNodeMath'); cut.operation = 'GREATER_THAN'; cut.inputs[1].default_value = 0.5
        nt.links.new(tex.outputs['Alpha'], cut.inputs[0])
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(cut.outputs[0], mix.inputs['Fac'])
        nt.links.new(clear.outputs[0], mix.inputs[1]); nt.links.new(layer.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
    else:
        nt.links.new(clear.outputs[0], out.inputs['Surface'])
cam = bpy.data.objects.new('LayerCam', bpy.data.cameras.new('LayerCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
lods = [bpy.data.objects[n] for n in ('Plant', 'Plant_LOD1', 'Plant_LOD2') if n in bpy.data.objects]
base = lods[0]
pts = [base.matrix_world @ Vector(c) for c in base.bound_box]
Hm = max(p.z for p in pts); Wm = max(max(abs(p.x), abs(p.y)) for p in pts)
cam.data.ortho_scale = max(2.15 * Wm, 1.12 * Hm)
VIEWS = {'front': (0.0, 6.0), 'three_quarter': (40.0, 25.0), 'side': (90.0, 6.0)}
stats = {}
for o in lods:
    for x in bpy.data.objects:
        if x.type == 'MESH':
            x.hide_render = x is not o
    for view, (yaw, pitch) in VIEWS.items():
        d = 40.0
        cam.location = (math.sin(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                        -math.cos(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                        Hm * 0.5 + d * math.sin(math.radians(pitch)))
        cam.rotation_euler = (Vector((0, 0, Hm * 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        path = os.path.join(W, f'layers_{o.name}_{view}.exr')
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path)
        px = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)[::-1, :, 0]
        bpy.data.images.remove(img)
        n = np.log(np.clip(px, 1e-12, 1.0)) / math.log(ATTEN)
        n = np.where(px > 0.97, 0.0, n)                     # no passing layer (a little float noise allowed)
        np.save(os.path.join(W, f'layers_{o.name}_{view}.npy'), n.astype(np.float32))
        cov = n >= 0.5
        stats[f'{o.name}/{view}'] = {'mean': round(float(n[cov].mean()), 2) if cov.any() else 0.0,
                                     'p95': round(float(np.percentile(n[cov], 95)), 2) if cov.any() else 0.0,
                                     'max': round(float(n.max()), 1), 'covered_px': int(cov.sum())}
        os.remove(path)
        print('LAYERS', SID, o.name, view, stats[f'{o.name}/{view}'])
json.dump(stats, open(os.path.join(W, 'layers.json'), 'w'), indent=1)
