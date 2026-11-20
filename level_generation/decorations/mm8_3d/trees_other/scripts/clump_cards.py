"""LOD2 clump cards, step 1 of 3 (renders): work/<id>/tree.blend + clumps.json -> clump<v>_<view>_<pass>.png.
Step 2 make_clump_atlas.py packs the atlas, step 3 clump_lod2.py replaces Tree_LOD2's leaves. Usage: -- <id>

400 whorl cards at <=1.6x cannot keep the crown's coverage at LOD2, so each clump becomes four cards that show a
pre-rendered LOD0 clump at the same leaf scale: three vertical cards 60 degrees apart (side view) and one horizontal
card (top view), so the clump's baked lit top stays up. Atlas cells (512 px): row 0 = side views of two
representative outer clumps, row 1 = their top views. Each cell is a Cycles emission render of the clump's cards:
albedo = leaf texel x the clump-local term only (lit top, shaded underside and core); normal = the cards' shading
normals in camera space (R right, G up, B toward the viewer = the card's tangent space). The crown-level sky occlusion
goes into each card's COLOR_0 (the clump's mean, x its tint x TONE[2]), as on the other levels.
Material LeavesFar: MASK 0.5, double-sided, openyamm_wind 0.12, openyamm_translucency 0.35."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector, Matrix
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
W = spec['work']
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'tree.blend'))
data = json.load(open(os.path.join(W, 'clumps.json')))
clumps = data['clumps']
rng = np.random.default_rng(spec['clump_seed'])

# ---------------------------------------------------------------- LOD2 groups (groups.json, used by clump_lod2.py)
# Four cards (8 triangles) per group within the LOD2 budget. A crown that fits keeps one group per clump; otherwise the
# hidden inner clumps go first, then the nearest groups merge. Each group's cards show a render of that group, so
# leaves keep their LOD0 size on the cards.
lod2 = bpy.data.objects['Tree_LOD2']
bark_index = [i for i, m in enumerate(lod2.data.materials) if m.name == 'Bark'][0]
leaf_index = [i for i, m in enumerate(lod2.data.materials) if m.name == 'Leaves'][0]
bark2 = sum(1 for p in lod2.data.polygons if p.material_index != leaf_index)      # bark (and moss) stay at LOD2
capacity = (spec['lod']['triangles'][2] - bark2 - 10) // 8
members = [[i] for i in range(len(clumps))]
if len(members) > capacity:
    members = [[i] for i, c in enumerate(clumps) if not c['inner']]


def group_of(ids):
    weights = np.array([clumps[i]['radius'] ** 2 for i in ids])
    centre = np.average([clumps[i]['centre'] for i in ids], axis=0, weights=weights)
    radius = max(np.linalg.norm(np.array(clumps[i]['centre']) - centre) + clumps[i]['radius'] for i in ids)
    radius = radius if len(ids) == 1 else 0.85 * radius
    return {'members': ids, 'centre': centre.tolist(), 'radius': float(radius),
            'inner': all(clumps[i]['inner'] for i in ids),
            'tint': np.average([clumps[i]['tint'] for i in ids], axis=0, weights=weights).tolist(),
            'sky': float(np.average([clumps[i]['sky'] for i in ids], weights=weights)),
            'cards': [card for i in ids for card in clumps[i]['cards']]}


while len(members) > capacity:
    centres = np.array([group_of(m)['centre'] for m in members])
    d = np.linalg.norm(centres[:, None] - centres[None], axis=2); np.fill_diagonal(d, np.inf)
    a, b = np.unravel_index(int(d.argmin()), d.shape)
    members[a] = members[a] + members[b]; del members[b]
groups = [group_of(m) for m in members]
json.dump([{k: v for k, v in g.items() if k != 'cards'} for g in groups], open(os.path.join(W, 'groups.json'), 'w'))
print('CLUMP groups', len(groups), 'of', len(clumps), 'clumps; capacity', capacity)
clumps = groups
FRAME = spec['lod'].get('clump_frame', 3.0)   # cell spans FRAME x clump radius (ball, fringe and a clear border)
sc = bpy.context.scene
leaf_mat = bpy.data.materials['Leaves']
leaf_tex = next(n for n in leaf_mat.node_tree.nodes if n.type == 'TEX_IMAGE' and '_basecolor' in n.image.name)
leaf_nrm = next(n for n in leaf_mat.node_tree.nodes if n.type == 'TEX_IMAGE' and '_normal' in n.image.name)

# ---------------------------------------------------------------- representative clumps
outer = [i for i, c in enumerate(clumps) if not c['inner'] and len(c['cards']) >= 20]
median = float(np.median([clumps[i]['radius'] for i in outer]))
near = sorted(outer, key=lambda i: abs(clumps[i]['radius'] - median))[:max(6, len(outer) // 3)]
variants = [int(i) for i in rng.choice(near, 2, replace=False)]
print('CLUMP variants', variants, 'radius', [round(clumps[i]['radius'], 2) for i in variants])


def clump_object(ci):
    c = Vector(clumps[ci]['centre']); r = clumps[ci]['radius']
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for card in clumps[ci]['cards']:
        vs = [bm.verts.new((Vector(q) - c) / r) for q in card['corners']]
        f = bm.faces.new(vs)
        u0, v0, su, sv = common.cell_uv(spec, card['cell'])
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + su * du, v0 + sv * dv)
        normals += [Vector(n) for n in card['normals']]; colours += card['local']
    me = bpy.data.meshes.new('clump'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    attr = me.color_attributes.new('Local', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.concatenate([[v, v, v, 1.0] for v in colours]))
    obj = bpy.data.objects.new('clump', me); sc.collection.objects.link(obj)
    return obj


def bake_material(mode):
    m = bpy.data.materials.new(f'bake_{mode}'); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = leaf_tex.image
    em = nt.nodes.new('ShaderNodeEmission')
    if mode == 'albedo':
        attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Local'
        mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
        nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
        nt.links.new(mul.outputs[0], em.inputs['Color'])
    else:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = leaf_nrm.image
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
        vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'
        vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
        nt.links.new(nm.outputs['Normal'], vt.inputs[0])
        enc = nt.nodes.new('ShaderNodeVectorMath'); enc.operation = 'MULTIPLY_ADD'
        nt.links.new(vt.outputs[0], enc.inputs[0]); enc.inputs[1].default_value = (0.5, 0.5, -0.5)
        enc.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(enc.outputs[0], em.inputs['Color'])
    clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
    nt.links.new(tex.outputs['Alpha'], clip.inputs[0])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(clip.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m


for o in bpy.data.objects:
    o.hide_render = True
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = False
if spec.get('transparent_bounces'):
    # many overlapping cutout cards (large cards, dense crowns) exceed Cycles' default transparent bounces and
    # render black where the ray gives up; species opt in to a higher limit (absent = the approved renders)
    sc.cycles.transparent_max_bounces = spec['transparent_bounces']
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '16'
cam = bpy.data.objects.new('ClumpCam', bpy.data.cameras.new('ClumpCam')); sc.collection.objects.link(cam)
sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = FRAME; cam.data.clip_end = 100
VIEWS = {'side': ((0, -20, 0), (math.pi / 2, 0, 0)), 'top': ((0, 0, 20), (0, 0, 0))}
cells = {}
for vi, ci in enumerate(variants):
    obj = clump_object(ci)
    for mode in ('albedo', 'normal'):
        obj.data.materials.clear(); obj.data.materials.append(bake_material(mode))
        sc.view_settings.view_transform = 'Standard' if mode == 'albedo' else 'Raw'
        sc.view_settings.look = 'None'
        for view, (loc, rot) in VIEWS.items():
            cam.location = loc; cam.rotation_euler = rot
            path = os.path.join(W, f'clump{vi}_{view}_{mode}.png')
            sc.render.filepath = path; bpy.ops.render.render(write_still=True)
            cells[(vi, view, mode)] = path
    bpy.data.objects.remove(obj, do_unlink=True)
print('CLUMP renders', len(cells))
