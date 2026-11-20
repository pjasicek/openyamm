"""MM6 skull pile `sklplrev` (86 placements; 214 x 153 units, static), version 3: high-to-low bake. The full-detail
Meshy multi-image pile (4.66M triangles, from the Codex HD masters) is the high mesh; the game mesh is its collapse
decimation (make_pile_low.py) with its own UVs, textured by a 2k bake of the high mesh's colour, tangent normals and
ambient occlusion (bake_pile.py, compose_pile.py). LOD1 is a decimation of the low mesh, LOD2/LOD3 of the far mesh
(add_far_lod.py), whose own charts sit in a corner of the same atlas: one texture set for every level. COLOR_0 is white (light and shade live in the texture).
Writes work/skullpile_export.glb (+ work/skullpile.blend).
Usage: blender --background ../work/pile_low.blend --python build_pile_baked.py -- [texture prefix]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

pl = blib.pl
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREFIX = args[0] if args else 'pilebaked'
LOD_TRIS = (11000, 4000, 2000, 300)
FAR_FROM = 2                      # levels from here are made from the far mesh (add_far_lod.py), its own baked charts

import numpy as np  # noqa: E402


def plain_uv():
    """A texel of the far mesh's charts (the atlas corner, add_far_lod.py) at the median colour of its lit texels, in
    a smooth 8 x 8 neighbourhood: one representative bone tone for the farthest mound."""
    image = next(n for n in material.node_tree.nodes if n.type == 'TEX_IMAGE').image
    w, h = image.size
    grid = np.array(image.pixels[:], np.float32).reshape(h, w, 4)[..., :3]      # rows bottom-up, as UV v
    corner = int(w * 0.875)
    region = grid[corner:, corner:]
    blocks = region.reshape(region.shape[0] // 8, 8, region.shape[1] // 8, 8, 3)
    lum = blocks.mean((1, 3)) @ np.array([0.2126, 0.7152, 0.0722])
    lit = lum > 0.08
    target = np.median(lum[lit])
    score = np.abs(lum - target) + 0.04 * blocks.std((1, 3)).sum(-1) + (~lit) * 10
    row, col = np.unravel_index(np.argmin(score), score.shape)
    print('PLAIN texel', np.round(blocks[row, :, col].mean((0, 1)) * 255).tolist(), 'target lum', round(float(target), 3))
    return ((corner + (col + 0.5) * 8) / w, (corner + (row + 0.5) * 8) / h)


def far_mound(obj, target):
    """The farthest level: voxel-remeshed (10 units) and decimated freely; every corner samples one plain bone texel
    of the shared atlas (decimating the far mesh's charts to 300 triangles stretched them into shards)."""
    mod = obj.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = blib.u(10.0)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    pl.decimate_to(obj, target)
    layer = obj.data.uv_layers.new(name='UVMap')
    uv = plain_uv()
    for loop in layer.data:
        loop.uv = uv


bpy.data.objects.remove(bpy.data.objects['high'])
low = bpy.data.objects['low']
material = blib.texture_material('Bone', PREFIX)
far_mesh = bpy.data.objects['far']
# LOD3 decimates the far mesh far below its bake: the tangent normals no longer fit (shards of light), so it shares
# the base colour image without the normal map (the GLB stores the image once).
plain = material.copy(); plain.name = 'BoneFar'
for node in [n for n in plain.node_tree.nodes if n.type == 'NORMAL_MAP']:
    plain.node_tree.nodes.remove(node)
lods = []
for level, target in enumerate(LOD_TRIS):
    name = 'SkullPile' if level == 0 else f'SkullPile_LOD{level}'
    obj = blib.duplicate(far_mesh if level >= FAR_FROM else low, name)
    obj.data.materials.clear(); obj.data.materials.append(plain if level == len(LOD_TRIS) - 1 else material)
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    if level == len(LOD_TRIS) - 1:
        far_mound(obj, target)                     # decimation slivers smeared the charts at 300 triangles
    else:
        pl.decimate_to(obj, target)
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, 0.0)
    for p in obj.data.polygons:
        p.use_smooth = True
    pl.white_colour(obj)
    print('LEVEL', level, name, 'tris', pl.triangles(obj))
    lods.append(obj)
bpy.data.objects.remove(low)
bpy.data.objects.remove(far_mesh)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, 'skullpile.blend'))
pl.export(lods, os.path.join(blib.WORK, 'skullpile_export.glb'))
