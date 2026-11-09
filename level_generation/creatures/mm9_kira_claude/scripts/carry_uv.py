"""Rig iterations after the paint: the rig chain (rig_nb, graft_hands, helpers_nb) is deterministic on the frozen graft, so its mesh equals the painted one vertex for vertex. Copies the UV layers and `mat` from the UV blend onto a new rigged blend, after checking
positions and faces match. Args: <rigged blend> <uv blend> <out blend>"""
import bpy, sys
import numpy as np
IN, UV, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
with bpy.data.libraries.load(UV) as (src, dst):
    dst.objects = ['Body']
uo = dst.objects[0]; um = uo.data
nv, nf, nl = len(me.vertices), len(me.polygons), len(me.loops)
assert (nv, nf, nl) == (len(um.vertices), len(um.polygons), len(um.loops)), ((nv, nf, nl), (len(um.vertices), len(um.polygons), len(um.loops)))
a = np.zeros(nv * 3); b = a.copy(); me.vertices.foreach_get('co', a); um.vertices.foreach_get('co', b)
la = np.zeros(nl, int); lb = la.copy(); me.loops.foreach_get('vertex_index', la); um.loops.foreach_get('vertex_index', lb)
print('CARRY max vertex move', float(np.abs(a - b).max()), 'loops differ', int((la != lb).sum()))
assert np.abs(a - b).max() < 1e-4 and (la == lb).all()
for n in ('UVMap', 'HeadUV', 'PartUV'):
    if n in me.uv_layers: me.uv_layers.remove(me.uv_layers[n])
    d = np.zeros(nl * 2, np.float32); um.uv_layers[n].data.foreach_get('uv', d)
    me.uv_layers.new(name=n); me.uv_layers[n].data.foreach_set('uv', d)
mt = np.zeros(nf, np.int32); um.attributes['mat'].data.foreach_get('value', mt)
if 'mat' in me.attributes: me.attributes.remove(me.attributes['mat'])
me.attributes.new('mat', 'INT', 'FACE').data.foreach_set('value', mt.tolist())
me.uv_layers.active = me.uv_layers['UVMap']
bpy.data.objects.remove(uo); bpy.data.meshes.remove(um)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CARRY done', OUT)
