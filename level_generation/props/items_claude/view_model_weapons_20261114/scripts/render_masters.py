"""Step 4, fallback (README.md "Crossbow"): tier masters rendered in Blender instead of painted by Codex, for a kind
whose Codex masters the image tool refuses every time (the crossbow: "violence" on every brief wording). The exact
upload (a single-piece kind) is rendered from prep.py's guide cameras with procedural materials per region and tier
(grained wood, steel or gilt, leather, cord; the legendary tier's cyan inlay as emissive bands), Cycles, transparent,
even studio light. Meshy then paints over them as over Codex masters.

Usage: blender --background --python render_masters.py -- <kind> <tier>
Writes work/<kind>/masters_t<tier>/<NN>_<view>.png (the names meshy_request.py reads).
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from kinds import KINDS  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
KIND, TIER = argv[0], int(argv[1])
WORK = os.path.join(PROJECT, 'work', KIND)
OUT = os.path.join(WORK, f'masters_t{TIER}')
os.makedirs(OUT, exist_ok=True)
NUMBER = {'front': '01', 'back': '02', 'left': '03', 'right': '04', 'top': '05', 'bottom': '06'}
REGIONS = {'blade': 0, 'metal': 1, 'wood': 2, 'leather': 3, 'gem': 4, 'glow': 5, 'string': 6, 'dark': 7, 'brass': 8,
           'edge': 9}

# Per tier and region: base colour (linear), metallic, roughness, grain colour (wood: the darker grain), and the
# legendary tier's emissive inlay.
TIERS = {
    1: {'metal': ((0.16, 0.155, 0.15), 1.0, 0.62), 'wood': ((0.30, 0.24, 0.17), 0.0, 0.8, (0.17, 0.13, 0.09)),
        'leather': ((0.22, 0.14, 0.08), 0.0, 0.85), 'string': ((0.42, 0.36, 0.25), 0.0, 0.9),
        'brass': ((0.16, 0.155, 0.15), 1.0, 0.62)},
    2: {'metal': ((0.55, 0.56, 0.58), 1.0, 0.3), 'wood': ((0.55, 0.25, 0.07), 0.0, 0.45, (0.30, 0.11, 0.03)),
        'leather': ((0.09, 0.05, 0.03), 0.0, 0.6), 'string': ((0.75, 0.70, 0.58), 0.0, 0.7),
        'brass': ((0.72, 0.52, 0.22), 1.0, 0.28)},
    3: {'metal': ((0.85, 0.62, 0.22), 1.0, 0.2), 'wood': ((0.025, 0.02, 0.018), 0.0, 0.25, (0.06, 0.045, 0.02)),
        'leather': ((0.32, 0.02, 0.03), 0.0, 0.45), 'string': ((0.85, 0.65, 0.25), 0.3, 0.4),
        'brass': ((0.9, 0.66, 0.25), 1.0, 0.18)},
    4: {'metal': ((0.09, 0.09, 0.12), 1.0, 0.3), 'wood': ((0.78, 0.74, 0.62), 0.0, 0.5, (0.6, 0.56, 0.45)),
        'leather': ((0.02, 0.035, 0.11), 0.0, 0.55), 'string': ((0.8, 0.82, 0.86), 0.5, 0.35),
        'brass': ((0.8, 0.82, 0.86), 1.0, 0.22), 'inlay': (0.1, 0.85, 1.0)},
}


def material(name, spec, kind):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    colour, metallic, roughness = spec[0], spec[1], spec[2]
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    coord = nt.nodes.new('ShaderNodeTexCoord')
    if kind == 'wood':
        # Grain along the stock (X): stretched noise into a wave, mixed between the wood and its grain colour.
        mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (0.08, 1.6, 1.6)
        noise = nt.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 3.0
        noise.inputs['Detail'].default_value = 8.0
        wave = nt.nodes.new('ShaderNodeTexWave')
        wave.bands_direction = 'Y'
        wave.inputs['Scale'].default_value = 1.4
        wave.inputs['Distortion'].default_value = 6.0
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (*spec[3], 1.0)
        ramp.color_ramp.elements[1].color = (*colour, 1.0)
        nt.links.new(coord.outputs['Object'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], wave.inputs['Vector'])
        nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        # Fine brushed or leather grain: a little noise in the colour.
        noise = nt.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 40.0 if kind != 'leather' else 18.0
        noise.inputs['Detail'].default_value = 6.0
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = tuple(c * 0.75 for c in colour) + (1.0,)
        ramp.color_ramp.elements[1].color = tuple(min(c * 1.15, 1.0) for c in colour) + (1.0,)
        nt.links.new(coord.outputs['Object'], noise.inputs['Vector'])
        nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    if 'inlay' in TIERS[TIER] and kind in ('metal', 'brass'):
        # Thin luminous bands across the metal (the legendary inlay).
        wave = nt.nodes.new('ShaderNodeTexWave')
        wave.inputs['Scale'].default_value = 0.6
        wave.wave_profile = 'SAW'
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.9
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].position = 0.95
        ramp.color_ramp.elements[1].color = (*TIERS[TIER]['inlay'], 1)
        nt.links.new(coord.outputs['Object'], wave.inputs['Vector'])
        nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 3.0
    return mat


bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'layout.blend'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
me = obj.data
assert len(KINDS[KIND]['pieces']) == 1, 'render_masters.py handles single-piece uploads'
co = np.array([v.co for v in me.vertices])
lo, hi = co.min(0), co.max(0)
# prep.py's upload of one piece: centred across X, standing on z = 0.
obj.location = Vector((-(lo[0] + hi[0]) / 2, 0.0, -lo[2]))
bpy.context.view_layer.update()
region = np.array([d.value for d in me.attributes['region'].data])
me.materials.clear()
slots = {}
for name, spec in TIERS[TIER].items():
    if name == 'inlay':
        continue
    slots[REGIONS[name]] = len(me.materials)
    me.materials.append(material(f'{name}_t{TIER}', spec, name))
fallback = slots[REGIONS['metal']]
for p in me.polygons:
    p.material_index = slots.get(int(region[p.index]), fallback)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
scene.world = bpy.data.worlds.new('w')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.55, 0.57, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
co = np.array([obj.matrix_world @ v.co for v in me.vertices])
ctr = Vector(((co.max(0) + co.min(0)) / 2).tolist())
ext = np.ptp(co, 0)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.clip_end = 1000
scene.camera = cam
light = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN'))
light.data.energy = 2.0
scene.collection.objects.link(light)
views = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'left': Vector((1, 0, 0)),
         'right': Vector((-1, 0, 0)), 'top': Vector((0, 0, 1)), 'bottom': Vector((0, 0, -1))}
for name in KINDS[KIND]['views']:
    d = views[name]
    across = [i for i in range(3) if abs(d[i]) < 0.5]
    w_ext, h_ext = (ext[0], ext[1]) if name in ('top', 'bottom') else (ext[across[0]], ext[2])
    portrait = h_ext >= w_ext
    scene.render.resolution_x, scene.render.resolution_y = (1024, 1536) if portrait else (1536, 1024)
    big, small = (h_ext, w_ext) if portrait else (w_ext, h_ext)
    cam.data.ortho_scale = max(big / 0.9, small * 1.5 / 0.9)
    cam.location = ctr + d * 300
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    # The key light from the viewer, a little above.
    light.rotation_euler = (-(d + Vector((0, 0, 0.6)))).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'{NUMBER[name]}_{name}.png')
    bpy.ops.render.render(write_still=True)
json.dump({'source': 'render_masters.py', 'tier': TIER}, open(os.path.join(OUT, 'rendered.json'), 'w'))
print('MASTERS rendered', KIND, TIER)
