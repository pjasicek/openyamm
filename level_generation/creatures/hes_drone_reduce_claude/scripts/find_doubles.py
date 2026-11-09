"""Two-sided sheets of the installed GLB (a face plus its reversed copy on the same positions: wing membranes) before
import_source.py's weld merges each pair into one face. Writes work/doubles.npy (sorted corner positions, mesh-local
Blender space, per pair) for keep_doubles.py and export_cand.py (REA_DOUBLES). Usage: REA_GLB=... blender -b -P find_doubles.py"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, os.environ['REA_GLB']))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == os.environ.get('REA_NODE', 'Body'))
me = body.data; me.calc_loop_triangles()
co = np.array([v.co[:] for v in me.vertices])
seen, pairs = {}, []
for t in me.loop_triangles:
    p = co[list(t.vertices)]; key = tuple(sorted(map(tuple, np.round(p, 5))))
    if key in seen:
        pairs.append(np.array(key))
    else:
        seen[key] = t.index
np.save(os.path.join(HERE, 'work', 'doubles.npy'), np.array(pairs))
print('DOUBLES', len(pairs), 'of', len(me.loop_triangles))
