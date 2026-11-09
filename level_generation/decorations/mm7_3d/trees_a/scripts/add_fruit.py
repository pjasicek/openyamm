"""Fruit for a food tree (work/<id>/tree.blend, copied from its base species): spec fruit.count fruit (LOD0, LOD1,
LOD2 counts; LOD1/LOD2 keep the first ones, so a level switch never moves a fruit) on the outer face of the crown's
outer clumps, each a small smooth ball of two offset rings (LOD0, 16 triangles), octahedron (LOD1) or tetrahedron (LOD2) of radius fruit.radius_m,
material Fruit (opaque, solid colour fruit.srgb, wind as the leaves so it sways with the crown), COLOR_0 0.9.
Image paths are pointed at this species' own copies. Usage: blender --background --python add_fruit.py -- <id>"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load(); W = spec['work']; FRUIT = spec['fruit']
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'tree.blend'))
for img in bpy.data.images:
    if img.filepath:
        own = os.path.join(W, os.path.basename(bpy.path.abspath(img.filepath)))
        if os.path.exists(own):
            img.filepath = own; img.reload()
clumps = json.load(open(os.path.join(W, 'clumps.json')))['clumps']
H = spec['height_m']
centre = Vector((0, 0, common.load(spec['base'])['crown']['centre'] * H))
rng = np.random.default_rng(9090)
outer = [c for c in clumps if not c['inner']]
points = []
for c in rng.permutation(len(outer)):
    if len(points) >= FRUIT['count'][0]:
        break
    cl = outer[int(c)]; cc = Vector(cl['centre'])
    out = (cc - centre); out.z *= 0.6; out.normalize()
    d = (out + Vector(rng.normal(0, 0.35, 3))).normalized()
    if d.z > 0.7 or d.z < -0.6:                         # sides of the clump, not its crown or underside
        continue
    p = cc + d * cl['radius'] * FRUIT.get('depth', 0.8) + Vector((0, 0, -0.05))
    if all((p - q).length > 0.35 for q in points):
        points.append(p)
print('FRUIT positions', len(points))


def material():
    m = bpy.data.materials.new('Fruit'); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    colour = bpy.data.images.new('fruit_basecolor', 4, 4); lin = common.lin(np.array(FRUIT['srgb']) / 255.0)
    colour.pixels = [*lin, 1.0] * 16; colour.filepath_raw = os.path.join(W, 'fruit_basecolor.png')
    colour.file_format = 'PNG'; colour.save()
    flat = bpy.data.images.new('fruit_normal', 4, 4); flat.pixels = [0.5, 0.5, 1.0, 1.0] * 16
    flat.colorspace_settings.name = 'Non-Color'
    flat.filepath_raw = os.path.join(W, 'fruit_normal.png'); flat.file_format = 'PNG'; flat.save()
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = colour
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = flat
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.45; bsdf.inputs['Metallic'].default_value = 0.0
    m['openyamm_wind'] = bpy.data.materials['Leaves']['openyamm_wind']
    return m


fruit_mat = material()
R = FRUIT['radius_m']
for lod, name in enumerate(('Tree', 'Tree_LOD1', 'Tree_LOD2')):
    # The fruit is built as its own object and joined, so the tree's own vertices, normals and colours stay
    # exactly as in the base species.
    tree = bpy.data.objects[name]
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    normals = []
    for p in points[:FRUIT['count'][lod]]:
        if lod == 0:                     # two offset rings and blunt poles (16 triangles): a round silhouette
            dirs = [Vector((0.82 * math.cos(k * math.pi / 2), 0.82 * math.sin(k * math.pi / 2), 0.5)) for k in range(4)]
            dirs += [Vector((0.82 * math.cos((k + 0.5) * math.pi / 2), 0.82 * math.sin((k + 0.5) * math.pi / 2), -0.5))
                     for k in range(4)]
            dirs += [Vector((0, 0, 0.95)), Vector((0, 0, -0.95))]
            faces = [(k, (k + 1) % 4, 8) for k in range(4)] + [(4 + (k + 1) % 4, 4 + k, 9) for k in range(4)]
            faces += [(k, 4 + k, (k + 1) % 4) for k in range(4)] + [((k + 1) % 4, 4 + k, 4 + (k + 1) % 4)
                                                                     for k in range(4)]
        elif lod == 1:
            dirs = [Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1.1), (0, 0, -1.1))]
            faces = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        else:
            dirs = [Vector(v).normalized() for v in ((1, 1, 1), (-1, -1, 1), (-1, 1, -1), (1, -1, -1))]
            faces = [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)]
        vs = [bm.verts.new(p + d * R) for d in dirs]
        normals += [d.normalized() for d in dirs]
        for f in faces:
            face = bm.faces.new([vs[i] for i in f]); face.smooth = True
            for loop in face.loops:
                loop[uv].uv = (0.5, 0.5)
    me = bpy.data.meshes.new(f'fruit{lod}'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', [0.9, 0.9, 0.9, 1.0] * len(me.vertices)); me.color_attributes.active_color = attr
    me.materials.append(fruit_mat)
    fruit = bpy.data.objects.new(f'fruit{lod}', me); bpy.context.scene.collection.objects.link(fruit)
    for x in bpy.data.objects:
        x.select_set(x in (tree, fruit))
    bpy.context.view_layer.objects.active = tree
    bpy.ops.object.join()
    print('FRUIT lod', lod, name, FRUIT['count'][lod], 'tris', len(tree.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'tree.blend'))
