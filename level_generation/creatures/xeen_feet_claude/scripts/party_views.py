"""Textured renders from the party's eye (180 world units up, about 600 units away; model metres at scale 267):
front, three-quarter, side, the blow (Attack at the impact frame), Hit, the corpse -> review/party_<name>.png"""
import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim.blend'))
rig = bpy.data.objects['Feet_Rig']; ob = bpy.data.objects['Feet']; sc = bpy.context.scene
mat = bpy.data.materials.new('m'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(HERE, 'textures', 'feet_basecolor_graded.png'))
nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(mat)
SCALE = 267.0
eye = 180 / SCALE; dist = 600 / SCALE
shots = [('front', 'Standing', 0, 0), ('quarter', 'Standing', 10, 40), ('side', 'Walking', 20, 90),
         ('blow', 'Attack', 14, 0), ('blow_quarter', 'Attack', 14, 40), ('hit', 'Hit', 4, 20), ('dead', 'Dead', 0, 25),
         ('back', 'Standing', 30, 180)]
for name, clip, frame, ang in shots:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(frame)
    a = math.radians(ang)
    loc = (dist * math.sin(a), -dist * math.cos(a), eye)
    C.setup(textured=True)
    sc.display.shading.light = 'STUDIO'
    sc.render.resolution_x, sc.render.resolution_y = 900, 600
    cd = bpy.data.cameras.new('c'); cd.lens = 50
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam)
    cam.matrix_world = C.look(loc, (0, 0, 0.16)); sc.camera = cam
    C.floor_grid()
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o.name not in ('Feet', 'Floor')
    sc.render.filepath = os.path.join(HERE, 'review', f'party_{name}.png')
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
print('PARTY views', len(shots))
