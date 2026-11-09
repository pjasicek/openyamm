"""Bake the grafted hydra's two texture sets (Cycles, selected-to-active) on work/hd_atlas.blend (uv_atlas.py output):
  body texture (2048x2048, faces of part 0): from the uncut 20k Meshy model (work/hd_source.blend); texels its rays
    miss come from the capped work/hd_base.blend (the cut tail root),
  head texture (1536x1024, faces of part k): from the high-res retextured heads mapped into place by graft_heads.py
    (work/heads_hi.blend, HeadHi1..5; their 2K Meshy base colour, roughness and normal maps).
Maps per set: base colour, roughness, tangent-space normal (detail and the shape the reduction removed) and ambient
occlusion of the whole low mesh (both parts occlude each other). Texels no bake reached keep alpha 0 and are recorded
in work/bake_miss_<set>.npy; compose_hyd.py --assemble fills them from the nearest baked texel.
  blender --background work/hd_atlas.blend --python scripts/bake_hydra.py
Writes textures/body_{base_color,roughness,normal,ao}.png and textures/head_{...}.png."""
import bpy, bmesh, os
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
SETS = {'body': (2048, 2048), 'head': (1536, 1024)}
AO_REACH = 0.04
HEAD_CAGE, HEAD_RAY = 0.008, 0.04   # thin fins and crests need the tight cage (0.018 washed them out); the wide pass only
                                    # fills the texels this one misses

src = bpy.data.objects['Hydra']
for m in list(src.modifiers):
    src.modifiers.remove(m)
part = np.zeros(len(src.data.polygons), int); src.data.attributes['part'].data.foreach_get('value', part)


def split(name, keep):
    me = src.data.copy(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(part[f.index])], context='FACES')
    bm.to_mesh(me); bm.free(); me.materials.clear()
    return o


low = {'body': split('BodyLow', lambda k: k == 0), 'head': split('HeadLow', lambda k: k > 0)}
# each head baked on its own against its own high-res head (all five as sources let rays hit a neighbour), in two
# passes: tight, then wide for the texels the tight pass missed (decimated jaw fringes left 5-9 % unbaked, padded into
# triangle-shaped patches: the purple head's 'stitched' chin, user check 2026-10-09)
for k in range(1, 6):
    low[f'head{k}'] = split(f'HeadLow{k}', lambda p_, k=k: p_ == k)
src.hide_render = True; src.hide_set(True)


def link(path, names):
    with bpy.data.libraries.load(path) as (s, d):
        d.objects = names
    for o in d.objects:
        bpy.context.scene.collection.objects.link(o)
    return d.objects


high_body, capped = link(os.path.join(HERE, 'work', 'hd_source.blend'), ['Hydra'])[0], \
    link(os.path.join(HERE, 'work', 'hd_base.blend'), ['Hydra'])[0]
high_heads = link(os.path.join(HERE, 'work', 'heads_hi.blend'), [f'HeadHi{k}' for k in range(1, 6)])
images = {}
for name, (w, h) in SETS.items():
    mat = bpy.data.materials.new(f'{name}_bake'); mat.use_nodes = True
    low[name].data.materials.append(mat)
    if name == 'head':
        for k in range(1, 6):
            low[f'head{k}'].data.materials.append(mat)
    for kind, cs in (('base_color', 'sRGB'), ('roughness', 'Non-Color'), ('normal', 'Non-Color'), ('ao', 'Non-Color')):
        tags = ('', '_fill') + (tuple(f'_{k}{t}' for k in range(1, 6) for t in ('', '_fill')) if name == 'head' and kind != 'ao' else ())
        for tag in tags:
            img = bpy.data.images.new(f'{name}_{kind}{tag}', w, h, alpha=True, float_buffer=False)
            img.colorspace_settings.name = cs; img.generated_color = (0, 0, 0, 0)
            images[f'{name}_{kind}{tag}'] = img

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.device = 'CPU'
bake = sc.render.bake; bake.margin = 0


def run(target, sources, kind, tag='', cage=0.012, ray=0.06, image=None):
    mat = low[target].data.materials[0]; nt = mat.node_tree
    node = nt.nodes.new('ShaderNodeTexImage'); node.image = images[image or f'{target}_{kind}{tag}']; nt.nodes.active = node
    for o in bpy.context.view_layer.objects:
        o.select_set(o in sources or o is low[target])
    bpy.context.view_layer.objects.active = low[target]
    if kind == 'ao':
        bake.use_selected_to_active = False
        sc.world = sc.world or bpy.data.worlds.new('w')
        sc.world.light_settings.distance = AO_REACH
        bpy.ops.object.bake(type='AO')
    else:
        bake.use_selected_to_active = True; bake.cage_extrusion = cage; bake.max_ray_distance = ray
        if kind == 'base_color':
            bake.use_pass_direct = False; bake.use_pass_indirect = False; bake.use_pass_color = True
        bpy.ops.object.bake(type={'base_color': 'DIFFUSE', 'roughness': 'ROUGHNESS', 'normal': 'NORMAL'}[kind])
    nt.nodes.remove(node)
    print('BAKED', target, kind + tag, flush=True)


for kind in ('base_color', 'roughness', 'normal'):
    run('body', [high_body], kind)
    run('body', [capped], kind, '_fill')
    for k, hi in enumerate(high_heads, 1):
        run(f'head{k}', [hi], kind, cage=HEAD_CAGE, ray=HEAD_RAY, image=f'head_{kind}_{k}')
        run(f'head{k}', [hi], kind, cage=0.03, ray=0.12, image=f'head_{kind}_{k}_fill')
# AO: the low mesh only (both parts), sources hidden
for o in [high_body, capped] + high_heads:
    o.hide_render = True
for n, o in low.items():
    o.hide_render = n.startswith('head') and n != 'head'
run('body', [], 'ao'); run('head', [], 'ao')


def pixels(img):
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


for name in SETS:
    miss = None
    for kind in ('base_color', 'roughness', 'normal', 'ao'):
        a = pixels(images[f'{name}_{kind}'])
        if name == 'head' and kind != 'ao':
            # merge: each head's tight bake, then its wide bake where the tight one missed
            fill = np.zeros_like(a)
            for k in range(1, 6):
                t_ = pixels(images[f'head_{kind}_{k}']); w_ = pixels(images[f'head_{kind}_{k}_fill'])
                m = (a[..., 3] < 0.5) & (t_[..., 3] > 0.5); a[m] = t_[m]
                m = (fill[..., 3] < 0.5) & (w_[..., 3] > 0.5); fill[m] = w_[m]
            images[f'head_{kind}_fill'].pixels.foreach_set(fill.ravel())
        if kind != 'ao':
            b = pixels(images[f'{name}_{kind}_fill'])
            m = a[..., 3] < 0.5; a[m] = b[m]
        if kind == 'base_color':
            miss = a[..., 3] < 0.5
        a[..., 3] = 1.0
        img = images[f'{name}_{kind}']; img.pixels.foreach_set(a.ravel())
        img.filepath_raw = os.path.join(T, f'{name}_{kind}.png'); img.file_format = 'PNG'; img.save()
    np.save(os.path.join(HERE, 'work', f'bake_miss_{name}.npy'), miss[::-1])
    print('SAVED', name, 'unbaked texels', int(miss.sum()), 'of', miss.size)
