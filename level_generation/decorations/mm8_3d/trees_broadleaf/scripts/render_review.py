"""Eevee review renders of a tree blend (sun + sky, alpha-clipped leaves, Standard view). Materials get the
engine's vertex-colour rule (base colour x COLOR_0 'Color'); mode 'occlusion' renders the vertex colour alone, 'plain' leaves it out.
Args: <id> out_prefix blend views [mode] [resolution_height] [noshadow]. Views: eye, three_quarter, back (eye level from behind)."""
import bpy, sys, os, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 2:]       # after the species id
prefix, blend, views = args[0], args[1], args[2].split(',')
mode = args[3] if len(args) > 3 else 'lit'
res = int(args[4]) if len(args) > 4 else 540
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = True
sc.render.resolution_y = res; sc.render.resolution_x = int(res * 480 / 540)
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
if len(args) > 5 and args[5] == 'noshadow':     # like the engine: no shadow maps, no screen-space occlusion or GI
    sun.data.use_shadow = False
    sc.eevee.use_shadows = False; sc.eevee.use_fast_gi = False; sc.eevee.use_raytracing = False
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is not None and not bsdf.inputs['Base Color'].links and m.name == 'Shell':
        # untextured inner crown shell: a white stand-in texel, so it gets COLOR_0 like the other parts
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (1, 1, 1, 1)
        nt.links.new(rgb.outputs[0], bsdf.inputs['Base Color'])
    if bsdf is None or not bsdf.inputs['Base Color'].links:
        continue
    tex = bsdf.inputs['Base Color'].links[0].from_node
    bsdf.inputs['Specular IOR Level'].default_value = 0.15     # the engine's leaves barely reflect
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    if mode == 'occlusion':
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(attr.outputs['Color'], em.inputs['Color'])
        surface = em.outputs[0]
        if bsdf.inputs['Alpha'].links:
            clip = bsdf.inputs['Alpha'].links[0].from_node
            tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
            nt.links.new(clip.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(em.outputs[0], mx.inputs[2]); surface = mx.outputs[0]
        nt.links.new(surface, out.inputs['Surface'])
    elif mode == 'lit':
        mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
        nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
        nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
lods = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Tree')]
Hh = max((o.matrix_world @ Vector(c)).z for o in lods for c in o.bound_box)
if len(args) > 6:                                  # explicit framing height (gate.py: frame as the exported blend)
    Hh = float(args[6])
target = Vector((0, 0, Hh * 0.5))
CAMS = {'eye': (0.0, 1.6), 'three_quarter': (45.0, 5.5), 'back': (180.0, 1.6), 'side': (90.0, 1.6),
        'under': (0.0, 1.5), 'close': (30.0, 3.5),        # close: three-quarter-ish at half the distance
        'upward': (0.0, 2.0), 'low34': (45.0, 1.2)}        # under-crown gate views (2026-10-16, metres, not scaled)                       # under: close below the crown, looking up into it
for m in bpy.data.materials:                   # the engine culls back faces of single-sided (opaque) materials
    if m.name in ('Bark', 'Shell', 'Fruit'):
        m.use_backface_culling = True
for o in lods:
    for x in lods:
        x.hide_render = x is not o
    if o.name != 'Tree' and ('close' in views or 'upward' in views):
        continue                                  # close-ups and under-crown views: LOD0 only
    for view in views:
        yaw, height = CAMS[view]
        if view == 'upward':                      # 2 m up, 1.5 m from the trunk, pitched 60 degrees up, wide lens
            cam.data.lens = 24
            cam.location = (0.0, -1.5, 2.0)
            cam.rotation_euler = (math.radians(90 + 60), 0.0, 0.0)
            sc.render.filepath = f'{prefix}_{o.name}_{view}.png'
            bpy.ops.render.render(write_still=True)
            continue
        if view == 'low34':                       # low three-quarter: 1.2 m up at 0.55 of the review distance
            cam.data.lens = 35
            d = 0.55 * 10.5 * Hh / 6.69
            cam.location = (math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, height)
            cam.rotation_euler = (Vector((0, 0, Hh * 0.55)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f'{prefix}_{o.name}_{view}.png'
            bpy.ops.render.render(write_still=True)
            continue
        cam.data.lens = 50
        scale = Hh / 6.69                         # framing as for the 6.69 m 6tree01, whatever the species' size
        d = (2.6 if view == 'under' else 5.2 if view == 'close' else 10.5) * scale; height *= scale
        cam.location = (math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, height)
        aim = Vector((0, 0, Hh * 0.62)) if view in ('under', 'close') else target
        cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{prefix}_{o.name}_{view}.png'
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
