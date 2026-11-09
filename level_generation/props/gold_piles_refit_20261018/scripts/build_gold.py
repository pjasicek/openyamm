"""Rebuild the nine rejected gold piles as supported coins and sprite-specific stacks.

Run in isolated background Blender. Every coin is closed; there is no mound/filler mesh.
"""
import json
import math
import random
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]

THICKNESS = .24


def save_image(name, values, data=False):
    height, width = values.shape[:2]
    image = bpy.data.images.new(name, width, height, alpha=False)
    image.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    rgba = np.concatenate([values[::-1], np.ones((height, width, 1))], axis=2)
    image.pixels[:] = np.clip(rgba, 0, 1).ravel()
    image.filepath_raw = str(PROJECT / 'textures' / (name + '.png'))
    image.file_format = 'PNG'
    image.save()
    image.pack()
    return image


def material():
    image = bpy.data.images.load(str(PROJECT / 'references/coin_face_readable.png'))
    image.scale(512, 512)
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(512, 512, 4)[::-1, :, :3]
    # Broad minting/patina regions survive mipmapping; fine image grain does not define the albedo.
    value = pixels @ np.array([.2126, .7152, .0722])
    fine = value.copy()
    for _ in range(12):
        fine = (fine + np.roll(fine, 1, 0) + np.roll(fine, -1, 0)
                + np.roll(fine, 1, 1) + np.roll(fine, -1, 1)) / 5
    gold = np.array([224, 145, 30], dtype=np.float32) / 255
    # Discrete material colours replace painted lighting gradients: bronze recess, gold, worn gold.
    dark = np.clip((.40 - fine) / .08, 0, 1)
    worn = np.clip((fine - .58) / .09, 0, 1) * (1-dark)
    base = np.broadcast_to(gold, pixels.shape).copy()
    base = base * (1-dark[..., None]) + np.array([105, 55, 30]) / 255 * dark[..., None]
    base = base * (1-worn[..., None]) + np.array([243, 185, 35]) / 255 * worn[..., None]
    rough = .30 + dark * .15 - worn * .08
    # OpenYAMM's weak environment reflection needs a diffuse share for readable gold.
    mr = np.stack([np.ones_like(value), rough, .70 * (1-dark) + .10 * dark], axis=-1)
    # A restrained +Y tangent normal describes minting; raised rims are real geometry.
    height = value.copy()
    for _ in range(2):
        height = (height * 2 + np.roll(height, 1, 0) + np.roll(height, -1, 0)
                  + np.roll(height, 1, 1) + np.roll(height, -1, 1)) / 6
    dy, dx = np.gradient(height * 4)
    normal = np.stack([-dx, dy, np.ones_like(dx)], axis=-1)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    normal = normal * .5 + .5
    base[:48, :48] = np.array([243, 185, 35]) / 255
    mr[:48, :48] = [1, .19, .85]
    normal[:48, :48] = [.5, .5, 1]
    base[:48, -48:] = np.array([155, 85, 30]) / 255
    mr[:48, -48:] = [1, .34, .70]
    normal[:48, -48:] = [.5, .5, 1]
    maps = [save_image('coin_base', base), save_image('coin_mr', mr, True),
            save_image('coin_normal', normal, True)]
    mat = bpy.data.materials.new('Minted gold, engraved face and bevelled rim')
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    for image, label in zip(maps, ['base', 'mr', 'normal']):
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = image
        if label == 'base':
            links.new(tex.outputs['Color'], shader.inputs['Base Color'])
        elif label == 'mr':
            separate = nodes.new('ShaderNodeSeparateColor')
            links.new(tex.outputs['Color'], separate.inputs['Color'])
            links.new(separate.outputs['Green'], shader.inputs['Roughness'])
            links.new(separate.outputs['Blue'], shader.inputs['Metallic'])
        else:
            node = nodes.new('ShaderNodeNormalMap')
            links.new(tex.outputs['Color'], node.inputs['Color'])
            links.new(node.outputs['Normal'], shader.inputs['Normal'])
    return mat


