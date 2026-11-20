"""Bake the 20k Meshy hydra onto the reduced mesh. Meshy's own UV atlas is fragmented,
so collapsing it in place smears the texture at seams; instead the reduced mesh gets a fresh unwrap (or keeps the
atlas UVs of uv_atlas.py when it has them) and receives base
colour, roughness and a tangent-space normal (Meshy's detail normal plus the shape the reduction removed) from the
high mesh by Cycles selected-to-active bakes.
Run on work/hd_source.blend (the uncut textured 20k hydra 'Hydra'):
  blender --background work/hd_source.blend --python scripts/bake_reduced.py -- <reduced.blend> [size]
The tail-cut cap (remove_tail.py) lies inside the uncut source's old tail root, so its rays miss; texels the source
bake leaves unwritten (alpha 0) are filled by a second bake from the capped work/hd_base.blend.
Writes textures/body_base_color.png, body_roughness.png, body_normal.png (size, default 2048) and
work/hd_reduced.blend (object 'Hydra', the reduced mesh with the baked material)."""
import bpy, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
args = sys.argv[sys.argv.index('--') + 1:]
REDUCED, SIZE = args[0], int(args[1]) if len(args) > 1 else 2048

high = bpy.data.objects['Hydra']; high.name = 'HydraHigh'
with bpy.data.libraries.load(REDUCED) as (src, dst):
    dst.objects = ['Hydra']
low = dst.objects[0]; bpy.context.scene.collection.objects.link(low)
low.data = low.data.copy()
if 'Upload' in low.data.uv_layers:
    # atlas UVs from uv_atlas.py: bake straight into the atlas layout ('UVMap'), keep the upload layer
    low.data.uv_layers.active = low.data.uv_layers['UVMap']
else:
    for layer in list(low.data.uv_layers):
        low.data.uv_layers.remove(layer)
    low.data.uv_layers.new(name='UVMap')
    for o in bpy.context.view_layer.objects:
        o.select_set(o is low)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    # 89 deg islands: the spiky serpent fragments into thousands of tiny islands at 45 deg (12% coverage); 89 deg
    # packs 30% with 0.2% overlap (seam unwraps gave 13%).
    bpy.ops.uv.smart_project(angle_limit=1.55, island_margin=0.002, area_weight=0.0)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(shape_method='CONCAVE', rotate=True, margin=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')

mat = bpy.data.materials.new('HydraBaked'); mat.use_nodes = True; nt = mat.node_tree
low.data.materials.clear(); low.data.materials.append(mat)
images = {}
for name, colorspace in (('base_color', 'sRGB'), ('roughness', 'Non-Color'), ('normal', 'Non-Color')):
    for tag in ('', '_cap'):
        img = bpy.data.images.new(f'body_{name}{tag}', SIZE, SIZE, alpha=True, float_buffer=False)
        img.colorspace_settings.name = colorspace; img.generated_color = (0, 0, 0, 0)
        images[name + tag] = img
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'hd_base.blend')) as (src, dst):
    dst.objects = ['Hydra']
capped = dst.objects[0]; bpy.context.scene.collection.objects.link(capped)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'
bake = sc.render.bake
bake.use_selected_to_active = True; bake.cage_extrusion = 0.012; bake.max_ray_distance = 0.06; bake.margin = 8
missed = None
for source, tag in ((high, ''), (capped, '_cap')):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in (source, low))
    bpy.context.view_layer.objects.active = low
    for name, bake_type in (('base_color', 'DIFFUSE'), ('roughness', 'ROUGHNESS'), ('normal', 'NORMAL')):
        node = nt.nodes.new('ShaderNodeTexImage'); node.image = images[name + tag]
        nt.nodes.active = node
        if bake_type == 'DIFFUSE':
            bake.use_pass_direct = False; bake.use_pass_indirect = False; bake.use_pass_color = True
        bpy.ops.object.bake(type=bake_type)
        nt.nodes.remove(node)
        print('BAKED', name + tag, flush=True)
for name in ('base_color', 'roughness', 'normal'):
    a = np.empty(SIZE * SIZE * 4, np.float32); images[name].pixels.foreach_get(a); a = a.reshape(-1, 4)
    b = np.empty(SIZE * SIZE * 4, np.float32); images[name + '_cap'].pixels.foreach_get(b); b = b.reshape(-1, 4)
    miss = a[:, 3] < 0.5
    if name == 'base_color':
        # texels neither bake reached (thin horn tips): compose_hyd.py fills them from the nearest baked texel
        both = (miss & (b[:, 3] < 0.5)).reshape(SIZE, SIZE)[::-1]
        np.save(os.path.join(HERE, 'work', 'bake_miss.npy'), both)
    a[miss] = b[miss]; a[:, 3] = 1.0
    images[name].pixels.foreach_set(a.ravel())
    images[name].filepath_raw = os.path.join(T, f'body_{name}.png'); images[name].file_format = 'PNG'
    images[name].save()
    print('FILLED', name, int((miss & (b[:, 3] > 0.5)).sum()), 'texels from the capped mesh', flush=True)

bpy.data.objects.remove(capped, do_unlink=True)
bpy.data.objects.remove(high, do_unlink=True)
low.name = low.data.name = 'Hydra'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hd_reduced.blend'))
print('SAVED hd_reduced.blend triangles', sum(len(p.vertices) - 2 for p in low.data.polygons))
