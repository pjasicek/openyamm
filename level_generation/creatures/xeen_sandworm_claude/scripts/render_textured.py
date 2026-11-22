"""Textured EEVEE renders of the sand worm from the party's eye height (176 world units = 1.60 model m at the
Sand Worm binding's scale 110), about 3.0 m (330 units) from the axis, with the tier previews of
claude_shared/tier_textures.py (work/tier_worm_sandworm_<a|c>.png = what the engine's region ramps give) as base
colour. Writes review/textured_<name>.png and the list work/_textured.json (nothing saved to the blend)."""
import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import json as _json
IMPACT = _json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'anim_info.json')))['clips']['Attack']['impact_s']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
mesh = bpy.data.objects['Worm']; rig = bpy.data.objects['Worm_Rig']
mat = bpy.data.materials.new('Worm_A'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(path, cs):
    img = bpy.data.images.load(path, check_existing=False); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


base = tex(os.path.join(HERE, 'work', 'tier_worm_sandworm_a.png'), 'sRGB')
nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex(os.path.join(T, 'worm_normal_1k.png'), 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
sep = nt.nodes.new('ShaderNodeSeparateColor'); com = nt.nodes.new('ShaderNodeCombineColor')
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
nt.links.new(nm.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Green'], inv.inputs[1])
nt.links.new(sep.outputs['Red'], com.inputs['Red']); nt.links.new(inv.outputs[0], com.inputs['Green'])
nt.links.new(sep.outputs['Blue'], com.inputs['Blue'])
nt.links.new(com.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex(os.path.join(T, 'worm_mr_1k.png'), 'Non-Color'); s2 = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], s2.inputs['Color']); nt.links.new(s2.outputs['Green'], bsdf.inputs['Roughness'])
bsdf.inputs['Metallic'].default_value = 0.0
try:
    bsdf.inputs['Specular IOR Level'].default_value = 0.0      # the binding sets openyamm_specular 0
except KeyError:
    pass
mesh.data.materials.clear(); mesh.data.materials.append(mat)

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
C.floor_grid()
EYE = 1.60; DIST = 3.0
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 50
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
shots = []


def shot(name, action, t, azim_deg, dist=DIST, eye=EYE, target=(0, -0.1, 0.5), lens=50, tier='a'):
    base.image = bpy.data.images.load(os.path.join(HERE, 'work', f'tier_worm_sandworm_{tier}.png'), check_existing=True)
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
            o.hide_render = o.name not in ('Worm', 'Floor')
    bpy.ops.render.render(write_still=True)
    shots.append((name, sc.render.filepath))


shot('front', 'Standing', 0.0, 0)
shot('quarter', 'Standing', 0.6, 35)
shot('side', 'Standing', 1.2, 90)
shot('windup', 'Attack', 0.38, 15)
shot('blow', 'Attack', IMPACT, 15)
shot('walk', 'Walking', 0.3, 35)
shot('run', 'Running', 0.2, 60)
shot('hit', 'Hit', 0.1, 15)
shot('dead', 'Dead', 0.5, 30, target=(0.1, -0.2, 0.2))
shot('maw_close', 'Standing', 1.2, 10, dist=1.3, eye=1.55, target=(0, -0.15, 0.95), lens=60)
shot('back', 'Standing', 0.0, 180)
shot('c_front', 'Standing', 0.0, 0, tier='c')
shot('c_blow', 'Attack', IMPACT, 15, tier='c')
shot('c_walk', 'Walking', 0.3, 35, tier='c')
shot('c_dead', 'Dead', 0.5, 30, target=(0.1, -0.2, 0.2), tier='c')
import json
json.dump(shots, open(os.path.join(HERE, 'work', '_textured.json'), 'w'))
print('RENDERED', len(shots))
