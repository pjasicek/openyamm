"""Torso part: faces with a design difference between tiers (upper body inside the arm cut, tatter, rope) get their own UV layout TorsoUV and a face attribute `torso`. Body UVMap and HeadUV stay.
Writes the tier B upload: the whole figure, non-torso faces collapsed to one UV point. Args: <uv blend> <out blend> <upload glb> <report>. Never re-run once the upload went to Meshy."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, OUT, UP, REP = sys.argv[sys.argv.index('--') + 1:]
CUT_X = 0.315
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
nv = len(me.vertices); nf = len(me.polygons)
pa = np.zeros(nv, np.int32); me.attributes['part'].data.foreach_get('value', pa)
hd = np.zeros(nf, np.int32); me.attributes['head'].data.foreach_get('value', hd)
P = np.array([v.co[:] for v in me.vertices]); fv = np.array([p.vertices[:] for p in me.polygons])
torso = (hd == 0) & (((pa[fv] == 0).all(1) & (np.abs(P[fv, 0]).mean(1) < CUT_X)) | np.isin(pa[fv], (2, 3)).all(1))
print('torso faces', int(torso.sum()), 'of', nf)
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup); dm = dup.data
dm.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', list(range(nf)))
dm.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', list(range(nv)))
bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not torso[f.index]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dm); bm.free(); dm.update()
for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
rep = uv_atlas.unwrap(dup, size=1536)
fo = np.zeros(len(dm.polygons), np.int32); dm.attributes['fo'].data.foreach_get('value', fo)
vo = np.zeros(len(dm.vertices), np.int32); dm.attributes['vo'].data.foreach_get('value', vo)
uv = dm.uv_layers['UVMap'].data
tmap = {}
for p in dm.polygons:
    for li in p.loop_indices: tmap[(int(fo[p.index]), int(vo[dm.loops[li].vertex_index]))] = tuple(uv[li].uv)
bpy.data.objects.remove(dup)
if 'TorsoUV' in me.uv_layers: me.uv_layers.remove(me.uv_layers['TorsoUV'])
me.uv_layers.new(name='TorsoUV')
loops = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loops)
tu = np.zeros((len(me.loops), 2), np.float32)
for p in me.polygons:
    if torso[p.index]:
        for li in p.loop_indices: tu[li] = tmap[(p.index, int(loops[li]))]
me.uv_layers['TorsoUV'].data.foreach_set('uv', tu.ravel())
me.attributes.new('torso', 'INT', 'FACE').data.foreach_set('value', torso.astype(np.int32).tolist())
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
# upload: whole figure, TorsoUV active (other faces at the collapsed point 0,0)
d = body.copy(); d.data = me.copy(); d.modifiers.clear(); d.parent = None; d.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(d); dd = d.data
for g in list(d.vertex_groups): d.vertex_groups.remove(g)
dd.uv_layers['UVMap'].data.foreach_set('uv', tu.ravel())
dd.uv_layers.remove(dd.uv_layers['HeadUV']); dd.uv_layers.remove(dd.uv_layers['TorsoUV'])
for a in [a.name for a in dd.attributes if a.name in ('part', 'head', 'torso')]: dd.attributes.remove(dd.attributes[a])
dd.materials.clear(); dd.materials.append(bpy.data.materials.new('m'))
for o in bpy.data.objects: o.select_set(o is d)
bpy.context.view_layer.objects.active = d
bpy.ops.export_scene.gltf(filepath=UP, export_format='GLB', use_selection=True, export_animations=False, export_skins=False, export_yup=True, export_attributes=False, export_materials='EXPORT')
json.dump(rep, open(REP, 'w'), indent=1, default=str)
print('UVDONE')
