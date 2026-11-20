"""Bake the 20k Meshy body onto the reduced body. Meshy's own UV atlas is fragmented (72% of vertices lie on a seam),
so collapsing it in place smears the texture at seams; instead the reduced mesh gets a fresh unwrap and receives base
colour, roughness and a tangent-space normal (Meshy's detail normal plus the shape the reduction removed) from the
high mesh by Cycles selected-to-active bakes.
Run on work/hd_base.blend (the textured 20k body 'Demon'):
  blender --background work/hd_base.blend --python scripts/bake_reduced.py -- <reduced.blend> [size]
Writes textures/body_base_color.png, body_roughness.png, body_normal.png (size, default 2048) and
work/hd_reduced.blend (object 'Demon', the reduced mesh with the baked material)."""
import bpy, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
args = sys.argv[sys.argv.index('--') + 1:]
REDUCED, SIZE = args[0], int(args[1]) if len(args) > 1 else 2048

high = bpy.data.objects['Demon']; high.name = 'DemonHigh'
with bpy.data.libraries.load(REDUCED) as (src, dst):
    dst.objects = ['Demon']
low = dst.objects[0]; bpy.context.scene.collection.objects.link(low)
low.data = low.data.copy()
for layer in list(low.data.uv_layers):
    low.data.uv_layers.remove(layer)
low.data.uv_layers.new(name='UVMap')
for o in bpy.context.view_layer.objects:
    o.select_set(o is low)
bpy.context.view_layer.objects.active = low
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
# Large islands (89 deg) packed by shape: about 42% texture coverage, close to Meshy's own atlas (51%, 44% after
# collapsing), with no flipped or overlapping triangles.
bpy.ops.uv.smart_project(angle_limit=1.55, island_margin=0.002, area_weight=0.0)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(shape_method='CONCAVE', rotate=True, margin=0.002)
bpy.ops.object.mode_set(mode='OBJECT')

mat = bpy.data.materials.new('DemonBaked'); mat.use_nodes = True; nt = mat.node_tree
low.data.materials.clear(); low.data.materials.append(mat)
images = {}
for name, colorspace in (('base_color', 'sRGB'), ('roughness', 'Non-Color'), ('normal', 'Non-Color')):
    img = bpy.data.images.new(f'body_{name}', SIZE, SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    images[name] = img

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'
bake = sc.render.bake
bake.use_selected_to_active = True; bake.cage_extrusion = 0.004; bake.max_ray_distance = 0.02; bake.margin = 8
for o in bpy.context.view_layer.objects:
    o.select_set(o in (high, low))
bpy.context.view_layer.objects.active = low
for name, bake_type in (('base_color', 'DIFFUSE'), ('roughness', 'ROUGHNESS'), ('normal', 'NORMAL')):
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = images[name]
    nt.nodes.active = node
    if bake_type == 'DIFFUSE':
        bake.use_pass_direct = False; bake.use_pass_indirect = False; bake.use_pass_color = True
    bpy.ops.object.bake(type=bake_type)
    images[name].filepath_raw = os.path.join(T, f'body_{name}.png'); images[name].file_format = 'PNG'
    images[name].save()
    nt.nodes.remove(node)
    print('BAKED', name, flush=True)

bpy.data.objects.remove(high, do_unlink=True)
low.name = low.data.name = 'Demon'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hd_reduced.blend'))
print('SAVED hd_reduced.blend triangles', sum(len(p.vertices) - 2 for p in low.data.polygons))
