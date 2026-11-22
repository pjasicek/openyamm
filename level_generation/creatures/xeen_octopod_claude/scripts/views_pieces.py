"""Clay views of the raw Smart Topology return with its connected pieces coloured (main body grey, small pieces
yellow, the two largest extra pieces red and blue): review/pieces_<view>.png."""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = 'Octopod'
lab = np.load(os.path.join(HERE, 'work', 'raw_label.npy'))
u, c = np.unique(lab, return_counts=True); order = u[np.argsort(-c)]
cols = {order[0]: (0.7, 0.7, 0.7, 1), order[1]: (0.9, 0.1, 0.1, 1), order[2]: (0.1, 0.2, 0.9, 1)}
mesh.data.materials.clear()
mats = {}
for key, col in list(cols.items()) + [('small', (0.95, 0.85, 0.1, 1))]:
    m = bpy.data.materials.new(str(key)); m.diffuse_color = col; mesh.data.materials.append(m); mats[key] = len(mesh.data.materials) - 1
for p in mesh.data.polygons:
    k = lab[p.vertices[0]]
    p.material_index = mats.get(k, mats['small'])
for name, (loc, tgt, s) in {'face': ((0, -3, 0.05), (0, 0, 0.0), 0.5), 'top': ((0, 0, 3), (0, 0, 0), 1.1),
                            'quarter': ((-1.6, -2.0, 1.4), (0, 0, 0), 1.2), 'under': ((0, 0, -3), (0, 0, 0), 1.1),
                            'facequarter': ((-1.2, -2.2, 0.8), (0, -0.1, 0.0), 0.55)}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'pieces_{name}.png'), res=(700, 500), floor=False,
             color='MATERIAL')
print('VIEWS done')
