"""Stage 2 (Blender): LOD0 = the Low collection of work/<id>/high.blend joined (face attribute part from each piece),
atlas UVs (claude_shared/uv_atlas.py), a tangent normal baked from the High collection, and base colour, metallic-
roughness and (optionally) emission evaluated on the LOD0 itself from the parts' stone recipes (scripts/stones.json:
box-projected grain through a colour ramp, veins, weathering, AO and cavity, crevice and top-face tints, an emblem
mask on top faces). Writes work/<id>/low.blend, bake_color.png (sRGB), bake_normal.png, bake_mr.png
(R 1, G roughness, B metallic), bake_emit.png when a recipe emits, and uv.npz for gutter_fill.
Usage: blender -b --python lowbake.py -- <config.json> <id>"""
import json
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
import uv_atlas  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(os.path.join(HERE, argv[0])))[argv[1]]
STONES = json.load(open(os.path.join(HERE, 'stones.json')))
work = os.path.join(PROJECT, 'work', argv[1])
TEX = os.path.join(REPO, 'assets_source', 'worlds')
RECOLOUR = len(argv) > 2 and argv[2] == 'recolour'
bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'low.blend' if RECOLOUR else 'high.blend'))
scene = bpy.context.scene
size = cfg.get('tex_size', 2048)
recipes = {int(k): v for k, v in cfg['recipes'].items()}
if RECOLOUR:
    highs = []
    low = bpy.data.objects['LOD0']
    me = low.data
    mat = me.materials[0]
    target = mat.node_tree.nodes.active
else:
    highs = list(bpy.data.collections['High'].objects)
    lows = list(bpy.data.collections['Low'].objects)

def image(name, sz, non_color):
    img = bpy.data.images.new(name, sz, sz, alpha=False, float_buffer=False)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


def bake(kind, img, path, node=None):
    (node or target).image = img
    bpy.ops.object.bake(type=kind)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    print('BAKED', kind, path)


VIS = ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
       'visible_shadow')
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32

if not RECOLOUR:
    bm = bmesh.new()
    part = bm.faces.layers.float.new('part')
    for o in lows:
        before = len(bm.faces)
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[before:]:
            f[part] = float(o['part'])
    for lay in list(bm.verts.layers.deform.values()):
        bm.verts.layers.deform.remove(lay)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY')
    for f in bm.faces:
        f.material_index = 0
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    me = bpy.data.meshes.new('LOD0')
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=cfg.get('sharp_angle', 1.047198))
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name='UVMap')
    for a in [a for a in me.attributes if a.domain == 'CORNER' and a.data_type == 'BYTE_COLOR']:
        me.attributes.remove(a)
    for o in lows:
        bpy.data.objects.remove(o, do_unlink=True)
    low = bpy.data.objects.new('LOD0', me)
    scene.collection.objects.link(low)
    ntri = len(me.polygons)
    print('LOD0 triangles', ntri)
    parts = np.zeros(ntri, np.float32)
    me.attributes['part'].data.foreach_get('value', parts)
    fig_parts = set(cfg.get('dense_parts', [0, 2]))
    g_fig = low.vertex_groups.new(name='Figure')
    g_base = low.vertex_groups.new(name='Base')
    for p, poly in zip(parts, me.polygons):
        (g_fig if int(p) in fig_parts else g_base).add(list(poly.vertices), 1.0, 'REPLACE')
    report = uv_atlas.unwrap(low, head_groups=('Figure',), head_factor=cfg.get('head_factor', 1.5), margin_px=4,
                             size=size, sparrow_seconds=cfg.get('sparrow_seconds', 20), sparrow_runs=cfg.get('sparrow_runs', 3))
    print('UV charts', report.get('charts_used'), 'packer', report.get('packer_used'), 'fallbacks', report.get('fallbacks'))
    print('UV report', {k: report[k] for k in report if k in ('atlas', 'islands', 'stretch_p90', 'density_spread')})
    low.vertex_groups.clear()

    mat = bpy.data.materials.new('Target')
    mat.use_nodes = True
    target = mat.node_tree.nodes.new('ShaderNodeTexImage')
    mat.node_tree.nodes.active = target
    me.materials.clear()
    me.materials.append(mat)


    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = cfg.get('cage', 0.06)
    scene.render.bake.max_ray_distance = cfg.get('ray', 0.18)
    scene.render.bake.margin = 0
    scene.render.bake.margin_type = 'EXTEND'
    VIS = ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter',
           'visible_shadow')
    for o in scene.objects:
        o.select_set(o in highs)
    low.select_set(True)
    for attr in VIS:
        setattr(low, attr, False)
    bpy.context.view_layer.objects.active = low


    if cfg.get('bake_normal', True):
        bake('NORMAL', image('bake_normal', size, True), os.path.join(work, 'bake_normal.png'))
    else:
        img = image('bake_normal', size, True)
        img.generated_color = (0.5, 0.5, 1.0, 1.0)
        img.filepath_raw = os.path.join(work, 'bake_normal.png')
        img.file_format = 'PNG'
        img.save()


