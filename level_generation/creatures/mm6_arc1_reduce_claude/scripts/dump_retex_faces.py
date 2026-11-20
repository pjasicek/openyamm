"""Per-corner data of work/retex_<label>.blend for compose_retex.py, every UV layer looked up by name:
rest positions, OldUV / Upload / UVMap, per-face head and comp -> work/retex_faces_<label>.npz.
Usage: blender -b -P dump_retex_faces.py -- <label> <cand object>"""
import bpy, os, sys
import numpy as np
label, name = sys.argv[sys.argv.index('--') + 1:][:2]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'retex_{label}.blend'))
ob = bpy.data.objects[name]; me = ob.data
me.calc_loop_triangles(); tris = list(me.loop_triangles)
co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
take = lambda n: np.array([[tuple(me.uv_layers[n].data[l].uv) for l in t.loops] for t in tris], np.float32)
attr = lambda n: np.array([a.value for a in me.attributes[n].data])
head, comp = attr('head'), attr('comp')
np.savez_compressed(os.path.join(HERE, 'work', f'retex_faces_{label}.npz'),
                    pos=np.array([[co[v] for v in t.vertices] for t in tris], np.float32),
                    old=take('OldUV'), upload=take('Upload'), runtime=take('UVMap'),
                    head=np.array([head[t.polygon_index] for t in tris]), comp=np.array([comp[t.polygon_index] for t in tris]))
print('DUMPED', len(tris), [l.name for l in me.uv_layers])
