"""Build the recoloured thrones and the teal statue (lane S, D-66) from shipped models. No Meshy.

    blender -b --python build.py -- <project dir>

Writes <project>/export/xeen_deco_throne_steel.glb, xeen_deco_throne_gold.glb (the MM9 throne, 220 triangles, one
material, new base colour + metallic-roughness maps) and <project>/work/xeen_deco_statue_teal_raw.glb (MM8's elf
statue in teal metal on a built two-step plinth; LOD1/LOD2 by collapse decimation; link with
tools/link_static_model_lods.py). Textures come from scripts/recolour.py (work/tex/)."""
import math
import os
import sys

import bmesh
import bpy

proj = sys.argv[sys.argv.index('--') + 1]
ROOT = os.path.abspath(os.path.join(proj, '..', '..', '..'))
SRC = os.path.join(ROOT, 'assets_source')
TEX = os.path.join(proj, 'work', 'tex')
EXPORT = os.path.join(proj, 'export')
os.makedirs(EXPORT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path, non_color=False):
    img = bpy.data.images.load(path)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


def upstream_image(socket):
    stack = [l.from_node for l in socket.links]
    while stack:
        n = stack.pop()
        if n.type == 'TEX_IMAGE':
            return n
        stack += [l.from_node for i in n.inputs for l in i.links]
    raise RuntimeError('no image upstream')


def retexture(mat, base_png, mr_png):
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    base_node = upstream_image(bsdf.inputs['Base Color'])
    base_node.image = load(base_png)
    for name in ('Metallic', 'Roughness'):
        for link in list(bsdf.inputs[name].links):
            nt.links.remove(link)
    mr = nt.nodes.new('ShaderNodeTexImage')
    mr.image = load(mr_png, True)
    uv = base_node.inputs['Vector'].links[0].from_node if base_node.inputs['Vector'].links else None
    if uv is not None:
        nt.links.new(uv.outputs[0], mr.inputs['Vector'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])


def export(path):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_yup=True, export_apply=True,
                              export_image_format='AUTO')
    print('EXPORTED', path)


def tris(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


# Thrones.
for tag in ('steel', 'gold'):
    reset()
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, 'worlds/mm9/models/mm9_deco_throne.glb'))
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    ob.name = ob.data.name = f'xeen_throne_{tag}'
    mat = ob.data.materials[0]
    mat.name = f'xeen_throne_{tag}'
    retexture(mat, os.path.join(TEX, f'{tag}_base.png'), os.path.join(TEX, f'{tag}_mr.png'))
    export(os.path.join(EXPORT, f'xeen_deco_throne_{tag}.glb'))

# Teal statue.
reset()
bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, 'engine/models/mm8_deco_elfstatue.glb'))
scene = bpy.context.scene
ob = next(o for o in scene.objects if o.type == 'MESH')
for o in list(scene.objects):
    if o is not ob:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.update()
for mat in ob.data.materials:
    key = 'blade' if 'blade' in mat.name.lower() else 'stone'
    retexture(mat, os.path.join(TEX, f'teal_{key}_base.png'), os.path.join(TEX, f'teal_{key}_mr.png'))
    mat.name = f'xeen_statue_teal_{key}'
    mat.use_backface_culling = True

# Plinth: a base slab and a die, bevelled, in dark Ancient steel (flat colour). Statue raised onto the die.
xs = [(ob.matrix_world @ v.co) for v in ob.data.vertices]
feet = [p for p in xs if p.z < 0.08]
cx = (min(p.x for p in feet) + max(p.x for p in feet)) / 2
cy = (min(p.y for p in feet) + max(p.y for p in feet)) / 2
print('FEET centre', round(cx, 3), round(cy, 3))
SLAB_H, DIE_H = 0.10, 0.32
ob.location.x -= cx
ob.location.y -= cy
ob.location.z += SLAB_H + DIE_H
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

pm = bpy.data.materials.new('xeen_statue_teal_plinth')
pm.use_nodes = True
pb = next(n for n in pm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
pb.inputs['Base Color'].default_value = (0.030, 0.052, 0.058, 1.0)
pb.inputs['Metallic'].default_value = 0.7
pb.inputs['Roughness'].default_value = 0.5
pm.use_backface_culling = True

bm = bmesh.new()
for (sx, sy, z0, h) in ((1.06, 0.86, 0.0, SLAB_H), (0.90, 0.70, SLAB_H, DIE_H)):
    r = bmesh.ops.create_cube(bm, size=1.0)
    verts = r['verts']
    for v in verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z = z0 + (v.co.z + 0.5) * h
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.018, segments=1, affect='EDGES')
plinth_mesh = bpy.data.meshes.new('plinth')
bm.to_mesh(plinth_mesh)
bm.free()
plinth = bpy.data.objects.new('plinth', plinth_mesh)
scene.collection.objects.link(plinth)
plinth_mesh.materials.append(pm)
# The joined mesh needs a UV layer on every face; the plinth's faces get a box projection (unused by its material).
plinth_mesh.uv_layers.new(name=ob.data.uv_layers[0].name)
bpy.ops.object.select_all(action='DESELECT')
plinth.select_set(True)
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
ob.name = ob.data.name = 'xeen_statue_teal'
for p in ob.data.polygons:
    p.use_smooth = p.use_smooth  # keep the source's shading
counts = [tris(ob.data)]
for level, ratio in enumerate((0.45, 0.18), 1):
    lod = bpy.data.objects.new(f'xeen_statue_teal_LOD{level}', ob.data.copy())
    scene.collection.objects.link(lod)
    mod = lod.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.select_all(action='DESELECT')
    lod.select_set(True)
    bpy.context.view_layer.objects.active = lod
    bpy.ops.object.modifier_apply(modifier='dec')
    counts.append(tris(lod.data))
print('STATUE_TRIS', counts)
bb = [ob.matrix_world @ v.co for v in ob.data.vertices]
print('STATUE_BOUNDS', [round(min(p[i] for p in bb), 3) for i in range(3)], [round(max(p[i] for p in bb), 3)
                                                                              for i in range(3)])
export(os.path.join(proj, 'work', 'xeen_deco_statue_teal_raw.glb'))
