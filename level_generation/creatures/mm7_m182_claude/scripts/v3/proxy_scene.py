"""Proxy-painted v3 model for the render-guided HD masters (Blender). work/v3/uv_master.blend + work/v3/proxy maps:
cdr1 body faces show the recoloured cdr1 paint (UV_cdr1), the head the v2 MM7 head look (UV_v2head), the wing bones
the recoloured cdr1 wing paint, the membranes a procedural light grey-green fine-cell pattern (native membrane
colour, 3 cm cells with darker borders), the lofted neck procedural scales with gold throat plates on its
ventral side, the spine row yellow. Membrane faces: scripts/v3/wing_classes.py (wing faces farther than 5.5 cm from the
wing bone chain; v3a used a 2.2 cm thin-shell ray test, which left the inner panels as arm). Renders the five views of work/v3/spec_clay.json (EEVEE, soft even light, transparent).
Usage: blender -b -P proxy_scene.py -- <out dir> [proxy blend name]"""
import bpy, sys, math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[2]; out = Path(sys.argv[sys.argv.index('--') + 1]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
o = bpy.data.objects['Body']; me = o.data; rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
part = np.array([d.value for d in me.attributes['v3part'].data])
sys.path.insert(0, str(P / 'scripts/v3')); import wing_classes
wing_classes.classify(o, rig)
membrane = np.array([d.value > .5 for d in me.attributes['membrane'].data])
# ventral attribute for the loft (throat plates)
D = Vector((0, -0.25, -0.97)).normalized()
ven = me.attributes.new('ventral', 'FLOAT', 'POINT')
for v in me.vertices: ven.data[v.index].value = v.normal.dot(D)
def img_mat(name, image, uvmap, rough=.8):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(image)); u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = uvmap
    nt.links.new(u.outputs[0], t.inputs[0]); nt.links.new(t.outputs[0], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = rough
    return m
def cell_mat(name, c_light, c_dark, scale, edge=.06, extra=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = edge
    nt.links.new(vo.outputs['Distance'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = c_dark; mx.inputs['B'].default_value = c_light
    nt.links.new(mr.outputs['Result'], mx.inputs['Factor']); col = mx.outputs['Result']
    if extra: col = extra(nt, col, tc)
    nt.links.new(col, bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = .85
    return m
srgb = lambda r, g, b: (((r / 255 + .055) / 1.055) ** 2.4, ((g / 255 + .055) / 1.055) ** 2.4, ((b / 255 + .055) / 1.055) ** 2.4, 1)
def veins(nt, col, tc):
    # faint darker veins: a stretched wave pattern, and sparse warm flecks
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 3.0; wv.inputs['Distortion'].default_value = 6
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .0; mr.inputs['From Max'].default_value = .12
    nt.links.new(wv.outputs['Fac'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = srgb(82, 92, 68); nt.links.new(col, mx.inputs['B'])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; nt.links.new(mr.outputs['Result'], inv.inputs[1])
    sc = nt.nodes.new('ShaderNodeMath'); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = .18; nt.links.new(inv.outputs[0], sc.inputs[0])
    nt.links.new(sc.outputs[0], mx.inputs['Factor'])
    return mx.outputs['Result']
def throat(nt, col, tc):
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'ventral'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .45; mr.inputs['From Max'].default_value = .6
    nt.links.new(at.outputs['Fac'], mr.inputs['Value'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 9
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    seam = nt.nodes.new('ShaderNodeMapRange'); seam.inputs['From Min'].default_value = .0; seam.inputs['From Max'].default_value = .25
    nt.links.new(wv.outputs['Fac'], seam.inputs['Value'])
    g = nt.nodes.new('ShaderNodeMix'); g.data_type = 'RGBA'; g.inputs['A'].default_value = srgb(120, 92, 25); g.inputs['B'].default_value = srgb(214, 178, 62)
    nt.links.new(seam.outputs['Result'], g.inputs['Factor'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(col, mx.inputs['A']); nt.links.new(g.outputs['Result'], mx.inputs['B'])
    nt.links.new(mr.outputs['Result'], mx.inputs['Factor'])
    return mx.outputs['Result']
PX = P / 'work/v3/proxy'
mats = [img_mat('PBody', PX / 'body_proxy.png', 'UV_cdr1'), img_mat('PHead', PX / 'head_proxy.png', 'UV_v2head'),
        img_mat('PWingBone', PX / 'wings_proxy.png', 'UV_cdr1'),
        cell_mat('PMembrane', srgb(160, 172, 136), srgb(88, 100, 74), 30, .2),
        cell_mat('PLoft', srgb(52, 78, 44), srgb(18, 30, 16), 55, .05, throat),
        cell_mat('PSpine', srgb(222, 204, 92), srgb(150, 140, 40), 30, .15)]
orig_slot = [p.material_index for p in me.polygons]       # materials.clear() resets the face indices
me.materials.clear()
for m in mats: me.materials.append(m)
for p in me.polygons:
    p.material_index = orig_slot[p.index]
    pv = part[list(p.vertices)]
    if (pv == 3).all(): p.material_index = 5
    elif (pv == 2).any() and p.material_index == 0: p.material_index = 4
    elif p.material_index == 2: p.material_index = 3 if membrane[p.index] else 2
    elif p.material_index == 1: p.material_index = 1
    else: p.material_index = 0
print('PROXY membrane faces', int(membrane.sum()), 'of', sum(1 for p in me.polygons if p.material_index in (2, 3)), 'wing faces')
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('Key', bpy.data.lights.new('Key', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 1.2; sun.rotation_euler = (0.6, 0.15, -0.5)
sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
import json
spec = json.loads((P / 'work/v3/spec_clay.json').read_text())
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 100
sc.render.resolution_x, sc.render.resolution_y = spec['res']; sc.render.resolution_percentage = 100
for s in spec['shots']:
    t = Vector(s['target']); cam.location = t + Vector(s['dir']).normalized() * 20
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = s['scale']
    sc.render.filepath = str(out / (s['name'].replace('clay_', '') + '.png')); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/v3' / (sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else 'proxy.blend')))
print('PROXY rendered', len(spec['shots']))
