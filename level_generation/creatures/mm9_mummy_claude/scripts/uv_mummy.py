"""UVs: uv_atlas.py on the body faces (2K, hands denser, top 8 % of the square left free for the strip swatch) and on the head alone (HeadUV, 0..1). Writes the neutral body upload.
Never re-run after an upload went to Meshy. Args: <in blend> <out blend> <body upload glb> <report json> <work npz>"""
import bpy, sys, os, json, bmesh
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, OUT, UP, REPORT, NPZ = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
for o in bpy.data.objects: o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
n = len(me.polygons)
head = np.zeros(n, np.int32); me.attributes['head'].data.foreach_get('value', head); head = head == 1
def single(mask):
    d = ob.copy(); d.data = me.copy(); d.modifiers.clear(); bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not mask[f.index]], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(d.data); bm.free(); d.data.update(); d.vertex_groups.clear(); return d
dh = single(head); db = single(~head)
# hands 1.4x
co = np.array([tuple(v.co) for v in db.data.vertices])
g = db.vertex_groups.new(name='hand'); g.add(np.where(np.abs(co[:, 0]) > 0.47)[0].tolist(), 1.0, 'REPLACE')
for o in bpy.data.objects: o.select_set(o == db)
bpy.context.view_layer.objects.active = db
rep = {}
rep['body'] = uv_atlas.unwrap(db, group_factors={'hand': 1.4}, height_share=0.915, fine=250, steps=0)
for o in bpy.data.objects: o.select_set(o == dh)
bpy.context.view_layer.objects.active = dh
rep['head'] = uv_atlas.unwrap(dh, fine=250, steps=0)
json.dump(rep, open(REPORT, 'w'), indent=1, default=float)
print('UVS', rep)
def dump(d):
    me_ = d.data
    bm = bmesh.new(); bm.from_mesh(me_); uvl = bm.loops.layers.uv.active; bmesh.ops.triangulate(bm, faces=bm.faces)
    pos = []; uv = []
    for f in bm.faces:
        for l in f.loops: pos.append(tuple(l.vert.co)); uv.append(tuple(l[uvl].uv))
    bm.free(); return np.array(pos), np.array(uv)
pb, ub = dump(db); ph, uh = dump(dh)
np.savez(NPZ, pb=pb, ub=ub, ph=ph, uh=uh)
for o in bpy.data.objects: o.select_set(o == db)
bpy.context.view_layer.objects.active = db
db.vertex_groups.clear()
os.makedirs(os.path.dirname(UP), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UP, use_selection=True, export_format='GLB', export_yup=True, export_skins=False, export_animations=False, export_materials='NONE', export_attributes=False)
db.name = 'BodyUV'; dh.name = 'HeadUV'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('UV DONE')
