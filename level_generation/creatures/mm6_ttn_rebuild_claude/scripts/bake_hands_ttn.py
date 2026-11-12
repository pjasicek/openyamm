"""Bake the grafted Titan hands into their atlas rectangles (after mm9_yrsa_claude/v2/scripts/bake_hands.py).

Rest pose, Cycles CPU, at the atlas size (2080 x 1024) in the body's UVMap (the rectangles graft_ttn.py packed), into
work/hands/: hand_skin.png (MakeHuman CC0 skin through MHUV, emission), hand_mask.png (coverage), hand_ao.png (AO with
the body as occluder). Args: -- <blend> <MakeHuman skin, e.g. middleage_caucasian_male/middleage_lightskinned_male_diffuse.png>"""
import bpy, bmesh, os, sys
a = sys.argv[sys.argv.index('--') + 1:]
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIN = os.path.expanduser('~/.config/blender/5.2/extensions/.user/blender_org/mpfb/data/skins/' + a[1])
OUT = os.path.join(PROJ, 'work', 'hands'); os.makedirs(OUT, exist_ok=True)
W, H = 2080, 1024
bpy.ops.wm.open_mainfile(filepath=os.path.join(PROJ, a[0]))
sc = bpy.context.scene
body = bpy.data.objects['Titan']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
hands = body.copy(); hands.data = body.data.copy(); sc.collection.objects.link(hands); hands.name = 'Hands'
for o, keep in ((hands, 1), (body, 0)):
    bm = bmesh.new(); bm.from_mesh(o.data); hl = bm.faces.layers.int['hand']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[hl] != keep], context='FACES')
    bm.to_mesh(o.data); bm.free()
try:
    sc.render.engine = 'CYCLES'
except TypeError:
    pass
sc.cycles.device = 'CPU'; sc.cycles.samples = 64
skin = bpy.data.images.load(SKIN)


def target(name):
    img = bpy.data.images.new(name, W, H, alpha=False, float_buffer=False)
    img.generated_color = (0, 0, 0, 1)
    return img


def setup(kind, img):
    mat = bpy.data.materials.new('bake_' + kind); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    outn = nt.nodes.new('ShaderNodeOutputMaterial')
    if kind == 'skin':
        uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'MHUV'
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = skin
        em = nt.nodes.new('ShaderNodeEmission')
        nt.links.new(uv.outputs['UV'], tx.inputs['Vector']); nt.links.new(tx.outputs['Color'], em.inputs['Color'])
        nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])
    elif kind == 'mask':
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1, 1, 1, 1)
        nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])
    else:
        bs = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(bs.outputs['BSDF'], outn.inputs['Surface'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.nodes.active = t
    hands.data.materials.clear(); hands.data.materials.append(mat)
    for p in hands.data.polygons:
        p.material_index = 0
    hands.data.uv_layers.active = hands.data.uv_layers['UVMap']
    hands.data.uv_layers['UVMap'].active_render = True


for o in bpy.data.objects:
    o.select_set(o == hands)
bpy.context.view_layer.objects.active = hands
for kind, btype, fname in (('skin', 'EMIT', 'hand_skin.png'), ('mask', 'EMIT', 'hand_mask.png'),
                           ('ao', 'AO', 'hand_ao.png')):
    img = target('hand_' + kind)
    setup(kind, img)
    bpy.ops.object.bake(type=btype, margin=0, use_clear=True, use_selected_to_active=False)
    img.filepath_raw = os.path.join(OUT, fname); img.file_format = 'PNG'; img.save()
    print('BAKED', fname)
