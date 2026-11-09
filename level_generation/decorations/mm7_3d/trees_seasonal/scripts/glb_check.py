"""LOD0 of finished GLBs side by side (quality pass): each GLB is imported and rendered from the review eye camera and
the three-quarter camera (render_review.py's framing and lighting, no shadows as the engine), base colour x COLOR_0,
leaf cards alpha-clipped. Prints mean colour and coverage per file; writes <out>_<k>_<view>.png and <out>.json.
Usage: blender -b -P glb_check.py -- <out prefix> a.glb [b.glb ...]"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
prefix, paths = args[0], args[1:]
CPU = os.environ.get('TREES_REVIEW_CPU') == '1'
stats = []
for k, path in enumerate(paths):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    ob = next(o for o in bpy.data.objects if o.type == 'MESH')
    sc = bpy.context.scene
    if CPU:
        sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.cycles.max_bounces = 0
        sc.cycles.transparent_max_bounces = 64
    else:
        sc.render.engine = 'BLENDER_EEVEE'
        sc.eevee.use_shadows = False
    sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
    sc.render.resolution_y = 540; sc.render.resolution_x = 480
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86); sun.data.use_shadow = False
    sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
    colour = ob.data.color_attributes[0].name if ob.data.color_attributes else None
    for m in ob.data.materials:
        nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None:
            continue
        bsdf.inputs['Specular IOR Level'].default_value = 0.15
        has_vc = any(n.type in ('VERTEX_COLOR', 'ATTRIBUTE') for n in nt.nodes)
        if colour and not has_vc and bsdf.inputs['Base Color'].links:
            tex = bsdf.inputs['Base Color'].links[0].from_node
            attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = colour
            mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
            nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
            nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
        if m.blend_method != 'OPAQUE' or bsdf.inputs['Alpha'].is_linked:
            m.surface_render_method = 'DITHERED'
    zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
    H = max(zs)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    row = {'path': path}
    for view, (yaw, height) in {'eye': (0.0, 1.6), 'three_quarter': (45.0, 5.5)}.items():
        s = H / 6.69; d = 10.5 * s
        cam.location = (math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, height * s)
        cam.rotation_euler = (Vector((0, 0, H * 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        out = f'{prefix}_{k}_{view}.png'; sc.render.filepath = out; bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(out); px = np.array(img.pixels[:]).reshape(-1, 4)
        m = px[:, 3] > 0.5
        row[view] = {'mean_srgb': (px[m, :3].mean(0) * 255).round(1).tolist(), 'opaque_px': int(m.sum())}
    stats.append(row)
    print('CHECK', k, os.path.basename(path), row['eye'], row['three_quarter'])
json.dump(stats, open(prefix + '.json', 'w'), indent=1)
