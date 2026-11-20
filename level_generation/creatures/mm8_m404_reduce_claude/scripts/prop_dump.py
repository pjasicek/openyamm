"""Static decoration GLBs -> work/<name>.npz: LOD0 vertices, triangles, wedge UVs (u + 100 x material: bark UVs tile beyond 0-1), opaque flag per
face, model height. Usage: blender -b -P deco_dump.py -- name [name ...] (work/mm8_m404_<name>_source_pre_reduce.glb)"""
import os, sys, bpy, bmesh, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
for name in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, f'level_generation/creatures/mm8_m404_reduce_claude/work/mm8_m404_{name}_source_pre_reduce.glb'))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(meshes) == 1, [o.name for o in meshes]
    o = meshes[0]
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.triangulate(bm, faces=bm.faces); bm.transform(o.matrix_world)
    uvl = bm.loops.layers.uv.active
    # alpha-mask/blend materials (leaf cards, water) feed the Principled Alpha socket
    opaque = [True] * len(o.data.materials)
    for i, m in enumerate(o.data.materials):
        opaque[i] = not any(n.type == 'BSDF_PRINCIPLED' and (n.inputs['Alpha'].is_linked or n.inputs['Alpha'].default_value < 1)
                            for n in m.node_tree.nodes) if m.node_tree else True
    bm.verts.index_update()
    faces = [f for f in bm.faces]
    np.savez(os.path.join(HERE, 'work', f'{name}.npz'),
             verts=np.array([v.co[:] for v in bm.verts]), faces=np.array([[v.index for v in f.verts] for f in faces], np.int32),
             wuv=np.array([[l[uvl].uv[0] + 100.0 * f.material_index, l[uvl].uv[1]] for f in faces for l in f.loops]),
             opaque=np.array([opaque[f.material_index] for f in faces]),
             materials=np.array([m.name for m in o.data.materials]))
    zs = [v.co.z for v in bm.verts]
    print('DUMP', name, len(faces), 'faces', sum(opaque[f.material_index] for f in faces), 'opaque; height', round(max(zs) - min(zs), 3), [m.name for m in o.data.materials], opaque)
