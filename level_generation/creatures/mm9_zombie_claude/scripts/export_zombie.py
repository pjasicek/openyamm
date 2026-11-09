"""Textured static export for clips_mm9.py: materials Zombie (body set) and ZombieHead (head set); head faces take HeadUV; a tatter lining (coincident inner faces, same UVs: back faces are culled in game);
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
# lining
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']; hl = bm.faces.layers.int['head']
fs = [f for f in bm.faces if all(v[lay] == 2 for v in f.verts)]
nrm = {v: v.normal.copy() for f in fs for v in f.verts}
ret = bmesh.ops.duplicate(bm, geom=fs)
nf = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
nv = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
vm = ret['vert_map']
for src, dst in vm.items():
    if isinstance(src, bmesh.types.BMVert) and src in nrm:
        dst.co = src.co - nrm[src] * 0.0015
bmesh.ops.reverse_faces(bm, faces=nf)
# the bridge between head and body rings was a strip of slivers (collapse gate at the neck): each head-ring vertex welds onto the nearest body-ring vertex
bf = [f for f in bm.faces if {v[lay] for v in f.verts} >= {0, 10}]
r0 = {v for f in bf for v in f.verts if v[lay] == 0}; r1 = {v for f in bf for v in f.verts if v[lay] == 10}
tm = {}
for v in r1:
    tm[v] = min(r0, key=lambda q: (q.co - v.co).length_squared)
bmesh.ops.weld_verts(bm, targetmap=tm)
print('WELD', len(bf), len(r0), len(r1))
# back faces are culled in game, so the mouth and nostrils looked through the hollow head at the sky: a dark plug inside the skull, rigid on the head, in a dark texel of the head set
import json
dk = json.load(open(bpy.path.abspath('//dark_uv.json')))
from mathutils import Matrix
ret_ = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=Matrix.Translation((0, 0.005, 0.895)) @ Matrix.Diagonal((0.058, 0.058, 0.062, 1)))
dl = bm.verts.layers.deform.verify()
gid = body.vertex_groups['Bip01 Head'].index
huv_ = bm.loops.layers.uv['HeadUV']; buv_ = bm.loops.layers.uv['UVMap']
tl = bm.faces.layers.int['torso']
fs_ = {f for v in ret_['verts'] for f in v.link_faces}
for v in ret_['verts']:
    v[lay] = 12; v[dl].clear(); v[dl][gid] = 1.0
for f in fs_:
    f[hl] = 1; f[tl] = 0
    for l in f.loops: l[huv_].uv = (dk['u'], dk['v']); l[buv_].uv = (dk['u'], dk['v'])
bmesh.ops.recalc_face_normals(bm, faces=list(fs_))
print('PLUG', len(fs_))
# stray shards left by the reductions
seen = set(); dead = []
for f0 in bm.faces:
    if f0 in seen: continue
    st = [f0]; seen.add(f0); cc = [f0]
    while st:
        f = st.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g not in seen: seen.add(g); st.append(g); cc.append(g)
    if len(cc) < 5: dead += cc
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
print('LINING', len(fs), 'shards', len(dead))
bm.to_mesh(me); bm.free()
nf_ = len(me.polygons)
hd = np.zeros(nf_, np.int32); me.attributes['head'].data.foreach_get('value', hd)
to = np.zeros(nf_, np.int32); me.attributes['torso'].data.foreach_get('value', to)
huv, buv, tuv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data, me.uv_layers['TorsoUV'].data
for p in me.polygons:
    if hd[p.index] or to[p.index]:
        src = huv if hd[p.index] else tuv
        for li in p.loop_indices: buv[li].uv = src[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers.remove(me.uv_layers['HeadUV']); me.uv_layers.remove(me.uv_layers['TorsoUV'])


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
me.materials.append(material('Zombie', BASE, NORM, ORM))
me.materials.append(material('ZombieHead', HBASE, HNORM, HORM))
me.materials.append(material('ZombieTorso', 'zombie_torso_a_final.png', 'zombie_torso_a_normal.png', 'zombie_torso_b_metal_rough_1k.png'))
me.polygons.foreach_set('material_index', (hd + 2 * to).tolist())
for a in [a.name for a in me.attributes if a.name in ('head', 'part', 'torso')]:
    me.attributes.remove(me.attributes[a])
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects: o.select_set(o == body)
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = 'Zombie'; me.name = 'Zombie'
for o in bpy.data.objects: o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False, export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', OUT, len(me.polygons))
