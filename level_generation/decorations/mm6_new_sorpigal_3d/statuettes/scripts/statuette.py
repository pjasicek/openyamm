"""Gold statuettes ped01-ped05 on the unchanged ped06 pedestal (../props/work/pedestal.blend, the installed
mm6_deco_pedestal.glb's LODs and materials).

Per animal (ANIMALS): the full-detail Meshy model (meshy/<animal>_hd_v1/, from the Codex HD three-quarter master) is
turned so the head points to -x (the sprite's view is the animal's left side, camera at -y), grounded, scaled to the
statuette's height above the slab measured on the sprite (each sprite normalised by its own pedestal's pixel height),
and placed on the slab with the sprite's horizontal offset. The game mesh is a collapse decimation of a voxel remesh
(LOW_TRIS) with Smart UV; tangent normals and ambient occlusion of the high mesh are baked onto it (TEX px). The
surface is a polished, slightly worn gold (metallic 1): base colour = GOLD x a cavity term from the AO, roughness
lower on exposed forms than in the cavities. LOD1 decimates LOD0 (same textures); LOD2 is a voxel mound of it.
Each pedestal LOD gets the statuette LOD of the same index.

Stages: `prep` (import, orient, scale, low mesh, UVs -> work/<animal>_low.blend), `bake` (-> work/<animal>_{normal,
ao}.png), `textures` (python, -> textures/<animal>_*), `build` (-> work/<animal>_export.glb).
Usage: blender --background --python statuette.py -- <animal> prep|bake|build ; python3 statuette.py <animal> textures"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
TEXTURES = os.path.join(HERE, 'textures')
PROPS = os.path.join(HERE, '..', 'props')
UNITS = 81.7
SLAB = 150.0                     # top of the pedestal's slab (map units)
SLAB_TOP = 2 * 0.216 * SLAB       # the slab's top face, side length (props/scripts/build_pedestal.py capital: 64.8)
FILL = 0.875                      # footprint share of the slab top (85-90 %)
CAP = 0.40                        # figure height at most this share of the pedestal height
TEX = 512
LOW_TRIS = (1400, 600, 220)
GOLD = (186, 156, 84)            # sRGB, worn gold toward the sprite's olive (median 135, 100, 38)

# Length (along x, the sprite's horizontal extent) and height above the slab of the figure, and the horizontal offset of
# its centre (map units, + = right in the sprite), measured on the x2 sprite against the slab (172 px = the model's
# 66.6-unit capital); the turn (degrees about z) that brings the Meshy model's head (Meshy front, -y) to -x; the sprite.
ANIMALS = {
    'bear': {'length': 51.5, 'height': 24.4, 'offset': -5.4, 'yaw': -90.0, 'sprite': 'ped01'},
    'tiger': {'length': 61.6, 'height': 28.7, 'offset': -7.0, 'yaw': -90.0, 'sprite': 'ped02'},
    'eagle': {'length': 32.1, 'height': 33.7, 'offset': -5.8, 'yaw': -90.0, 'sprite': 'ped03'},
    'wolf': {'length': 55.0, 'height': 34.1, 'offset': -0.2, 'yaw': -90.0, 'sprite': 'ped04'},
    'dragon': {'length': 54.2, 'height': 46.1, 'offset': -0.6, 'yaw': -90.0, 'sprite': 'ped05', 'fit': 'height'},
}


def u(value):
    return value / UNITS


def textures(animal):
    """Base colour (gold x cavity) and metallic-roughness from the baked AO; the normal map as baked."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    ao = np.asarray(Image.open(os.path.join(WORK, f'{animal}_ao.png')).convert('L'), np.float64) / 255
    ao = ndimage.gaussian_filter(ao, 0.7)
    cavity = np.clip((ao - 0.15) / 0.85, 0, 1) ** 1.3
    gold = np.array(GOLD, np.float64) / 255
    linear = np.where(gold <= 0.04045, gold / 12.92, ((gold + 0.055) / 1.055) ** 2.4)
    shade = 0.16 + 0.84 * cavity ** 1.4            # deep cavities near the sprite's dark brown-olive gold
    base_linear = linear[None, None, :] * shade[..., None]
    # Worn: fine pitting (two octaves of seeded noise) darkens and roughens the surface in speckles, as the sprite's
    # gold is grainy; the exposed tops are a touch paler, the hollows browner.
    rng = np.random.default_rng(sum(map(ord, animal)))
    pits = sum(ndimage.gaussian_filter(rng.normal(size=ao.shape), sigma) * weight
               for sigma, weight in ((0.8, 1.0), (3.0, 1.6)))
    pits = (pits - pits.mean()) / pits.std()
    wear = np.clip(1 + 0.16 * pits, 0.6, 1.3)
    base_linear *= wear[..., None]
    base_linear *= (1 + 0.10 * (cavity[..., None] - 0.5) * np.array([0.2, 0.6, 1.4]))
    base = np.where(base_linear <= 0.0031308, base_linear * 12.92, 1.055 * np.maximum(base_linear, 0) ** (1 / 2.4) - 0.055)
    Image.fromarray(np.round(np.clip(base, 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(TEXTURES, f'{animal}_basecolor.png'))
    rough = np.clip(0.34 + 0.28 * (1 - cavity) - 0.08 * pits, 0.2, 0.75)
    mr = np.zeros(ao.shape + (3,)); mr[..., 0] = 1; mr[..., 1] = rough; mr[..., 2] = 1.0
    Image.fromarray(np.round(mr * 255).astype(np.uint8)).save(os.path.join(TEXTURES, f'{animal}_mr.png'))
    Image.open(os.path.join(WORK, f'{animal}_normal.png')).save(os.path.join(TEXTURES, f'{animal}_normal.png'))
    print('TEXTURES', animal, 'cavity mean', round(float(cavity.mean()), 3))


def blender_main(animal, stage):
    import bmesh
    import bpy
    import numpy as np
    from mathutils import Matrix, Vector
    sys.path.insert(0, os.path.join(PROPS, 'scripts'))
    import props_lib as pl
    spec = ANIMALS[animal]

    def select(obj):
        for o in bpy.data.objects:
            o.select_set(o is obj)
        bpy.context.view_layer.objects.active = obj

    def duplicate(obj, name):
        dup = obj.copy(); dup.data = obj.data.copy(); dup.name = name; dup.data.name = name
        bpy.context.scene.collection.objects.link(dup)
        return dup

    def drop_crumbs(obj, fraction=0.01):
        bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
        label = np.full(len(bm.verts), -1); count = 0
        for v in bm.verts:
            if label[v.index] >= 0:
                continue
            stack = [v]; label[v.index] = count
            while stack:
                w = stack.pop()
                for e in w.link_edges:
                    o = e.other_vert(w)
                    if label[o.index] < 0:
                        label[o.index] = count; stack.append(o)
            count += 1
        sizes = np.bincount(label)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if sizes[label[v.index]] < fraction * len(bm.verts)],
                         context='VERTS')
        bm.to_mesh(obj.data); bm.free()
        return count

    if stage == 'prep':
        bpy.ops.wm.read_factory_settings(use_empty=True)
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', f'{animal}_hd_v1', 'model_urls_glb.glb'))
        meshes = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
        for o in bpy.data.objects:
            o.select_set(o in meshes)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1:
            bpy.ops.object.join()
        high = bpy.context.view_layer.objects.active
        for o in [o for o in bpy.data.objects if o is not high]:
            bpy.data.objects.remove(o)
        high.parent = None
        select(high)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        high.name = high.data.name = 'high'
        high.data.materials.clear()
        pieces = drop_crumbs(high)
        high.data.transform(Matrix.Rotation(math.radians(spec['yaw']), 4, 'Z'))
        co = np.array([v.co[:] for v in high.data.vertices])
        lo, hi = co.min(0), co.max(0)
        across = u(spec['length']) / (hi[0] - lo[0])
        up = u(spec['height']) / (hi[2] - lo[2])
        if spec.get('fit') == 'height':                      # the height rules (the dragon's raised neck)
            across = min(max(across, up * 0.8), up * 1.25)
        else:                                                # fit both, within 20 % of a uniform scale
            up = min(max(up, across * 0.8), across * 1.25)
        # Enlarged (user review, 2026-10-09): from the sprite fit, a uniform scale-up so the footprint fills FILL of the
        # slab top along x and at most FILL across, the figure at most CAP of the pedestal height, never smaller than
        # the sprite fit; centred on the slab.
        size_x, size_y, size_z = (hi[0] - lo[0]) * across, (hi[1] - lo[1]) * across, (hi[2] - lo[2]) * up
        enlarge = max(1.0, min(u(FILL * SLAB_TOP) / size_x, u(FILL * SLAB_TOP) / size_y, u(CAP * SLAB) / size_z))
        across *= enlarge; up *= enlarge
        print('ENLARGE', animal, round(enlarge, 3))
        centre = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
        high.data.transform(Matrix.Translation(Vector((0, 0, u(SLAB)))) @
                            Matrix.Diagonal((across, across, up, 1)) @ Matrix.Translation(-centre))
        co = np.array([v.co[:] for v in high.data.vertices])
        size = (co.max(0) - co.min(0)) * UNITS
        low = duplicate(high, 'low')
        select(low)
        pl.decimate_to(low, 200000)
        mod = low.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = u(0.35)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        pl.decimate_to(low, LOW_TRIS[0])
        for p in low.data.polygons:
            p.use_smooth = True
        while low.data.uv_layers:
            low.data.uv_layers.remove(low.data.uv_layers[0])
        low.data.uv_layers.new(name='UVMap')
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01, area_weight=0.0,
                                 scale_to_bounds=False)
        bpy.ops.uv.pack_islands(margin=0.01, rotate=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{animal}_low.blend'))
        print('PREP', animal, 'high tris', pl.triangles(high), 'pieces', pieces, 'low', pl.triangles(low),
              'size units (x, y, z)', np.round(size, 1).tolist())

    elif stage == 'bake':
        bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{animal}_low.blend'))
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
        scene.world = scene.world or bpy.data.worlds.new('World')
        scene.world.light_settings.distance = u(6.0)
        high, low = bpy.data.objects['high'], bpy.data.objects['low']
        for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission',
                     'visible_volume_scatter', 'visible_shadow'):
            setattr(low, attr, False)
        mat = bpy.data.materials.new('Bake'); mat.use_nodes = True
        low.data.materials.clear(); low.data.materials.append(mat)
        node = mat.node_tree.nodes.new('ShaderNodeTexImage'); mat.node_tree.nodes.active = node
        for o in bpy.data.objects:
            o.select_set(o in (high, low))
        bpy.context.view_layer.objects.active = low
        bake = scene.render.bake
        bake.use_selected_to_active = True; bake.cage_extrusion = u(0.6); bake.max_ray_distance = u(1.5)
        bake.margin = 6
        for name in ('normal', 'ao'):
            image = bpy.data.images.new(name, TEX, TEX); image.colorspace_settings.name = 'Non-Color'
            node.image = image
            if name == 'normal':
                scene.cycles.samples = 8; bake.normal_space = 'TANGENT'
                bpy.ops.object.bake(type='NORMAL')
            else:
                scene.cycles.samples = 128
                bpy.ops.object.bake(type='AO')
            image.filepath_raw = os.path.join(WORK, f'{animal}_{name}.png'); image.file_format = 'PNG'; image.save()
            print('BAKED', animal, name)

    elif stage == 'build':
        bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{animal}_low.blend'))
        bpy.data.objects.remove(bpy.data.objects['high'])
        low = bpy.data.objects['low']
        pl.TEX = TEXTURES
        gold = pl.material('StatuetteGold', animal)
        pl.TEX = os.path.join(PROPS, 'textures')
        # A plain gold for the far mound: the pedestal's own Gold material (shared, already in the GLB).
        with bpy.data.libraries.load(os.path.join(PROPS, 'work', 'pedestal.blend')) as (src, dst):
            dst.objects = ['Pedestal', 'Pedestal_LOD1', 'Pedestal_LOD2']
        pedestals = dst.objects
        for obj in pedestals:
            bpy.context.scene.collection.objects.link(obj)
        lods = []
        for level, target in enumerate(LOW_TRIS):
            figure = duplicate(low, f'figure{level}')
            figure.data.materials.clear(); figure.data.materials.append(gold)
            select(figure)
            if level == 2:
                mod = figure.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = u(1.2)
                bpy.ops.object.modifier_apply(modifier=mod.name)
                pedestal_gold = next(m for m in pedestals[0].data.materials if m.name.startswith('Gold'))
                figure.data.materials.clear(); figure.data.materials.append(pedestal_gold)
                figure.data.uv_layers.new(name='UVMap') if not figure.data.uv_layers else None
            pl.decimate_to(figure, target)
            for p in figure.data.polygons:
                p.use_smooth = True
            pl.white_colour(figure)
            print('FIGURE', level, pl.triangles(figure))
            pedestal = duplicate(pedestals[level], 'tmp')
            obj = pl.join(f'Statuette{animal.capitalize()}' + ('' if level == 0 else f'_LOD{level}'),
                          [pedestal, figure])
            lods.append(obj)
        for obj in pedestals:
            bpy.data.objects.remove(obj)
        bpy.data.objects.remove(low)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{animal}.blend'))
        pl.export(lods, os.path.join(WORK, f'{animal}_export.glb'))


if __name__ == '__main__':
    if '--' in sys.argv:
        animal, stage = sys.argv[sys.argv.index('--') + 1:][:2]
        blender_main(animal, stage)
    else:
        textures(sys.argv[1])