def layout(icon):
    """Positions transcribed from the reference paintings; shared MM6/MM7 art shares geometry."""
    coins = []
    seed = icon.replace('7item187', '6coinsm').replace('7item188', '6coinmid').replace('7item189', '6coinlg')
    rng = random.Random(seed)

    def stack(x, y, count, radius=1):
        for layer in range(count):
            # Very small offsets retain the readable horizontal bands of a real stack.
            coins.append(dict(x=x + rng.uniform(-.035, .035), y=y + rng.uniform(-.035, .035),
                              bottom=layer * THICKNESS, radius=radius, tilt=[0, 0], spin=rng.random() * 360,
                              stack=f'{x},{y}'))

    def loose(x, y, tilt_x=0, tilt_y=0, bottom=0, radius=1):
        coins.append(dict(x=x, y=y, bottom=bottom, radius=radius,
                          tilt=[tilt_x, tilt_y], spin=rng.random() * 360, stack=None))

    if icon == 'item204':
        stack(0, .55, 3)
        loose(-1.5, -.65, 16, -22)
        loose(.25, -1.3, 52, 8)
        loose(1.4, .1, 20, -45)
        loose(-1.35, 1.1, 0, 0)
        loose(1.05, 1.55, 0, 0)
    elif icon == 'item205':
        stack(0, .7, 5)
        stack(-1.8, -.65, 2)
        stack(-1.45, 1.25, 2)
        loose(.0, -1.65, 58, -3)
        loose(1.85, -1.15, 35, -22)
        loose(1.55, 1.2, 8, 20)
        loose(.7, -1.0)
    elif icon == 'item206':
        stack(.2, 1.15, 8)
        stack(-1.85, .4, 6)
        stack(2.15, .25, 4)
        stack(-.95, -1.35, 3)
        stack(1.9, 2.05, 2, .9)
        loose(-2.85, -.5, 18, -54)
        loose(-.1, -2.6, 48, 0)
        loose(1.6, -2.65, 40, 0)
        loose(2.9, -1.65, 30, 15, radius=.9)
        loose(3.25, -.25, 0, 0, radius=.9)
        loose(-2.7, 1.9, 0, 0, radius=.9)
        loose(-2.55, -1.95)
        loose(.15, -.45, 0, 0)
        loose(3.25, 1.5, 0, 0, radius=.9)
    elif seed == '6coinsm':
        stack(0, .5, 2)
        loose(-1.25, -.5, 18, -42)
        loose(.15, -1.2, 42, -8)
        loose(1.25, .1, 0, 0)
        loose(.8, 1.6, -20, 30)
        loose(-1.4, 1.15, 0, 0)
        loose(-1.8, -.1, 0, 0)
        loose(.3, -1.9, 0, 0)
        loose(1.65, -.95, 0, 0, radius=.85)
    elif seed == '6coinmid':
        # Low interleaved pile, with broad overlapping faces and no invented tall towers.
        for x, y in [(-2.8, .2), (-2.3, -1.35), (-1, -2.1), (.6, -2.1), (2, -1.5),
                     (3, -.25), (2.35, 1.15), (.85, 2), (-.9, 2), (-2.3, 1.4)]:
            loose(x, y, radius=.9)
        stack(-1, .25, 2)
        stack(1, .45, 2)
        stack(.15, 1.4, 3)
        loose(-1.5, -.9, 18, -22, .22)
        loose(.2, -1.0, 22, 0, .18)
        loose(1.8, -.6, 20, 20, .12)
    elif seed == '6coinlg':
        stack(-.8, 1.2, 8)
        stack(1.7, 1.2, 6)
        stack(.4, -.5, 3)
        for x, y in [(-3.0, .25), (-2.85, -1.1), (-1.8, -2.0), (-.1, -2.6),
                     (1.4, -2.45), (3.0, -1.7), (3.5, -.2), (2.9, 1.8), (-2.5, 1.8)]:
            loose(x, y, radius=.9)
        loose(-1.75, -.7, 30, -37)
        loose(.1, -1.9, 38, 2)
        loose(2.05, -1.8, 42, 15)
        loose(2.8, .1, 0, 12, .16, .85)
    else:
        raise AssertionError(icon)
    assert 7 <= len(coins) <= 60
    return coins


