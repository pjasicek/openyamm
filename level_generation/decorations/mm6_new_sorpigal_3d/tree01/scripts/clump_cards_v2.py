"""v2 LOD2 clump cards, step 1 of 3 (renders): work_v2/tree.blend + clumps.json -> work_v2/clump<v>_<view>_<pass>.png.
Step 2 make_clump_atlas_v2.py packs the atlas, step 3 clump_lod2_v2.py replaces Tree_LOD2's leaves.

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
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work_v2')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'tree.blend'))
data = json.load(open(os.path.join(W, 'clumps.json')))
clumps = data['clumps']; tone = float(data['tone']['2'] if '2' in data['tone'] else data['tone'][2])
rng = np.random.default_rng(2202)
FRAME = 3.0                                   # cell spans FRAME x clump radius (ball, fringe and a clear border)
sc = bpy.context.scene
leaf_mat = bpy.data.materials['Leaves']
leaf_tex = next(n for n in leaf_mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image.name.startswith('leaves_base'))
leaf_nrm = next(n for n in leaf_mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image.name.startswith('leaves_norm'))

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
        row, col = divmod(card['cell'], 2); u0, v0 = 0.5 * col, 0.5 * (1 - row)
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + 0.5 * du, v0 + 0.5 * dv)
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
