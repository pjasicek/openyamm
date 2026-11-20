"""MM6 skull pile `sklplrev` (86 placements in 10 maps, dungeons and outdoors; 214 x 153 units, static) from Meshy:
Codex HD masters of the native sprite (skullpile/references_hd/), Meshy Smart Topology (11.4k triangles, about 150
skull-sized lumps), squashed across to the sprite's width profile (squash_pile.py), Smart UV, and a Meshy retexture
from the four masters that paints a skull face on each lump (work/skullpile_tex.blend).
LODs by collapse decimation of the Meshy mesh (UVs kept): LOD_TRIS. COLOR_0 is vertex occlusion (deep gaps between
the skulls, as the sprite's near-black hollows) times one tint that brings the textured mean to the sprite's measured
mean colour. Writes work/skullpile_export.glb (+ .blend).
Usage: blender --background --python build_skullpile.py -- [texture prefix (default skullpile)]"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

pl = blib.pl
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PREFIX = args[0] if args else 'skullpile'
LOD_TRIS = (8000, 1600, 600, 220)
NATIVE_MEAN = (99, 92, 79)                 # sRGB mean of the opaque native sklplrev pixels
OCCLUSION = dict(rays=(40, 24, 16, 10), distance=blib.u(30), strength=0.3)
GAMMA = 1.0                                # occlusion exponent (the Meshy texture already paints dark gaps)

bpy.ops.wm.open_mainfile(filepath=os.path.join(blib.WORK, 'skullpile_tex.blend'))
source = bpy.data.objects['skullpile']
source.data.materials.clear()
for old in list(bpy.data.materials):
    bpy.data.materials.remove(old)
mat = blib.texture_material('Bone', PREFIX)
source.data.materials.append(mat)
image = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE').image
pixels = np.array(image.pixels[:], np.float32).reshape(-1, 4)[:, :3]
texture_mean = blib.srgb_to_linear(pixels).mean(0) if not image.is_float else pixels.mean(0)


def far_mound(obj, target):
    """The farthest level: the skulls fused into one lumpy mound (voxel remesh, then decimation). Its UVs all point
    at one texel of average bone colour; COLOR_0 occlusion carries the shading."""
    mod = obj.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = blib.u(9.0)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    pl.decimate_to(obj, target)
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, 0.0)              # the voxel shell reaches below the ground
    w, h = image.size
    grid = np.array(image.pixels[:], np.float32).reshape(h, w, 4)[:, :, :3]
    target_colour = np.array(image.pixels[:], np.float32).reshape(-1, 4)[:, :3].mean(0)
    smooth = grid.reshape(h // 8, 8, w // 8, 8, 3).mean((1, 3))
    flat = grid.reshape(h // 8, 8, w // 8, 8, 3).std((1, 3)).sum(-1)
    score = np.abs(smooth - target_colour).sum(-1) + flat
    row, col = np.unravel_index(np.argmin(score), score.shape)
    uv = ((col + 0.5) * 8 / w, (row + 0.5) * 8 / h)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    layer = obj.data.uv_layers[0]
    for loop in layer.data:
        loop.uv = uv


lods = []
for level, target in enumerate(LOD_TRIS):
    name = 'SkullPile' if level == 0 else f'SkullPile_LOD{level}'
    obj = blib.duplicate(source, name)
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    if level == len(LOD_TRIS) - 1:
        far_mound(obj, target)
    else:
        pl.decimate_to(obj, target)
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, 0.0)              # decimation and the voxel shell can dip below the ground
    for p in obj.data.polygons:
        p.use_smooth = True
    occlusion = pl.vertex_occlusion(obj, rays=OCCLUSION['rays'][level], distance=OCCLUSION['distance'],
                                    strength=OCCLUSION['strength'], floor=True)
    attr = obj.data.color_attributes['Color']
    colours = np.empty(len(obj.data.vertices) * 4, np.float32); attr.data.foreach_get('color', colours)
    colours = colours.reshape(-1, 4)
    colours[:, :3] **= GAMMA
    # The shaded texture (shade_pile.py) already carries the sprite's light and tones: COLOR_0 only adds the mild
    # vertex occlusion, normalised so the most open vertices stay at one.
    factor = np.full(3, 1.0 / max(float(colours[:, 0].max()), 1e-3))
    colours[:, :3] *= factor
    attr.data.foreach_set('color', colours.ravel())
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'occlusion', round(occlusion, 3),
          'factor', np.round(factor, 3).tolist(), 'clipped', round(float((colours[:, :3] > 1).mean()), 3))
    lods.append(obj)
bpy.data.objects.remove(source)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, 'skullpile.blend'))
pl.export(lods, os.path.join(blib.WORK, 'skullpile_export.glb'))
