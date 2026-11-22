"""Textured renders of the Guardian (EEVEE, the graded shared skin, emission from the colour mask) from the party's
eye height (176 world units = 1.41 model m at the binding's scale 125), about 375 units away, plus close-ups.
Writes review/textured_<name>.png (nothing saved to the blend); scripts/join.py makes the sheet."""
import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
mesh = bpy.data.objects['Skull']; rig = bpy.data.objects['Guardian_Rig']
mat = bpy.data.materials.new('Guardian_A'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name), check_existing=False); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


nt.links.new(tex('guardian_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('guardian_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nmap.inputs['Strength'].default_value = 1.0
# Meshy normal is +y down: flip green for Blender's +y up
sep = nt.nodes.new('ShaderNodeSeparateColor'); com = nt.nodes.new('ShaderNodeCombineColor')
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
nt.links.new(nm.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Green'], inv.inputs[1])
nt.links.new(sep.outputs['Red'], com.inputs['Red']); nt.links.new(inv.outputs[0], com.inputs['Green'])
nt.links.new(sep.outputs['Blue'], com.inputs['Blue'])
nt.links.new(com.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('guardian_mr_1k.png', 'Non-Color'); s2 = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], s2.inputs['Color']); nt.links.new(s2.outputs['Green'], bsdf.inputs['Roughness'])
bsdf.inputs['Metallic'].default_value = 0.0
em = tex('guardian_emission_rgb.png', 'sRGB')
nt.links.new(em.outputs['Color'], bsdf.inputs['Emission Color']); bsdf.inputs['Emission Strength'].default_value = 1.5
mesh.data.materials.clear(); mesh.data.materials.append(mat)

sc = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 520, 520
sc.render.film_transparent = False
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.12, 0.12, 0.14, 1); bg.inputs['Strength'].default_value = 0.6
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(-30))
C.floor_grid()
EYE = 1.41; DIST = 3.0
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 50
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam


def shot(name, action, t, azim_deg, dist=DIST, eye=EYE, target_z=0.48, lens=50):
    act = bpy.data.actions[action]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(round(t * 30)) + 1)
    a = math.radians(azim_deg)
    loc = Vector((dist * math.sin(a), -dist * math.cos(a), eye))
    cam.matrix_world = C.look(loc, (0, 0, target_z)); cam_d.lens = lens
    sc.render.filepath = os.path.join(HERE, 'review', f'textured_{name}.png')
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath


shots = [shot('front', 'Standing', 0.0, 0), shot('quarter', 'Standing', 0.5, 35), shot('side', 'Standing', 1.0, 90),
         shot('blow', 'Attack', 0.45, 15), shot('ranged', 'AttackRanged', 0.5, 15), shot('dead', 'Dead', 0.5, 30),
         shot('face_close', 'Standing', 0.0, 10, dist=1.6, eye=0.7, target_z=0.45, lens=60),
         shot('back', 'Standing', 0.0, 180)]
print('RENDERED', len(shots))
