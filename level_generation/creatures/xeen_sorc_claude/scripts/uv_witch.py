"""Witch body UVs for the 4K Meshy paint (claude_shared/TEXTURE_QUALITY_PASS.md section 0): claude_shared/uv_atlas.py
defaults (PartUV charts from the skin weights, seam pass, sparrow packing) on the final reduced, weighted body of the
gated master, in the bind pose. The face is the gold horned mask (hard surface, ornate, the creature's identity) and
gets twice the body's texel density through a 'FaceMask' vertex group (body skin with head weight > 0.5 in front of
the ears + the mask crown, jaw piece and forehead gem); the white mane cards keep the body density. One 2K set, no
separate head set (README: the face is a painted mask, not skin).
Writes <out blend> (UVMap replaced), <upload glb> (neutral static mesh with the UVs, no material) and <report json>.
Args: -- <in blend> <out blend> <upload glb> <report json> [key=value uv_atlas.unwrap options]"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'claude_shared'))
import uv_atlas
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT = [os.path.abspath(x) for x in argv[:4]]
options = {k: (float(v) if v.replace('.', '', 1).isdigit() and '.' in v else int(v) if v.isdigit() else v)
           for k, v in (a.split('=', 1) for a in argv[4:])}
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['Rig']; mesh = bpy.data.objects['Body']; me = mesh.data
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
if any(len(p.vertices) != 3 for p in me.polygons):
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    print('UV triangulated quads')
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
hi = mesh.vertex_groups['B_Head'].index
co = np.array([tuple(v.co) for v in me.vertices])
hw = np.zeros(len(me.vertices))
for v in me.vertices:
    for e in v.groups:
        if e.group == hi:
            hw[v.index] = e.weight
head = np.array(rig.data.bones['B_Head'].head_local)
face = ((gv == 0) & (hw > 0.5) & (co[:, 1] < head[1] + 0.02)) | (gv == 2)
g = mesh.vertex_groups.get('FaceMask') or mesh.vertex_groups.new(name='FaceMask')
g.add([int(i) for i in np.where(face)[0]], 1.0, 'REPLACE')
print('UV face-mask vertices', int(face.sum()))
report = uv_atlas.unwrap(mesh, head_groups=('FaceMask',), head_factor=2.0, **options)
mesh.vertex_groups.remove(mesh.vertex_groups['FaceMask'])
print('UV_ATLAS', json.dumps(report)[:1500])
json.dump(report, open(REPORT, 'w'), indent=1)
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
