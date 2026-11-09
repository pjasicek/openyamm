"""Textured static export of the rigged master for clips_mm9.py. One mesh 'Ghost' with four blended materials, because the engine sorts a blended creature primitive by its own
rest-pose centre: Ghost (torso + robe), GhostArmL, GhostArmR (sleeve, cuff, hand), GhostHead. Model y = 0 is the lowest bind vertex (floor_fix.py sets the hover). Opaque here: build_actor_lods.py refuses blended materials; ghost_variants.py makes them blended.
Args: blend out glb"""
import bpy, os, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; head = bpy.data.objects['Head']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
head.modifiers.clear()
for mod in list(body.modifiers):
    if mod.type != 'ARMATURE':
        body.modifiers.remove(mod)
for o in bpy.data.objects:
    o.select_set(o in (body, head))
bpy.context.view_layer.objects.active = body
nb = len(body.data.polygons)
bpy.ops.object.join()
me = body.data
n = len(me.polygons)


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = True
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


me.materials.clear()
for name in ('Ghost', 'GhostArmL', 'GhostArmR'):
    me.materials.append(material(name, 'ghost_basecolor_rgba.png', 'ghost_normal_1k.png', 'ghost_metal_rough_1k.png'))
me.materials.append(material('GhostHead', 'ghost_head_b_rgba.png', 'ghost_head_normal_1k.png', 'ghost_head_metal_rough_1k.png'))
# material per face: arm chain weight decides
names = {g.index: g.name for g in body.vertex_groups}


def arm_tag(nm):
    if nm.startswith('Finger L') or (nm.startswith('Z') and not nm.endswith('01') and not nm.startswith('Zarmbase')):
        return 1
    if nm.startswith('Finger R') or (nm.startswith('Z') and nm.endswith('01') and not nm.startswith('Zarmbase')):
        return 2
    return 0


vw = np.zeros((len(me.vertices), 3))
for v in me.vertices:
    for g in v.groups:
        vw[v.index, arm_tag(names[g.group])] += g.weight
idx = np.array([p.vertices[:] for p in me.polygons])
fw = vw[idx].mean(1)
slot = fw.argmax(1).astype(np.int32)
# no primitive may get a head face or a robe face
slot[nb:] = 3
me.polygons.foreach_set('material_index', slot.tolist())
print('SLOTS', np.bincount(slot, minlength=4))
for at in ('part', 'hand', 'graft_s', 'graft_side', 'robe_s', 'robe_t', 'fid'):
    if at in me.attributes:
        me.attributes.remove(me.attributes[at])
for ln in [l.name for l in me.uv_layers]:
    if ln != 'UVMap':
        me.uv_layers.remove(me.uv_layers[ln])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'Ghost'; me.name = 'Ghost'
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', use_selection=True, export_animations=False,
                          export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', argv[1], len(me.polygons))
