"""Mallet UVs from claude_shared/uv_atlas.py (sharp-texture layout, as the body; the analytic strip layout stretched the shaft 23x).
Reads work/mallet.npz (make_mallet.py), writes per-corner UVs as UVc (F x 3 x 2) into it and the report to work/uv_mallet.json.
Args: -- <size>"""
import bpy, sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
size = int(sys.argv[sys.argv.index('--') + 1])
Z = dict(np.load(os.path.join(HERE, 'work', 'mallet.npz')))
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Mallet'); me.from_pydata(Z['V'].tolist(), [], Z['F'].tolist()); me.update()
ob = bpy.data.objects.new('Mallet', me); bpy.context.scene.collection.objects.link(ob)
me.uv_layers.new(name='UVMap')
rep = uv_atlas.unwrap(ob, size=size, merge_below=int(os.environ.get('MERGE', 12)), max_cost=float(os.environ.get('COST', 2.0)), cut_closed=bool(int(os.environ.get('CUT', 0))), max_stretch=(float(os.environ['MAXST']) if 'MAXST' in os.environ else None))
uv = me.uv_layers['UVMap'].data
UVc = np.array([[uv[l].uv[:] for l in p.loop_indices] for p in me.polygons])
assert len(UVc) == len(Z['F']) and all(tuple(p.vertices) == tuple(f) for p, f in zip(me.polygons, Z['F']))
Z['UVc'] = UVc
np.savez(os.path.join(HERE, 'work', 'mallet.npz'), **Z)
json.dump(rep, open(os.path.join(HERE, 'work', 'uv_mallet.json'), 'w'), indent=1, default=str)
print('UVMALLET', {k: rep[k] for k in ('charts', 'use') if k in rep})
