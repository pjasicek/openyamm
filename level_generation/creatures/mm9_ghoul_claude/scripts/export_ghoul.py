"""Textured static export for clips_mm9.py: materials Ghoul (body set) and GhoulHead (head set); head faces take HeadUV; flap lining and rim, skull plug;
the armature lifted so model y = 0 is the floor. Args: <uv blend> <out glb> <body base> <head base> <normal> <orm> <head normal> <head orm>"""
import bpy, bmesh, sys, os
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, BASE, HBASE, NORM, ORM, HNORM, HORM = A
bpy.ops.wm.open_mainfile(filepath=IN)
TX = bpy.path.abspath('//../textures')
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for b in rig.pose.bones: b.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
# flap lining and rim: the flaps are single sheets, back faces are culled: an inner copy 4 mm toward the body (same UVs), and a rim on the open edge
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']; hl = bm.faces.layers.int['head']
fs = [f for f in bm.faces if all(v[lay] in (6, 7) for v in f.verts)]
nrm = {v: v.normal.copy() for f in fs for v in f.verts}
bd = [e for e in bm.edges if e.is_boundary and all(v[lay] in (6, 7) for v in e.verts)]
ret = bmesh.ops.duplicate(bm, geom=fs)
nf = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
vm = ret['vert_map']
for src, dst in vm.items():
    if isinstance(src, bmesh.types.BMVert) and src in nrm:
        dst.co = src.co - nrm[src] * 0.004
bmesh.ops.reverse_faces(bm, faces=nf)
buv_ = bm.loops.layers.uv['UVMap']; huv_ = bm.loops.layers.uv['HeadUV']
n_rim = 0
for e in bd:
    a, b_ = e.verts
    f0 = e.link_loops[0]
    if f0.vert is not a: a, b_ = b_, a
    uv = {l.vert: l[buv_].uv.copy() for l in e.link_faces[0].loops}
    q = bm.faces.new([b_, a, vm[a], vm[b_]])
    for l in q.loops:
        s_ = l.vert if l.vert in uv else next(k for k, w in vm.items() if isinstance(k, bmesh.types.BMVert) and w is l.vert)
        l[buv_].uv = uv[s_]
    q[hl] = 0
    n_rim += 1
# back faces are culled, so the mouth, nostrils and any gap at the jaw looked through the hollow head at the sky: a dark plug inside the skull, rigid on the head, in a dark texel of the head set
import json
dk = json.load(open(bpy.path.abspath('//dark_uv.json')))
from mathutils import Matrix
ret_ = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=Matrix.Translation((0, 0.03, 0.80)) @ Matrix.Diagonal((0.092, 0.115, 0.115, 1)))
dl = bm.verts.layers.deform.verify()
gid = body.vertex_groups['Bip01 Head'].index
fs_ = {f for v in ret_['verts'] for f in v.link_faces}
for v in ret_['verts']:
    v[lay] = 12; v[dl].clear(); v[dl][gid] = 1.0
for f in fs_:
    f[hl] = 1
    for l in f.loops: l[huv_].uv = (dk['u'], dk['v']); l[buv_].uv = (dk['u'], dk['v'])
bmesh.ops.recalc_face_normals(bm, faces=list(fs_))
print('PLUG', len(fs_), 'LINING', len(fs), 'RIM', n_rim)
bm.to_mesh(me); bm.free()
nf_ = len(me.polygons)
hd = np.zeros(nf_, np.int32); me.attributes['head'].data.foreach_get('value', hd)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if hd[p.index]:
        for li in p.loop_indices: buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV'])


def material(name, base, normal, mr):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(TX, fname), check_existing=True); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


me.materials.clear()
me.materials.append(material('Ghoul', BASE, NORM, ORM))
me.materials.append(material('GhoulHead', HBASE, HNORM, HORM))
me.polygons.foreach_set('material_index', hd.tolist())
for a in [a.name for a in me.attributes if a.name in ('head', 'part')]:
    me.attributes.remove(me.attributes[a])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'Ghoul'; me.name = 'Ghoul'
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', OUT, len(me.polygons))
