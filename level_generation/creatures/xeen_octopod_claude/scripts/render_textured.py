"""Textured EEVEE renders of the octopod over a dark lake plane at z 0 (the waterline), from about the party's eye
above the water (1.6 model m = 216 units at the Octopod binding's scale 135: a party on a bank or jetty about 40 units
over the water), about 3.2 m (430 units) from the axis, with the viewer's tier bakes (work/tier_octopod_<a|b|c>_
Octopod_A.png = what the engine's region ramps give) as base colour and the foam ring as an alpha cut-out.
Writes review/textured_<name>.png and the list work/_textured.json (nothing saved to the blend)."""
import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import json as _json
IMPACT = _json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'anim_info.json')))['clips']['Attack']['impact_s']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
mesh = bpy.data.objects['Octopod']; rig = bpy.data.objects['Octopod_Rig']
mat = bpy.data.materials.new('Octopod_A'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(path, cs):
    img = bpy.data.images.load(path, check_existing=False); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


base = tex(os.path.join(HERE, 'work', 'tier_octopod_a_Octopod_A.png'), 'sRGB')
nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex(os.path.join(T, 'octopod_normal_1k.png'), 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
sep = nt.nodes.new('ShaderNodeSeparateColor'); com = nt.nodes.new('ShaderNodeCombineColor')
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
nt.links.new(nm.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Green'], inv.inputs[1])
nt.links.new(sep.outputs['Red'], com.inputs['Red']); nt.links.new(inv.outputs[0], com.inputs['Green'])
nt.links.new(sep.outputs['Blue'], com.inputs['Blue'])
nt.links.new(com.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex(os.path.join(T, 'octopod_mr_1k.png'), 'Non-Color'); s2 = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], s2.inputs['Color']); nt.links.new(s2.outputs['Green'], bsdf.inputs['Roughness'])
bsdf.inputs['Metallic'].default_value = 0.0
try:
    bsdf.inputs['Specular IOR Level'].default_value = 0.0      # the binding sets openyamm_specular 0
except KeyError:
    pass
foam = bpy.data.materials.new('FoamR'); foam.use_nodes = True; fnt = foam.node_tree
fb = next(n for n in fnt.nodes if n.type == 'BSDF_PRINCIPLED')
ft = fnt.nodes.new('ShaderNodeTexImage'); ft.image = bpy.data.images.load(os.path.join(T, 'foam.png'))
fnt.links.new(ft.outputs['Color'], fb.inputs['Base Color']); rnd = fnt.nodes.new('ShaderNodeMath'); rnd.operation = 'ROUND'
fnt.links.new(ft.outputs['Alpha'], rnd.inputs[0]); fnt.links.new(rnd.outputs[0], fb.inputs['Alpha'])
try:
    foam.surface_render_method = 'DITHERED'
except AttributeError:
    foam.blend_method = 'CLIP'
mesh.data.materials[0] = mat; mesh.data.materials[1] = foam
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.002)); wp = bpy.context.active_object; wp.name = 'Water'
wm = bpy.data.materials.new('water'); wm.use_nodes = True
wbs = next(n for n in wm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
wbs.inputs['Base Color'].default_value = (0.015, 0.05, 0.06, 1); wbs.inputs['Roughness'].default_value = 0.25
wp.data.materials.append(wm)

sc = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 520, 420
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.12, 0.12, 0.14, 1); bg.inputs['Strength'].default_value = 0.7
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-30))
EYE = 1.60; DIST = 3.2
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 50
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
shots = []


def shot(name, action, t, azim_deg, dist=DIST, eye=EYE, target=(0, -0.1, 0.2), lens=40, tier='a'):
    base.image = bpy.data.images.load(os.path.join(HERE, 'work', f'tier_octopod_{tier}_Octopod_A.png'), check_existing=True)
    act = bpy.data.actions[action]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(round(t * 30)))
    if action == 'Dead':
        cam_d.lens = lens
    a = math.radians(azim_deg)
    loc = Vector((dist * math.sin(a), -dist * math.cos(a), eye))
    cam.matrix_world = C.look(loc, target); cam_d.lens = lens
    sc.render.filepath = os.path.join(HERE, 'review', f'textured_{name}.png')
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o.name not in ('Octopod', 'Water')
    bpy.ops.render.render(write_still=True)
    shots.append((name, sc.render.filepath))


shot('front', 'Standing', 0.0, 0)
shot('quarter', 'Standing', 0.8, 35)
shot('side', 'Standing', 1.6, 90)
shot('windup', 'Attack', 0.42, 15)
shot('blow', 'Attack', IMPACT, 15)
shot('walk', 'Walking', 0.3, 35)
shot('run', 'Running', 0.2, 60)
shot('hit', 'Hit', 0.1, 15)
shot('death', 'Death', 0.7, 30)
shot('dead', 'Dead', 0.5, 30)
shot('face_close', 'Standing', 1.2, 8, dist=1.6, eye=0.9, target=(0, -0.2, 0.25), lens=55)
shot('back', 'Standing', 0.0, 180)
shot('fidget', 'Fidget', 1.0, 20)
shot('b_front', 'Standing', 0.0, 0, tier='b')
shot('b_blow', 'Attack', IMPACT, 15, tier='b')
shot('c_front', 'Standing', 0.0, 0, tier='c')
shot('c_quarter', 'Standing', 0.8, 35, tier='c')
shot('c_walk', 'Walking', 0.3, 35, tier='c')
import json
json.dump(shots, open(os.path.join(HERE, 'work', '_textured.json'), 'w'))
print('RENDERED', len(shots))
