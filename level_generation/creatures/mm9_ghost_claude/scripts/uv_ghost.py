"""UVs (uv_atlas.py) on Body (hands denser) and on Head alone, neutral uploads for the two 4K retextures. Never re-run after an upload went to Meshy: the paints belong to these layouts.
Args: <in blend> <out blend> <body upload glb> <head upload glb> <report json> [key=value options]"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UP_BODY, UP_HEAD, REPORT = argv[:5]
options = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in (a.split('=', 1) for a in argv[5:])}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; head = bpy.data.objects['Head']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
for o in (body,):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='FIXED')
    bm.to_mesh(o.data); bm.free(); o.data.update()
me = body.data


def select(o):
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.context.view_layer.objects.active = o


n = len(me.polygons)
hand = np.zeros(n, np.int32); me.attributes['hand'].data.foreach_get('value', hand)
g = body.vertex_groups.new(name='TP_hand')
g.add(sorted({v for p, m in zip(me.polygons, hand) if m for v in p.vertices}), 1.0, 'REPLACE')
print('FACES', n, 'hand', hand.sum())
report = {}
select(body)
report['body'] = uv_atlas.unwrap(body, group_factors={'TP_hand': 1.45}, **options)
body.vertex_groups.remove(body.vertex_groups['TP_hand'])
select(head)
report['head'] = uv_atlas.unwrap(head, **options)


def export(o, path):
    d = o.copy(); d.data = o.data.copy(); d.modifiers.clear(); d.parent = None; d.matrix_world = o.matrix_world
    d.vertex_groups.clear()
    bpy.context.scene.collection.objects.link(d)
    select(d)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                              export_animations=False, export_materials='NONE', export_attributes=False)
    bpy.data.objects.remove(d)


export(body, UP_BODY); export(head, UP_HEAD)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REPORT, 'w'), indent=1, default=float)
print('UV', json.dumps(report, default=float)[:1200])
