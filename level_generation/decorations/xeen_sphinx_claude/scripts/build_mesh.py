"""Stage 2 (Blender): the high and low meshes of a sphinx.

- HighBody: the striped SDF surface (work/<id>/sdf.npz, cell 6) in metres (1 m = 100 units), Blender axes
  (x = +x, y = -f, z = z): the model faces -Y (glTF +Z). Material `HighStone` adds the stone grain (egywalh, box
  projected) as bump, which the normal bake picks up.
- HighFace: the MM6 peasant's head (assets_source/worlds/mm6/models/mm6_pman.glb, bind pose) cut below the chin,
  scaled so chin to crown is 790 head units and set into the nemes window (nose tip 85 in front of the face plane);
  it keeps its own normal map (carved brows, eyes, lips).
- LowBody: the flat (stripe-free) SDF surface (sdf_low.npz, cell 14) collapse-decimated to `lod0_body_tris`;
  LowFace: HighFace decimated to `lod0_face_tris`. Both triangulated, degenerate faces dissolved.
Writes work/<id>/mesh.blend. Usage: blender -b --python build_mesh.py -- <id>"""
import json
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
sid = sys.argv[sys.argv.index('--') + 1]
cfg = json.load(open(os.path.join(HERE, 'sphinx.json')))[sid]
work = os.path.join(PROJECT, 'work', sid)
PMAN = os.path.join(REPO, 'assets_source', 'worlds', 'mm6', 'models', 'mm6_pman.glb')
GRAIN = os.path.join(REPO, 'assets_source', 'worlds', 'mm6', 'textures_x4', 'egywalh.png')
U = 0.01   # metres per unit


def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def npz_mesh(path, name):
    d = np.load(path)
    v = d['verts'].astype(np.float64)
    q = d['quads']
    used = np.unique(q)
    remap = np.full(len(v), -1, np.int64)
    remap[used] = np.arange(len(used))
    v = v[used]
    q = remap[q]
    co = np.stack([v[:, 0], -v[:, 1], v[:, 2]], 1) * U
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(co))
    me.vertices.foreach_set('co', co.astype(np.float32).ravel())
    me.loops.add(q.size)
    me.loops.foreach_set('vertex_index', q.astype(np.int32).ravel())
    me.polygons.add(len(q))
    me.polygons.foreach_set('loop_start', (np.arange(len(q)) * 4).astype(np.int32))
    me.update(calc_edges=True)
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    # the y flip mirrors the winding: flip back so the faces point outward
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    top = max(me.polygons, key=lambda p: p.center.z)
    print(name, 'top face normal z %.2f (must be > 0)' % top.normal.z)
    return ob


def face_graft():
    """The peasant's head in the bind pose, cut below the chin, scaled and placed in the nemes window."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=PMAN)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    body = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
    arm.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(body.matrix_world)
    mats = list(body.data.materials)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    co = np.array([v.co for v in me.vertices])
    top = co[:, 2].max()
    height = top - co[:, 2].min()
    head = co[:, 2] > top - 0.16 * height
    front = co[head, 1].min()
    centre = head & (np.abs(co[:, 0]) < 0.014 * height) & (co[:, 1] < front + 0.035 * height)
    chin = co[centre, 2].min()
    nose = co[head & (np.abs(co[:, 0]) < 0.01 * height), 1].min()
    print('FACE source height %.3f top %.3f chin %.3f nose_y %.3f' % (height, top, chin, nose))
    hs = cfg['head']['scale']
    s = cfg.get('face_size', 790) * hs * U / (top - chin)
    # cut below the chin (a little neck kept, it sinks into the body's neck)
    bm = bmesh.new()
    bm.from_mesh(me)
    cut = chin - 0.06 * (top - chin)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < cut], context='VERTS')
    for v in bm.verts:
        v.co.x = v.co.x * s
        v.co.y = (v.co.y - nose) * s - (cfg['head']['f'] + 85 * hs) * U
        v.co.z = (v.co.z - chin) * s + cfg['head']['z'] * U
    # what stays inside the nemes is dropped (texture and triangles): behind the face window's back wall (head g
    # -330) and, above the window, behind the forehead band's front
    def hidden(v):
        g = (-v.co.y / U - cfg['head']['f']) / hs
        zl = (v.co.z / U - cfg['head']['z']) / hs
        return g < -380 or (zl > 640 and g < -60)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if hidden(v)], context='VERTS')
    bm.to_mesh(me)
    bm.free()
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new('HighFace', me)
    bpy.context.scene.collection.objects.link(ob)
    print('FACE scale %.2f, %d triangles' % (s / U, tris(me)))
    return ob


def stone_bump_material():
    m = bpy.data.materials.new('HighStone')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    acc = None
    for scale, weight in ((1 / 2.56, 0.6), (1 / 0.96, 0.4)):
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale, scale, scale)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        tx = nt.nodes.new('ShaderNodeTexImage')
        tx.image = bpy.data.images.load(GRAIN, check_existing=True)
        tx.image.colorspace_settings.name = 'Non-Color'
        tx.projection = 'BOX'
        tx.projection_blend = 0.3
        nt.links.new(mp.outputs[0], tx.inputs['Vector'])
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = weight
        nt.links.new(tx.outputs['Color'], mul.inputs[0])
        if acc is None:
            acc = mul.outputs[0]
        else:
            add = nt.nodes.new('ShaderNodeMath')
            nt.links.new(acc, add.inputs[0])
            nt.links.new(mul.outputs[0], add.inputs[1])
            acc = add.outputs[0]
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.04
    nt.links.new(acc, bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def decimated(ob, target, name):
    tmp = bpy.data.objects.new('tmp', ob.data.copy())
    bpy.context.scene.collection.objects.link(tmp)
    mod = tmp.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = min(1.0, target / tris(tmp.data))
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.dissolve_degenerate(bm, dist=2e-4, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY')
    bm.to_mesh(me)
    bm.free()
    me.name = name
    me.materials.clear()
    for a in [a for a in me.attributes if a.domain == 'CORNER' and a.data_type in ('BYTE_COLOR', 'FLOAT_COLOR')]:
        me.attributes.remove(a)
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    ob2 = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob2)
    print(name, 'triangles', tris(me))
    return ob2


bpy.ops.wm.read_factory_settings(use_empty=True)
high = npz_mesh(os.path.join(work, 'sdf.npz'), 'HighBody')
high.data.materials.append(stone_bump_material())
face = face_graft()
low_src = npz_mesh(os.path.join(work, 'sdf_low.npz'), 'LowSource')
print('HighBody triangles', 2 * len(high.data.polygons), 'LowSource quads', len(low_src.data.polygons))
low = decimated(low_src, cfg['lod0_body_tris'], 'LowBody')
# the doorway stays open at the back (A5's door leaves stand in it at the door plane, y 0)
D = cfg['door']
bm = bmesh.new()
bm.from_mesh(low.data)
back = [f for f in bm.faces if all(abs(-v.co.y * 100 - D['back']) < 6 and abs(v.co.x * 100) < D['width'] / 2 - 1
                                   and v.co.z * 100 < D['height'] - 1 for v in f.verts)]
bmesh.ops.delete(bm, geom=back, context='FACES')
bm.to_mesh(low.data)
bm.free()
print('door back faces removed', len(back))
bpy.data.objects.remove(low_src, do_unlink=True)
low_face = decimated(face, cfg['lod0_face_tris'], 'LowFace')
for o in (high, face):
    o.data.shade_smooth()
for o in (low, low_face):
    o.data.shade_smooth()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'mesh.blend'))
print('MESH_DONE')