# ------------------------------------------------------------------------------------- the stone shader
_RANGES = {}


def lum_range(rel):
    """The texture's linear luminance p3 / p97 (the grain is stretched to 0-1 between them)."""
    if rel not in _RANGES:
        img = bpy.data.images.load(os.path.join(TEX, rel), check_existing=True)
        px = np.array(img.pixels[:], np.float32).reshape(-1, 4)[:, :3]
        lin = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
        lum = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        _RANGES[rel] = (float(np.percentile(lum, 3)), float(np.percentile(lum, 97)))
        print('GRAIN', rel, _RANGES[rel])
    return _RANGES[rel]


class G:
    def __init__(self, nt):
        self.nt, self.N, self.L = nt, nt.nodes, nt.links
        self.tc = self.N.new('ShaderNodeTexCoord')
        self.geo = self.N.new('ShaderNodeNewGeometry')
        sep = self.N.new('ShaderNodeSeparateXYZ')
        self.L.new(self.geo.outputs['Normal'], sep.inputs[0])
        self.nz = sep.outputs['Z']
        pos = self.N.new('ShaderNodeSeparateXYZ')
        self.L.new(self.tc.outputs['Object'], pos.inputs[0])
        self.px, self.py, self.pz = pos.outputs['X'], pos.outputs['Y'], pos.outputs['Z']
        self.ao_big = self.N.new('ShaderNodeAmbientOcclusion')
        self.ao_big.inputs['Distance'].default_value = cfg.get('ao_big', 0.6)
        self.ao_big.samples = 16
        self.ao_small = self.N.new('ShaderNodeAmbientOcclusion')
        self.ao_small.inputs['Distance'].default_value = cfg.get('ao_small', 0.08)
        self.ao_small.samples = 16
        self.crev = self.math('SUBTRACT', 1.0, self.ao_small.outputs['AO'], clamp=True)
        top = self.N.new('ShaderNodeMapRange')
        top.inputs['From Min'].default_value = 0.5
        top.inputs['From Max'].default_value = 0.92
        self.L.new(self.nz, top.inputs['Value'])
        self.top = top.outputs[0]
        self.noise = self.N.new('ShaderNodeTexNoise')
        self.noise.inputs['Scale'].default_value = 0.35
        self.noise.inputs['Detail'].default_value = 4.0
        self.L.new(self.tc.outputs['Object'], self.noise.inputs['Vector'])

    def math(self, op, a, b=None, clamp=False):
        n = self.N.new('ShaderNodeMath')
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                self.L.new(v, n.inputs[i])
        return n.outputs[0]

    def mix(self, fac, a, b, blend='MIX'):
        n = self.N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        n.blend_type = blend
        for sock, v in (('Factor', fac), ('A', a), ('B', b)):
            if isinstance(v, (int, float)):
                n.inputs[sock].default_value = v
            elif isinstance(v, (list, tuple)):
                n.inputs[sock].default_value = (*v[:3], 1.0)
            else:
                self.L.new(v, n.inputs[sock])
        return n.outputs['Result']

    def maprange(self, v, lo, hi):
        n = self.N.new('ShaderNodeMapRange')
        n.inputs['From Min'].default_value = lo
        n.inputs['From Max'].default_value = hi
        self.L.new(v, n.inputs['Value'])
        return n.outputs[0]

    def tex(self, rel, scale, colour=False):
        mp = self.N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale, scale, scale * 0.6)
        self.L.new(self.tc.outputs['Object'], mp.inputs['Vector'])
        tx = self.N.new('ShaderNodeTexImage')
        tx.image = bpy.data.images.load(os.path.join(TEX, rel), check_existing=True)
        tx.projection = 'BOX'
        tx.projection_blend = 0.35
        self.L.new(mp.outputs[0], tx.inputs['Vector'])
        if colour:
            return tx.outputs['Color']
        bw = self.N.new('ShaderNodeRGBToBW')
        self.L.new(tx.outputs['Color'], bw.inputs[0])
        return bw.outputs[0]

    def grain(self, gc, colour=False):
        out = None
        for s, w in zip(gc['scales'], gc['weights']):
            t = self.tex(gc['tex'], s, colour)
            if colour:
                v = self.mix(w, (0, 0, 0), t) if out is None else self.mix(w / (1.0), out, t, 'ADD')
                term = self.N.new('ShaderNodeVectorMath')
                term.operation = 'SCALE'
                self.L.new(t, term.inputs[0])
                term.inputs['Scale'].default_value = w
                if out is None:
                    out = term.outputs[0]
                else:
                    add = self.N.new('ShaderNodeVectorMath')
                    add.operation = 'ADD'
                    self.L.new(out, add.inputs[0])
                    self.L.new(term.outputs[0], add.inputs[1])
                    out = add.outputs[0]
            else:
                term = self.math('MULTIPLY', t, w)
                out = term if out is None else self.math('ADD', out, term)
        if not colour and gc.get('normalise', True):
            lo, hi = lum_range(gc['tex'])
            out = self.maprange(out, lo, hi)
        return out

    def emblem_mask(self, em):
        """1 inside the emblem's carved shape on top faces near the emblem's height."""
        mp = self.N.new('ShaderNodeMapping')
        mp.vector_type = 'POINT'
        s = 1.0 / em['size']
        mp.inputs['Scale'].default_value = (s, s, 1.0)
        mp.inputs['Location'].default_value = (0.5 - em['centre'][0] * s, 0.5 - em['centre'][1] * s, 0)
        self.L.new(self.tc.outputs['Object'], mp.inputs['Vector'])
        tx = self.N.new('ShaderNodeTexImage')
        tx.image = bpy.data.images.load(os.path.join(work, em['image']), check_existing=True)
        tx.image.colorspace_settings.name = 'Non-Color'
        tx.extension = 'CLIP'
        self.L.new(mp.outputs[0], tx.inputs['Vector'])
        bw = self.N.new('ShaderNodeRGBToBW')
        self.L.new(tx.outputs['Color'], bw.inputs[0])
        upf = self.maprange(self.nz, 0.6, 0.85)
        zf = self.maprange(self.pz, em['z_min'], em['z_min'] + 0.01)
        return self.math('MULTIPLY', self.math('MULTIPLY', bw.outputs[0], upf), zf)

    def colour(self, r):
        if 'direct' in r:
            base = self.grain(r['direct'], colour=True)
            sc = self.N.new('ShaderNodeVectorMath')
            sc.operation = 'SCALE'
            self.L.new(base, sc.inputs[0])
            sc.inputs['Scale'].default_value = r['direct'].get('gain', 1.0)
            col = sc.outputs[0]
        else:
            g = self.grain(r['grain'])
            ramp = self.N.new('ShaderNodeValToRGB')
            cr = ramp.color_ramp
            stops = r['ramp']
            cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
            cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
            for pos, c in stops[1:-1]:
                e = cr.elements.new(pos)
                e.color = (*c, 1)
            self.L.new(g, ramp.inputs['Fac'])
            col = ramp.outputs['Color']
        if 'veins' in r:
            v = r['veins']
            vm = self.maprange(self.tex(v['tex'], v['scale']), v['lo'], v['hi'])
            col = self.mix(self.math('MULTIPLY', vm, v['amount']), col, v['colour'])
        if 'weather' in r:
            w = r['weather']
            wf = self.math('MULTIPLY', self.maprange(self.noise.outputs['Fac'], 0.42, 0.68), w['amount'])
            tint = self.N.new('ShaderNodeCombineXYZ')
            for c, k in zip('XYZ', w['tint']):
                self.L.new(self.math('ADD', 1.0, self.math('MULTIPLY', wf, k)), tint.inputs[c])
            wm = self.N.new('ShaderNodeVectorMath')
            wm.operation = 'MULTIPLY'
            self.L.new(col, wm.inputs[0])
            self.L.new(tint.outputs[0], wm.inputs[1])
            col = wm.outputs[0]
        if 'verdigris' in r:
            vg = r['verdigris']
            nz = self.N.new('ShaderNodeTexNoise')
            nz.inputs['Scale'].default_value = vg['noise']
            nz.inputs['Detail'].default_value = 6.0
            self.L.new(self.tc.outputs['Object'], nz.inputs['Vector'])
            patch = self.maprange(nz.outputs['Fac'], vg['lo'], vg['hi'])
            amt = self.math('ADD', patch, self.math('ADD', self.math('MULTIPLY', self.crev, vg['crevice'] * 3.0),
                                                     self.math('MULTIPLY', self.top, vg['top'])), clamp=True)
            green = self.mix(self.tex(r['grain']['tex'], 2.5), vg['dark'], vg['colour'])
            col = self.mix(amt, col, green)
            self.verdigris = amt
        a0, a1 = r.get('ao', [0.62, 0.5])
        occl = self.math('MULTIPLY', self.math('ADD', 1 - a0, self.math('MULTIPLY', self.ao_big.outputs['AO'], a0)),
                         self.math('ADD', 1 - a1, self.math('MULTIPLY', self.ao_small.outputs['AO'], a1)))
        sh = self.N.new('ShaderNodeVectorMath')
        sh.operation = 'SCALE'
        self.L.new(col, sh.inputs[0])
        self.L.new(occl, sh.inputs['Scale'])
        col = sh.outputs[0]
        if 'crevice' in r:
            c = r['crevice']
            col = self.mix(self.math('MULTIPLY', self.maprange(self.crev, c['lo'], c['hi']), c['amount']), col,
                           c['colour'])
        if 'top' in r:
            t = r['top']
            col = self.mix(self.math('MULTIPLY', self.math('MULTIPLY', self.top, self.noise.outputs['Fac']),
                                     t['amount']), col, t['colour'])
        if cfg.get('emblem'):
            em = cfg['emblem']
            col = self.mix(self.math('MULTIPLY', self.emblem_mask(em), em.get('amount', 1.0)), col,
                           r.get('emblem_colour', em.get('colour', [0.02, 0.02, 0.02])))
        f = r.get('floor', 0.0135)
        return self.mix(1.0, col, (f, f, f), 'LIGHTEN')

    def mr(self, r):
        base, gvar, topadd, crevadd = r['rough']
        g = self.grain(r['grain'] if 'grain' in r else r['direct'])
        rough = self.math('ADD', base, self.math('MULTIPLY', self.math('SUBTRACT', g, 0.35), gvar))
        rough = self.math('ADD', rough, self.math('MULTIPLY', self.top, topadd))
        rough = self.math('ADD', rough, self.math('MULTIPLY', self.crev, crevadd), clamp=True)
        metal = r.get('metal', 0.0)
        if 'verdigris' in r:
            self.colour(r)
            metal = self.math('SUBTRACT', 1.0, self.verdigris, clamp=True)
            rough = self.math('ADD', rough, self.math('MULTIPLY', self.verdigris, 0.4), clamp=True)
        comb = self.N.new('ShaderNodeCombineXYZ')
        comb.inputs['X'].default_value = 1.0
        self.L.new(rough, comb.inputs['Y'])
        if isinstance(metal, float):
            comb.inputs['Z'].default_value = metal
        else:
            self.L.new(metal, comb.inputs['Z'])
        return comb.outputs[0]

    def emit(self, r):
        e = r.get('emission')
        if not e:
            return None
        if e.get('from_red'):
            c = self.grain(r['direct'], colour=True)
            sep = self.N.new('ShaderNodeSeparateColor')
            self.L.new(c, sep.inputs[0])
            m = self.maprange(self.math('SUBTRACT', sep.outputs['Red'], sep.outputs['Green']), 0.12, 0.45)
        else:
            m = self.maprange(self.crev, r['crevice']['lo'] + 0.08, r['crevice']['hi'] + 0.1)
        m = self.math('MULTIPLY', m, e['strength'])
        return self.mix(m, (0, 0, 0), e['colour'])


