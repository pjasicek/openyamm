"""Replace Body in a cdr1-rig blend with a mesh from an npz (co, tri, uv, mat, W, bones; optional uv_v2head, attrs).
Head material preview: the v2 head base colour on the UV_v2head layer. Usage:
blender -b <rig.blend> -P build_mesh.py -- <mesh.npz> <out.blend> [--preview]"""
import bpy, sys, numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[2]
a = sys.argv[sys.argv.index('--') + 1:]
d = np.load(a[0]); preview = '--preview' in a
old = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; mats = list(old.data.materials)
me = bpy.data.meshes.new('BodyMesh')
co = d['co']; tri = d['tri']
me.vertices.add(len(co)); me.vertices.foreach_set('co', co.astype(np.float32).ravel())
me.loops.add(len(tri) * 3); me.loops.foreach_set('vertex_index', tri.astype(np.int32).ravel())
me.polygons.add(len(tri)); me.polygons.foreach_set('loop_start', np.arange(0, len(tri) * 3, 3, dtype=np.int32))
me.polygons.foreach_set('loop_total', np.full(len(tri), 3, np.int32))
me.polygons.foreach_set('material_index', d['mat'].astype(np.int32))
uvl = me.uv_layers.new(name='UVMap'); uvl.data.foreach_set('uv', d['uv'].astype(np.float32).reshape(-1))
if 'uv_v2head' in d.files:
    u2 = me.uv_layers.new(name='UV_v2head'); u2.data.foreach_set('uv', d['uv_v2head'].astype(np.float32).reshape(-1))
me.uv_layers.active_index = 0
for k in d.files:
    if k.startswith('pa_'):
        at = me.attributes.new(k[3:], 'INT', 'POINT'); at.data.foreach_set('value', d[k].astype(np.int32))
me.validate(); me.update()
for m in mats: me.materials.append(m)
new = bpy.data.objects.new('BodyNew', me); bpy.context.collection.objects.link(new)
new.parent = rig
bones = [str(b) for b in d['bones']]; W = d['W']
for j, b in enumerate(bones):
    g = new.vertex_groups.new(name=b); nz = np.where(W[:, j] > 0)[0]
    for v in nz: g.add([int(v)], float(W[v, j]), 'REPLACE')
mod = new.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
bpy.data.objects.remove(old, do_unlink=True); new.name = 'Body'; me.name = 'Body'
for p in me.polygons: p.use_smooth = True
if preview:
    m = bpy.data.materials.new('HeadPreview'); m.use_nodes = True; nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(P / 'textures/dragon_head_basecolor_2k.png'))
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UV_v2head'; nt.links.new(uvn.outputs[0], tex.inputs[0])
    nt.links.new(tex.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color'])
    me.materials[1] = m
print('BUILT', len(co), len(tri), 'groups', len(bones))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
