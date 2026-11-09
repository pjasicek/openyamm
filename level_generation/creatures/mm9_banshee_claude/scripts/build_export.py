"""Textured static export of the rigged master for clips_mm9.py. One mesh 'Banshee' with one material per blend primitive, because the engine sorts a blended creature primitive by its own rest-pose centre:
Banshee (torso), Skirt, ArmL, ArmR (sleeve, cuff, hand, claws), Cape, WingL, WingR, Head, HairL, HairR, Neck. Model y = 0 is the lowest bind vertex (floor_fix.py sets the hover).
Opaque here: build_actor_lods.py refuses blended materials; banshee_variants.py makes them blended. Args: blend out glb [notex]"""
import bpy, os, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
NOTEX = len(argv) > 2
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; cloak = bpy.data.objects['Cloak']; head = bpy.data.objects['Head']; hair = bpy.data.objects['Hair']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
for o in (body, cloak, head, hair):
    for mod in list(o.modifiers):
        if mod.type != 'ARMATURE':
            o.modifiers.remove(mod)


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = True
    if NOTEX:
        return mat
    nt = mat.node_tree
    bsdf = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(T, fname), check_existing=True)
        img.colorspace_settings.name = cs
        x = nt.nodes.new('ShaderNodeTexImage'); x.image = img
        return x
    b = tex(base, 'sRGB')
    nt.links.new(b.outputs['Color'], bsdf.inputs['Base Color'])
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


SLOTS = ['Banshee', 'BansheeSkirt', 'BansheeArmL', 'BansheeArmR', 'BansheeCape', 'BansheeWingL', 'BansheeWingR', 'BansheeHead', 'BansheeHairL', 'BansheeHairR', 'BansheeNeck']
BODYTEX = ('banshee_basecolor_rgba.png', 'banshee_normal_1k.png', 'banshee_metal_rough_1k.png')
CLOTH = ('banshee_cloth_rgba.png', 'banshee_cloth_normal.png', 'banshee_cloth_mr.png')
HEADT = ('banshee_head_a_rgba.png', 'banshee_head_normal_1k.png', 'banshee_head_metal_rough_1k.png')
HAIR = ('banshee_hair_rgba.png', 'banshee_cloth_normal.png', 'banshee_cloth_mr.png')
mats = {n: material(n, *(BODYTEX if i < 4 else CLOTH if i < 7 else HEADT if i in (7, 10) else HAIR)) for i, n in enumerate(SLOTS)}
UVNAME = 'UVMap'
for o in (body, cloak, head, hair):
    if not o.data.uv_layers:
        o.data.uv_layers.new(name=UVNAME)
    else:
        o.data.uv_layers.active.name = UVNAME
    for ln in [l.name for l in o.data.uv_layers]:
        if ln != UVNAME:
            o.data.uv_layers.remove(o.data.uv_layers[ln])
    o.data.materials.clear()
    for n in SLOTS:
        o.data.materials.append(mats[n])
# slots per face
def groups_of(o):
    names = {g.index: g.name for g in o.vertex_groups}
    return names


me = body.data
names = groups_of(body)


def arm_tag(nm):
    if nm.startswith('Zfing'):
        return 2 if nm[-2:] in ('04', '05', '06', '07') else 1     # 04-07 are the +x hand
    if nm.startswith('Z') and not nm.startswith('Zarmbase'):
        return 2 if nm.endswith('01') else 1
    return 0


vw = np.zeros((len(me.vertices), 3))
for v in me.vertices:
    for g in v.groups:
        vw[v.index, arm_tag(names[g.group])] += g.weight
idx = [p.vertices[:] for p in me.polygons]
part = np.zeros(len(idx), np.int32); me.attributes['part'].data.foreach_get('value', part)
slot = np.zeros(len(idx), np.int32)
for i, f in enumerate(idx):
    w = vw[list(f)].mean(0)
    if part[i] == 1:
        slot[i] = 1
    elif part[i] >= 2 or w[1:].sum() > 0.5:
        slot[i] = 2 + (1 if w[2] > w[1] else 0) if (w[1] + w[2]) > 0 else (2 if me.vertices[f[0]].co.x < 0 else 3)
    else:
        slot[i] = 0
me.polygons.foreach_set('material_index', slot.tolist())
print('SLOTS body', np.bincount(slot, minlength=4))
# cloak: the wings are the columns outside the shoulder
cm = cloak.data
cx = np.array([np.mean([cm.vertices[v].co.x for v in p.vertices]) for p in cm.polygons])
cs = np.where(cx < -0.2, 5, np.where(cx > 0.2, 6, 4))
cm.polygons.foreach_set('material_index', cs.tolist())
print('SLOTS cloak', np.bincount(cs, minlength=7)[4:])
hpv = np.zeros(len(head.data.vertices), np.int32); head.data.attributes['hpart'].data.foreach_get('value', hpv)
hslot = [10 if hpv[list(p.vertices)].max() == 5 else 7 for p in head.data.polygons]      # the neck loft and its stitch strip: blended, fading into the torso
head.data.polygons.foreach_set('material_index', hslot)
print('SLOTS neck', hslot.count(10))
hm = hair.data
hx = np.array([np.mean([hm.vertices[v].co.x for v in p.vertices]) for p in hm.polygons])
hair.data.polygons.foreach_set('material_index', np.where(hx < 0, 8, 9).tolist())
for o in (body, cloak, head, hair):
    for at in ('part', 'hpart', 'robe_s', 'robe_t'):
        if at in o.data.attributes:
            o.data.attributes.remove(o.data.attributes[at])
for o in bpy.data.objects:
    o.select_set(o in (body, cloak, head, hair))
bpy.context.view_layer.objects.active = body
for o in (body, cloak, head, hair):
    o.parent = rig
bpy.ops.object.join()
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.shade_smooth()
me = body.data
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'Banshee'; me.name = 'Banshee'
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', argv[1], len(me.polygons))
