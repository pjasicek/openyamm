"""Texture-aware reduction of the Meshy helmet (MeshLab quadric collapse with wedge UVs, as decimate_tex.py), keeping
its material and textures. Blender dumps the mesh, the im_venv python decimates, Blender rebuilds and exports.
Usage: blender -b -P helmet_reduce.py -- <meshy helmet.glb> <out.glb> <target triangles>"""
import os
import subprocess
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV = '/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/da4542c9-2ca5-4473-bf19-87d753441380/scratchpad/im_venv/bin/python'
src, out, target = sys.argv[sys.argv.index('--') + 1:][:3]
work = os.path.join(HERE, 'work', 'helmet_dec'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
o = next(x for x in bpy.data.objects if x.type == 'MESH')
o.data.transform(o.matrix_world); o.matrix_world.identity(); o.parent = None
bm = bmesh.new(); bm.from_mesh(o.data)
uvl = bm.loops.layers.uv.active
# weld positions only where the UVs agree is done by MeshLab's wedge UVs; weld exact duplicates first
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
verts = np.array([v.co[:] for v in bm.verts]); faces = np.array([[v.index for v in f.verts] for f in bm.faces])
wuv = np.array([[l[uvl].uv[0], l[uvl].uv[1]] for f in bm.faces for l in f.loops])
bm.free()
np.savez(os.path.join(work, 'in.npz'), verts=verts, faces=faces, wuv=wuv)
code = r'''
import sys, numpy as np, pymeshlab as ml
sys.path.insert(0, sys.argv[3])
from prop_ladder_io import write_obj, read_obj
w, target = sys.argv[1], int(sys.argv[2])
d = np.load(w + '/in.npz')
write_obj(w + '/in.obj', d['verts'], d['faces'], d['wuv'])
ms = ml.MeshSet(); ms.load_new_mesh(w + '/in.obj'); ms.load_new_mesh(w + '/in.obj')
ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=.3, extratcoordw=1.0,
    preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
ms.save_current_mesh(w + '/out.obj', save_textures=False)
a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=20000)
b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=20000)
H = float(np.ptp(d['verts'], 0).max())
v, f, uv = read_obj(w + '/out.obj')
np.savez(w + '/out.npz', verts=v, faces=f, wuv=uv)
print('DECIMATED', len(d['faces']), '->', len(f), 'max %.3f %% mean %.4f %% of the size' % (max(a['max'], b['max']) / H * 100, max(a['mean'], b['mean']) / H * 100))
'''
r = subprocess.run([VENV, '-I', '-c', code, work, target, os.path.join(HERE, 'scripts')], capture_output=True, text=True)
print(r.stdout, r.stderr[-2000:])
d = np.load(os.path.join(work, 'out.npz'))
me = bpy.data.meshes.new('Helmet')
me.from_pydata([tuple(v) for v in d['verts'].tolist()], [], [tuple(f) for f in d['faces'].tolist()]); me.update()
me.materials.append(o.data.materials[0])
uv = me.uv_layers.new(name='UVMap')
for p in me.polygons:
    p.use_smooth = True
    for k, li in enumerate(p.loop_indices):
        uv.data[li].uv = tuple(d['wuv'][p.index * 3 + k])
h = bpy.data.objects.new('Helmet', me); bpy.context.scene.collection.objects.link(h)
# smooth shading with sharp creases, normals from the Meshy surface
h.data.set_sharp_from_angle(angle=np.radians(60))
bpy.data.objects.remove(o, do_unlink=True)
for x in bpy.data.objects:
    x.select_set(x is h)
bpy.context.view_layer.objects.active = h
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB',
                          export_animations=False, export_skins=False)
print('HELMET', len(me.polygons), 'triangles ->', out)
