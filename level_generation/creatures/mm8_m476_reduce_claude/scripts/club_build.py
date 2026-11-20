"""Reduced club LOD0 per step (work/club/mesh_r<NN>.npz): geometry, wedge UVs and the source material, custom normals
by data transfer from the unwelded source club (its own glTF normals; no weld), two-way surface error against the
source. Exports work/club_r<NN>_lod0.glb (node Club). Usage: blender -b -P club_build.py -- <NN,...>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for tag in sys.argv[sys.argv.index('--') + 1].split(','):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', 'mm8_m476_club_source_pre_reduce.glb'))
    src = next(o for o in bpy.data.objects if o.type == 'MESH'); src.name = 'Source'
    d = np.load(os.path.join(HERE, 'work', 'club', f'mesh_r{tag}.npz'))
    me = bpy.data.meshes.new('Club'); me.from_pydata([tuple(v) for v in d['verts'].tolist()], [], [tuple(f) for f in d['faces'].tolist()])
    me.update(); me.materials.append(src.data.materials[0])
    uvl = me.uv_layers.new(name=src.data.uv_layers.active.name); w = d['wuv']
    for p in me.polygons:
        p.use_smooth = True
        for k, li in enumerate(p.loop_indices):
            uvl.data[li].uv = (w[p.index * 3 + k][0], w[p.index * 3 + k][1])
    c = bpy.data.objects.new('Club', me); bpy.context.scene.collection.objects.link(c); c.matrix_world = src.matrix_world.copy()
    dt = c.modifiers.new('N', 'DATA_TRANSFER'); dt.object = src; dt.use_loop_data = True
    dt.data_types_loops = {'CUSTOM_NORMAL'}; dt.loop_mapping = 'POLYINTERP_NEAREST'
    for o in bpy.data.objects:
        o.select_set(o == c)
    bpy.context.view_layer.objects.active = c; bpy.ops.object.modifier_apply(modifier=dt.name)
    bs = bmesh.new(); bs.from_mesh(src.data); bc = bmesh.new(); bc.from_mesh(me)
    ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
    e = [tc.find_nearest(v.co)[3] for v in bs.verts] + [ts.find_nearest(v.co)[3] for v in bc.verts]
    e = np.array(e) * 1000
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', f'club_r{tag}_lod0.glb'), use_selection=True, export_format='GLB',
                              export_yup=True, export_animations=False, export_skins=False, export_image_format='NONE')
    print(f'CLUB r{tag} tris {len(me.polygons)} err p99 {np.percentile(e, 99):.2f} max {e.max():.2f} mm')
