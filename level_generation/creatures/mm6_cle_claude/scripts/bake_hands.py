"""Bake the new hands' maps into their squares of the head texture set (work/rig_v4.blend, rest pose, Cycles CPU):
  work/hands/hand_skin.png  the MakeHuman (CC0) young caucasian male skin through the hands' own MakeHuman UVs (MHUV)
                            into HandUV (emission bake): nails, knuckle creases and palm lines
  work/hands/hand_ao.png    ambient occlusion with the body and staff as occluders (fingers on the staff, the cuff)
  work/hands/hand_mask.png  coverage of the hand islands (white)
1024 x 1024 in head-set UV space; hand_texture_set.py grades and merges them. Run after fit_hands.py."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

SKIN = os.path.expanduser('~/.config/blender/5.2/extensions/.user/blender_org/mpfb/data/skins/young_caucasian_male/'
                          'young_lightskinned_male_diffuse.png')
OUT = os.path.join(common.WORK, 'hands')
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v4.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Cleric_Rig']
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
try:
    sc.render.engine = 'CYCLES'
except TypeError:
    pass
sc.cycles.device = 'CPU'; sc.cycles.samples = 64
hands = [bpy.data.objects[n] for n in ('HandL', 'HandR')]
# the old hand faces sit where the new hands are: remove them (in memory only) so they do not occlude the AO bake
import bmesh
body = bpy.data.objects['Cleric']; oh = [0] * len(body.data.polygons)
body.data.attributes['old_hand'].data.foreach_get('value', oh)
bm = bmesh.new(); bm.from_mesh(body.data); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if oh[f.index]], context='FACES'); bm.to_mesh(body.data); bm.free()
skin = bpy.data.images.load(SKIN)


def target(name):
    img = bpy.data.images.new(name, 1024, 1024, alpha=False, float_buffer=False)
    img.generated_color = (0, 0, 0, 1)
    return img


def setup(kind, img):
    for o in hands:
        mat = bpy.data.materials.new(f'bake_{kind}_{o.name}'); mat.use_nodes = True
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
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
        nt.nodes.active = t
        o.data.materials.clear(); o.data.materials.append(mat)
        o.data.uv_layers.active = o.data.uv_layers['HandUV']
        o.data.uv_layers['HandUV'].active_render = True


for o in bpy.data.objects:
    o.select_set(o in hands)
bpy.context.view_layer.objects.active = hands[0]
for kind, btype, fname in (('skin', 'EMIT', 'hand_skin.png'), ('mask', 'EMIT', 'hand_mask.png'),
                           ('ao', 'AO', 'hand_ao.png')):
    img = target('hand_' + kind)
    setup(kind, img)
    bpy.ops.object.bake(type=btype, margin=0, use_clear=True, use_selected_to_active=False)
    img.filepath_raw = os.path.join(OUT, fname); img.file_format = 'PNG'; img.save()
    print('BAKED', fname)