def stone_material(kind):
    m = bpy.data.materials.new('Bake_' + kind)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(emit.outputs[0], out.inputs['Surface'])
    g = G(nt)
    attr = nt.nodes.new('ShaderNodeAttribute')
    attr.attribute_type = 'GEOMETRY'
    attr.attribute_name = 'part'
    result = None
    for k in sorted(recipes):
        r = STONES[recipes[k]]
        s = {'color': g.colour, 'mr': g.mr, 'emit': g.emit}[kind](r)
        if s is None:
            s = g.mix(1.0, (0, 0, 0), (0, 0, 0))
        if result is None:
            result = s
        else:
            sel = g.math('COMPARE', attr.outputs['Fac'], float(k))
            nt.nodes[-1].inputs[2].default_value = 0.5
            result = g.mix(sel, result, s)
    nt.links.new(result, emit.inputs['Color'])
    return m


scene.render.bake.use_selected_to_active = False
scene.render.bake.margin = 16
for o in highs:
    o.hide_render = True
    o.select_set(False)
for attr in VIS:
    setattr(low, attr, True)
jobs = [('color', 'bake_color.png', size, False), ('mr', 'bake_mr.png', size // 2, True)]
if any(STONES[v].get('emission') for v in recipes.values()):
    jobs.append(('emit', 'bake_emit.png', size // 2, False))
for kind, path, sz, nc in jobs:
    sm = stone_material(kind)
    node = sm.node_tree.nodes.new('ShaderNodeTexImage')
    sm.node_tree.nodes.active = node
    me.materials[0] = sm
    bake('EMIT', image('bake_' + kind, sz, nc), os.path.join(work, path), node)
me.materials[0] = mat

uv = np.zeros((len(me.loops), 2), np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', uv.ravel())
tri_uv = np.array([[uv[li] for li in p.loop_indices] for p in me.polygons], np.float32)
tri_uv[..., 1] = 1.0 - tri_uv[..., 1]
np.savez(os.path.join(work, 'uv.npz'), uv=tri_uv)
target.image = None
for o in highs:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'low.blend'))
print('LOWBAKE_DONE')
