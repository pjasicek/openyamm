"""Stage 3 (Blender): the Ancient-steel couch for one element, joined with the sleeping titan (work/body.blend),
materials attached, LODs 0-3 exported as work/<name>_raw.glb (link_static_model_lods.py then links the chain).

Couch (model metres = game units / 100; origin at its bottom centre; the open long side, the front, faces -Y =
glTF +Z; the head end is -X, on the left when looking at the front): a trim-metal base course, a hull-steel body
with chamfered corners, a deck slab (hull top, trim edge band) at sleeper.json couch.deck, four square corner posts
in trim metal, a raised hull headrest platform under the head, and glow windows (the element's core strip, emissive)
framed in trim on both long sides and both ends (emissive factor
sleeper.json elements.<element>.emission: below 1 so the bloom keeps the element's hue). Square-edged and flat-shaded; UVs world-scale box projection
(hull 2.56 m per tile = 1 texel per unit at x2, trim 1.28 m per tile), glow windows 0..1 across their height.
LOD0/1 carry the full couch, LOD2 drops the chamfers and frames, LOD3 also the posts.
Usage: blender -b --python build_export.py -- <element>"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
cfg = json.load(open(os.path.join(HERE, 'sleeper.json')))
element = sys.argv[sys.argv.index('--') + 1]
work = os.path.join(PROJECT, 'work')
tex = os.path.join(work, 'tex')
name = f'xeen_deco_sleeper_{element}'
C = cfg['couch']
L2, W2, DECK = C['length'] / 2, C['width'] / 2, C['deck']
HULL_TILE, TRIM_TILE = 2.56, 1.28
MATS = ['Hull', 'Trim', 'Glow']   # couch slots, appended after the body's one slot

bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'body.blend'))
scene = bpy.context.scene


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')

    def quad(self, pts, mat, uv=None):
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = mat
        f.normal_update()
        if uv is None:
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            tile = HULL_TILE if mat == 0 else TRIM_TILE
            for loop in f.loops:
                p = loop.vert.co
                if ax == 2:
                    u, v = p.x, p.y * (1 if n.z > 0 else -1)
                elif ax == 1:
                    u, v = p.x * (-1 if n.y > 0 else 1), p.z
                else:
                    u, v = p.y * (1 if n.x > 0 else -1), p.z
                loop[self.uv].uv = (u / tile, v / tile)
        else:
            for loop, t in zip(f.loops, uv):
                loop[self.uv].uv = t
        return f

    def prism(self, ring_lo, ring_hi, z0, z1, mat_side, mat_top, bottom=False, top=True):
        """A vertical prism between two equal-length rings (counter-clockwise seen from above) at z0 and z1."""
        n = len(ring_lo)
        for i in range(n):
            j = (i + 1) % n
            self.quad([(*ring_lo[i], z0), (*ring_lo[j], z0), (*ring_hi[j], z1), (*ring_hi[i], z1)], mat_side)
        if top:
            self.quad([(*p, z1) for p in ring_hi], mat_top)
        if bottom:
            self.quad([(*p, z0) for p in reversed(ring_lo)], mat_top)

    def box(self, x0, x1, y0, y1, z0, z1, mat_side, mat_top=None, chamfer=0.0, bottom=False, top=True):
        r = rect(x0, x1, y0, y1, chamfer)
        self.prism(r, r, z0, z1, mat_side, mat_side if mat_top is None else mat_top, bottom, top)

    def mesh(self, nm):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        me = bpy.data.meshes.new(nm)
        self.bm.to_mesh(me)
        self.bm.free()
        return me


def rect(x0, x1, y0, y1, c=0.0):
    if c <= 0:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c),
            (x0, y0 + c)]


def couch(level):
    """level 0: full; 2: no chamfers or window frames; 3: also no posts."""
    b = Builder()
    H, T, G = 0, 1, 2
    ch = 0.06 if level == 0 else 0.0
    body_top = DECK - 0.12
    # base course (trim), body (hull), deck slab (hull top, trim band)
    b.box(-L2 + 0.10, L2 - 0.10, -W2 + 0.10, W2 - 0.10, 0.0, 0.10, T, T, ch, top=False)
    b.box(-L2 + 0.08, L2 - 0.08, -W2 + 0.08, W2 - 0.08, 0.10, body_top, H, H, ch, top=False)
    b.box(-L2, L2, -W2, W2, body_top, DECK, T, H, ch * 0.5, bottom=True)
    # headrest platform at the head end (-X)
    hr = C['headrest']
    hx1, htop, hw = hr['x_end'], hr['top'], hr['half_width']
    b.box(-L2 + 0.06, hx1, -hw, hw, DECK, htop, H, H, 0.03 if level == 0 else 0.0)
    if level == 0:   # a trim band round the headrest's top edge
        b.box(hx1 - 0.0, hx1 + 0.02, -hw, hw, DECK, htop + 0.005, T, T)
    # corner posts
    if level < 3:
        ps = 0.11
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx, cy = sx * (L2 - ps + 0.02), sy * (W2 - ps + 0.02)
                b.box(cx - ps, cx + ps, cy - ps, cy + ps, 0.0, C['post_top'] - 0.04, T, T, 0.02 if level == 0 else 0.0,
                      top=False)
                # a pyramid cap
                r_lo = rect(cx - ps, cx + ps, cy - ps, cy + ps)
                r_hi = rect(cx - ps * 0.45, cx + ps * 0.45, cy - ps * 0.45, cy + ps * 0.45)
                b.prism(r_lo, r_hi, C['post_top'] - 0.04, C['post_top'], T, T)
    # glow windows: long sides (front -Y, back +Y) and both ends; the glow sits 3 cm behind a proud trim frame
    zw0, zw1 = 0.22, 0.48
    face_y = W2 - 0.08
    face_x = L2 - 0.08
    wins = [('y', -1, -2.45, 2.45), ('y', 1, -2.45, 2.45), ('x', -1, -0.95, 0.95), ('x', 1, -0.95, 0.95)]
    for axis, side, a0, a1 in wins:
        off = 0.004
        rep = (a1 - a0) / (zw1 - zw0) / 8.0      # the strip is 8:1
        def P(a, z, d):
            if axis == 'y':
                return (a, side * (face_y + d), z)
            return (side * (face_x + d), a, z)
        # outward-facing quad: order so the normal points to side
        pts = [P(a0, zw0, off), P(a1, zw0, off), P(a1, zw1, off), P(a0, zw1, off)]
        uvs = [(0, 0), (rep, 0), (rep, 1), (0, 1)]
        flip = (axis == 'y' and side > 0) or (axis == 'x' and side < 0)
        if flip:
            pts = pts[::-1]
            uvs = uvs[::-1]
        b.quad(pts, G, uvs)
        if level < 2:
            fw, fd = 0.05, 0.035     # frame bar width and how far it stands proud
            for (p0, p1, q0, q1) in ((a0 - fw, a1 + fw, zw0 - fw, zw0), (a0 - fw, a1 + fw, zw1, zw1 + fw),
                                     (a0 - fw, a0, zw0, zw1), (a1, a1 + fw, zw0, zw1)):
                if axis == 'y':
                    y_in, y_out = side * face_y, side * (face_y + fd)
                    b.box(p0, p1, min(y_in, y_out), max(y_in, y_out), q0, q1, T, T, bottom=True)
                else:
                    x_in, x_out = side * face_x, side * (face_x + fd)
                    b.box(min(x_in, x_out), max(x_in, x_out), p0, p1, q0, q1, T, T, bottom=True)
    me = b.mesh(f'couch{level}')
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    return me


def image(path, non_color):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


def pbr_material(nm, base, normal, mr, cull=True, emission=None, metal=None, rough=None, emission_strength=1.0):
    m = bpy.data.materials.new(nm)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = image(base, False)
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    if normal:
        tn = nt.nodes.new('ShaderNodeTexImage')
        tn.image = image(normal, True)
        nm_ = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tn.outputs['Color'], nm_.inputs['Color'])
        nt.links.new(nm_.outputs['Normal'], bsdf.inputs['Normal'])
    if mr:
        tm = nt.nodes.new('ShaderNodeTexImage')
        tm.image = image(mr, True)
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(tm.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
        nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
    if emission:
        te = nt.nodes.new('ShaderNodeTexImage')
        te.image = image(emission, False)
        nt.links.new(te.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    m.use_backface_culling = cull
    return m


def T(f):
    return os.path.join(tex, f)


mats = {
    'Hull': pbr_material(f'{name}_hull', T('hull_basecolor.png'), T('hull_normal.png'), T('hull_mr.png')),
    'Trim': pbr_material(f'{name}_trim', T(f'trim_{element}_basecolor.png'), T(f'trim_{element}_normal.png'),
                         T(f'trim_{element}_mr.png')),
    'Glow': pbr_material(f'{name}_glow', T(f'glow_{element}.png'), None, None, emission=T(f'glow_{element}.png'),
                         metal=0.0, rough=0.4, emission_strength=cfg['elements'][element]['emission']),
}
body_mats = {k: pbr_material(f'{name}_body{k}', T(f'body{k}_basecolor.png'), T(f'body{k}_normal.png'),
                             T(f'body{k}_mr.png'), cull=False) for k in ('0', '2', '3')}
# the titan's own source materials keep metallic factor 0 (its MR texture's blue is not metal)
for m in body_mats.values():
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for link in list(m.node_tree.links):
        if link.to_socket == bsdf.inputs['Metallic']:
            m.node_tree.links.remove(link)
    bsdf.inputs['Metallic'].default_value = 0.0

counts = []
objs = []
for lod in range(4):
    body = bpy.data.objects[f'Body_LOD{lod}']
    body.data.materials.clear()
    body.data.materials.append(body_mats['0' if lod < 2 else str(lod)])
    cm = couch(0 if lod < 2 else lod)
    cob = bpy.data.objects.new(f'couch{lod}', cm)
    scene.collection.objects.link(cob)
    for k in MATS:
        cm.materials.append(mats[k])
    # couch material indices 0..2 become 1..3 after the join (body slot first)
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    cob.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    nm = name if lod == 0 else f'{name}_LOD{lod}'
    body.name = nm
    body.data.name = nm
    for a in [a for a in body.data.attributes if a.name.startswith('Col') or a.name == 'part']:
        body.data.attributes.remove(a)
    while len(body.data.uv_layers) > 1:
        body.data.uv_layers.remove(body.data.uv_layers[-1])
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    counts.append(tris)
    objs.append(body)
co = [v.co for v in objs[0].data.vertices]
lo = [min(c[i] for c in co) for i in range(3)]
hi = [max(c[i] for c in co) for i in range(3)]
print('LOD_TRIANGLES', counts)
print('BOUNDS', [round(x * 100, 1) for x in lo], [round(x * 100, 1) for x in hi])
for o in list(scene.objects):
    o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
out = os.path.join(work, f'{name}_raw.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_extras=True, export_normals=True, export_tangents=False, export_animations=False,
                          export_skins=False, export_morph=False, export_image_format='AUTO', export_apply=True,
                          export_vertex_color='NONE')
json.dump({'lod_triangles': counts, 'bounds_units': [[x * 100 for x in lo], [x * 100 for x in hi]]},
          open(os.path.join(work, f'{element}_lods.json'), 'w'), indent=1)
print('EXPORTED', out)