def coin(bm, uv, spec, sides, profile):
    radius = spec['radius']
    rx, ry = [math.radians(a) for a in spec['tilt']]
    transform = Matrix.Rotation(rx, 4, 'X') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(math.radians(spec['spin']), 4, 'Z')
    local = [[Vector((r * radius * math.cos(k * math.tau / sides),
                      r * radius * math.sin(k * math.tau / sides), z)) for k in range(sides)]
             for r, z in profile]
    points = [transform @ co for ring in local for co in ring]
    bottom = min(co.z for co in points)
    translation = Vector((spec['x'], spec['y'], spec['bottom'] - bottom))
    rings = [[bm.verts.new(transform @ co + translation) for co in ring] for ring in local]

    def face(vertices, coords, smooth=False):
        f = bm.faces.new(vertices)
        f.smooth = smooth
        for loop, coord in zip(f.loops, coords):
            loop[uv].uv = coord
        return f

    disk_uv = [( .5 + .475 * math.cos(k * math.tau / sides),
                 .5 + .475 * math.sin(k * math.tau / sides)) for k in range(sides)]
    face(rings[0][::-1], disk_uv[::-1])
    face(rings[-1], disk_uv)
    for level in range(len(rings) - 1):
        for k in range(sides):
            n = (k + 1) % sides
            # Darker minted side bands separate stacked coins; the broad raised rim stays bright.
            side = profile[level][1] < THICKNESS-.06 and profile[level+1][1] > .06
            left = .92 if side else .02
            face([rings[level][k], rings[level][n], rings[level+1][n], rings[level+1][k]],
                 [(left, .92), (left+.06, .92), (left+.06, .98), (left, .98)], True)


def build(icon, specs, mat, lod):
    sides = [20, 12, 12, 8][lod]
    profiles = [
        [(.94, 0), (1, .04), (1, .20), (.94, .24), (.82, .24), (.78, .18)],
        [(.94, 0), (1, .04), (1, .20), (.94, .24), (.78, .18)],
        [(.94, 0), (1, .24), (.78, .18)],
        [(.94, 0), (1, .24), (.78, .18)],
    ]
    profile = profiles[lod]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    for spec in specs:
        coin(bm, uv, spec, sides, profile)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='EAR_CLIP')
    assert all(edge.is_manifold for edge in bm.edges), icon
    assert bm.calc_volume() > 0
    # Each disconnected solid is a real coin, never a dome or invisible gap-filler.
    assert len(bm.verts) == len(specs) * sides * len(profile)
    coords = np.array([v.co[:] for v in bm.verts])
    centre = (coords.min(0) + coords.max(0)) / 2
    for v in bm.verts:
        v.co -= Vector((centre[0], centre[1], coords[:, 2].min()))
        # A pile's long axis is Blender Y / glTF Z.
        if np.ptp(coords[:, 0]) >= np.ptp(coords[:, 1]):
            v.co.x, v.co.y = -v.co.y, v.co.x
        v.co *= .014
    mesh = bpy.data.meshes.new(icon + f'_LOD{lod}')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(icon + (f'_LOD{lod}' if lod else ''), mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mat)
    assert len(mesh.polygons) <= 15000
    return obj


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mat = material()
    ownership = json.loads((PROJECT / 'ownership.json').read_text())
    receipts = {}
    for row in ownership:
        icon = row['icon']
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        specs = layout(icon)
        objects = [build(icon, specs, mat, lod) for lod in range(4)]
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT / 'blends' / (icon + '.blend')))
        raw = PROJECT / 'work/unlinked' / (icon + '_export.glb')
        bpy.ops.export_scene.gltf(filepath=str(raw), export_format='GLB', use_selection=True,
                                 export_apply=True, export_image_format='AUTO', export_materials='EXPORT')
        receipts[icon] = dict(coins=len(specs), triangles=[len(o.data.polygons) for o in objects],
                              layout=specs, export='work/exports/' + icon + '_export.glb')
    (PROJECT / 'work/build_receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print('BUILT', {k: (v['coins'], v['triangles']) for k, v in receipts.items()}, flush=True)


if __name__ == '__main__':
    main()
