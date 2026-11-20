"""UVs: claude_shared/uv_atlas.py on the whole body (2K, hands denser, linings thin, skull faces thin: the skull has its own
set) and on the skull alone (HeadUV, 0..1). Writes the two neutral uploads. Never re-run after an upload went to Meshy.
Args: <in blend> <out blend> <body upload glb> <head upload glb> <report json> [key=value uv_atlas options]"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UP_BODY, UP_HEAD, REPORT = argv[:5]
options = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in (a.split('=', 1) for a in argv[5:])}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
n = len(me.polygons)
part = np.zeros(n, np.int32); me.attributes['part'].data.foreach_get('value', part)
HEAD = part == 30; LINE = np.isin(part, (40, 41, 42)); HAND = np.isin(part, (3, 10))
print('FACES', n, 'head', HEAD.sum(), 'lining', LINE.sum(), 'hand', HAND.sum())


def vgroup(name, mask):
    g = body.vertex_groups.new(name=name)
    g.add(sorted({v for p, m in zip(me.polygons, mask) if m for v in p.vertices}), 1.0, 'REPLACE')


vgroup('TP_skull', HEAD); vgroup('TP_line', LINE); vgroup('TP_hand', HAND)


def single(mask, path, keep_uv=True):
    """static neutral GLB of the chosen faces"""
    d = body.copy(); d.data = me.copy(); d.modifiers.clear(); d.parent = None; d.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(d)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(d.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not mask[f.index]], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(d.data); bm.free(); d.data.update()
    d.vertex_groups.clear()
    return d


def export(d, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for o in bpy.data.objects:
        o.select_set(o == d)
    bpy.context.view_layer.objects.active = d
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                              export_animations=False, export_materials='NONE', export_attributes=False)


report = {}
report['body'] = uv_atlas.unwrap(body, group_factors={'TP_skull': 0.25, 'TP_line': 0.4, 'TP_hand': 1.5}, **options)
for g in ('TP_skull', 'TP_line', 'TP_hand'):
    body.vertex_groups.remove(body.vertex_groups[g])
me = body.data
# skull alone
dh = single(HEAD, None)
fi = dh.data.attributes.get('fid')
report['head'] = uv_atlas.unwrap(dh, **options)
# carry the skull's UVs into HeadUV of the master, face by face (faces keep their order within the skull)
hu = me.uv_layers.new(name='HeadUV')
idx = np.nonzero(HEAD)[0]
assert len(idx) == len(dh.data.polygons)
for k, p in enumerate(dh.data.polygons):
    q = me.polygons[int(idx[k])]
    pos = {tuple(np.round(dh.data.vertices[dh.data.loops[l].vertex_index].co, 5)): tuple(dh.data.uv_layers['UVMap'].data[l].uv) for l in p.loop_indices}
    for l in q.loop_indices:
        hu.data[l].uv = pos[tuple(np.round(me.vertices[me.loops[l].vertex_index].co, 5))]
export(dh, UP_HEAD)
bpy.data.objects.remove(dh)
# body upload without the linings (they are filled from the outer paint in compose)
db = single(~LINE, None)
export(db, UP_BODY)
bpy.data.objects.remove(db)
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers['UVMap'].active_render = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REPORT, 'w'), indent=1)
print('UV', json.dumps(report)[:900])
