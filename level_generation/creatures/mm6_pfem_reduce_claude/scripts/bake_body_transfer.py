"""Head-detail rebuild (2026-10-14): the body set's geometry and UVs changed with the re-decimation, so the existing
Meshy body return (meshy/retexture_r45, on the round-3 body UVs) is carried onto the new body UVs by baking, selected
to active, from the round-3 body (backup_round3/r45_master.blend) instead of a new body retexture. Base colour,
metallic and roughness bake as emission; the normal map bakes in tangent space (Meshy's DirectX green is flipped for
Blender and back for the output). Out: meshy/retexture_r45_baked/texture_urls_0_*.png (2048, a drop-in Meshy return
for compose_r45.py with RETEX_JOB=retexture_r45_baked)."""
import os

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'meshy', 'retexture_r45', 'texture_urls_0')
OUT = os.path.join(HERE, 'meshy', 'retexture_r45_baked'); os.makedirs(OUT, exist_ok=True)
SIZE = 2048
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
sc = bpy.context.scene


def body_copy(obj, name):
    """Static copy of a peasant mesh with only the body texture set (head == 0), in world space."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), depsgraph=dg)
    me.transform(obj.matrix_world)
    bm = bmesh.new(); bm.from_mesh(me)
    head = bm.faces.layers.int.get('head')
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[head] != 0], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


new = body_copy(bpy.data.objects['Peasant'], 'NewBody')
with bpy.data.libraries.load(os.path.join(HERE, 'backup_round3', 'r45_master.blend')) as (src, dst):
    dst.objects = ['Peasant']
old_src = [o for o in bpy.data.objects if o.name.startswith('Peasant') and o is not bpy.data.objects['Peasant']
           and o.type == 'MESH'][0]
sc.collection.objects.link(old_src)
for m in list(old_src.modifiers):
    old_src.modifiers.remove(m)
old_src.parent = None; old_src.matrix_world = bpy.data.objects['Peasant'].matrix_world.copy()
old = body_copy(old_src, 'OldBody')
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o not in (new, old)


def image(path, colour):
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    return im


# old material: emission of a chosen map, plus the Meshy normal map (green flipped to Blender's OpenGL)
mat = bpy.data.materials.new('OldMeshy'); mat.use_nodes = True; nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
outn = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
emit = nt.nodes.new('ShaderNodeEmission'); tex = nt.nodes.new('ShaderNodeTexImage')
ntex = nt.nodes.new('ShaderNodeTexImage'); ntex.image = image(SRC + '_normal.png', False)
sep = nt.nodes.new('ShaderNodeSeparateColor'); inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'
inv.inputs[0].default_value = 1.0; comb = nt.nodes.new('ShaderNodeCombineColor'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(ntex.outputs['Color'], sep.inputs['Color']); nt.links.new(sep.outputs['Green'], inv.inputs[1])
nt.links.new(sep.outputs['Red'], comb.inputs['Red']); nt.links.new(inv.outputs[0], comb.inputs['Green'])
nt.links.new(sep.outputs['Blue'], comb.inputs['Blue']); nt.links.new(comb.outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
nt.links.new(tex.outputs['Color'], emit.inputs['Color'])
old.data.materials.clear(); old.data.materials.append(mat)

target = bpy.data.materials.new('NewTarget'); target.use_nodes = True
tnode = target.node_tree.nodes.new('ShaderNodeTexImage'); target.node_tree.nodes.active = tnode
new.data.materials.clear(); new.data.materials.append(target)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
bake = sc.render.bake
bake.use_selected_to_active = True; bake.use_cage = False; bake.cage_extrusion = 0.012; bake.max_ray_distance = 0.03
bake.margin = 8
bpy.ops.object.select_all(action='DESELECT'); old.select_set(True); new.select_set(True)
bpy.context.view_layer.objects.active = new


def run(kind, name, colour, src_map=None):
    out = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=False)
    out.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    tnode.image = out
    if src_map:
        tex.image = image(SRC + src_map, colour)
        nt.links.new(emit.outputs['Emission'], outn.inputs['Surface'])
    else:
        nt.links.new(bsdf.outputs['BSDF'], outn.inputs['Surface'])
    bpy.ops.object.bake(type=kind, normal_space='TANGENT') if kind == 'NORMAL' else bpy.ops.object.bake(type=kind)
    return out


for suffix, colour in (('_base_color.png', True), ('_metallic.png', False), ('_roughness.png', False)):
    im = run('EMIT', 'baked' + suffix, colour, suffix)
    im.filepath_raw = os.path.join(OUT, 'texture_urls_0' + suffix); im.file_format = 'PNG'; im.save()
im = run('NORMAL', 'baked_normal', False)
px = np.array(im.pixels[:], np.float32).reshape(SIZE, SIZE, 4)
px[..., 1] = 1.0 - px[..., 1]          # back to Meshy's DirectX green
im.pixels[:] = px.ravel()
im.filepath_raw = os.path.join(OUT, 'texture_urls_0_normal.png'); im.file_format = 'PNG'; im.save()
print('BAKED body maps to', OUT, 'new body faces', len(new.data.polygons), 'old', len(old.data.polygons))
