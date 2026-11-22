"""Sorceress UVs for ONE 4K Meshy paint that yields a body set and a separate head set
(claude_shared/TEXTURE_QUALITY_PASS.md section 0, CLAUDE_CREATURE_TEXTURES.md "Head detail").
The gated master (bind pose, final reduced weighted body) is welded once, then split by face into
- HEAD: the skin faces whose three vertices carry B_Head weight > 0.5 (face, ears, scalp under the mane, above the
  choker) and the head pieces (garment 2: eyes, lips, circlet, earrings);
- BODY: everything else (skin, halter, gloves, boots, mane and curls, caps, choker, girdle, panels).
Each part is laid out with claude_shared/uv_atlas.py defaults (PartUV charts, seam pass, sparrow packing, 2048 square,
the other part as a visibility occluder) and the two squares share one upload: BODY in u 0..0.5, HEAD in u 0.5..1,
both in v 0..0.5 (the top half stays empty). Meshy paints that at 4K, so each set gets a 2048 square, downsampled once
to 1K (body 1K + head 1K: the head-set rule; merge_head_material.py later puts them side by side again).
The faces keep a 'headset' face attribute (1 = head). Writes <out blend> (UVMap = the combined upload layout),
<upload glb> (neutral static mesh, no material) and <report json> (both unwrap reports).
Args: -- <in blend> <out blend> <upload glb> <report json>"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'claude_shared'))
import uv_atlas
IN, OUT, UPLOAD, REPORT = [os.path.abspath(x) for x in sys.argv[sys.argv.index('--') + 1:]]
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['Rig']; mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = mesh.data
if any(len(p.vertices) != 3 for p in me.polygons):
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    print('UV triangulated quads')
print('UV weld', uv_atlas._weld(mesh, 1e-5))
me = mesh.data
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
hi = mesh.vertex_groups['B_Head'].index
hw = np.zeros(len(me.vertices))
for v in me.vertices:
    for e in v.groups:
        if e.group == hi:
            hw[v.index] = e.weight
headv = ((gv == 0) & (hw > 0.5)) | (gv == 2)
hf = np.array([all(headv[i] for i in p.vertices) for p in me.polygons])
# whole head pieces: a garment-2 piece is head even where one vertex is light (rigid head anyway)
fa = me.attributes.get('headset') or me.attributes.new('headset', 'INT', 'FACE')
fa.data.foreach_set('value', hf.astype(np.int32))
fid = me.attributes.get('fid') or me.attributes.new('fid', 'INT', 'FACE')
fid.data.foreach_set('value', np.arange(len(me.polygons), dtype=np.int32))
print('UV head faces', int(hf.sum()), 'body faces', int((~hf).sum()))


def part(keep_head):
    dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
    dup.matrix_world = mesh.matrix_world; dup.name = 'HEADPART' if keep_head else 'BODYPART'
    bpy.context.scene.collection.objects.link(dup)
    bm = bmesh.new(); bm.from_mesh(dup.data)
    lay = bm.faces.layers.int['headset']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if bool(f[lay]) != keep_head], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(dup.data); bm.free(); dup.data.update()
    return dup


H, B = part(True), part(False)
rep = {}
for name, ob, other in (('head', H, B), ('body', B, H)):
    r = uv_atlas.unwrap(ob, weld=0, vis_objects=(other,))
    rep[name] = r
    print('UV_ATLAS', name, json.dumps({k: r.get(k) for k in ('charts_used', 'packer_used', 'fallbacks', 'atlas', 'islands')})[:600])
# combined layout on the master: body square -> u 0..0.5, head square -> u 0.5..1, v 0..0.5
for layer in list(me.uv_layers):
    me.uv_layers.remove(layer)
me.uv_layers.new(name='UVMap')
flat = np.zeros((len(me.loops), 2), np.float32)
for ob, du in ((B, 0.0), (H, 0.5)):
    m = ob.data; uvl = m.uv_layers['UVMap'].data
    fids = np.zeros(len(m.polygons), np.int32); m.attributes['fid'].data.foreach_get('value', fids)
    for p, f in zip(m.polygons, fids):
        src = me.polygons[int(f)]
        assert len(src.loop_indices) == len(p.loop_indices)
        for li_dst, li_src in zip(src.loop_indices, p.loop_indices):
            u, v = uvl[li_src].uv
            flat[li_dst] = (u * 0.5 + du, v * 0.5)
me.uv_layers['UVMap'].data.foreach_set('uv', flat.ravel())
for ob in (H, B):
    bpy.data.objects.remove(ob, do_unlink=True)
json.dump(rep, open(REPORT, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = mesh.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UV done; upload', UPLOAD, len(me.polygons))
