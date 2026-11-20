"""Step 1 of the held-sword retexture pilot (README.md): new UVs on the installed ground model, the Meshy upload and the
guides for the Codex HD masters. Geometry, scale and orientation stay those of the installed source.

Usage: blender --background --python prep.py -- <icon> [key=value uv_atlas.unwrap options]

Reads assets_source/engine/world_items/models/item_<icon>.glb and writes into work/<icon>/:
  uv.blend            the mesh with the new UVs (locked: never re-run once the upload went to Meshy)
  uv_report.json      uv_atlas report
  uv_measure.glb      original orientation, new UVs, a grey 2048 placeholder base colour (texture_quality.py input)
  upload.glb          the same mesh stood upright for Meshy: tip up (+Y glTF), blade face toward +Z (Meshy front)
  guide_{front,left,back,right}.png  plain grey orthographic renders of upload.glb, 1024 x 1536, transparent
  orient.json         the rotation from the source to the upload frame
"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
ICON = argv[0]
options = {}
for a in argv[1:]:
    k, v = a.split('=', 1)
    try:
        options[k] = int(v)
    except ValueError:
        try:
            options[k] = float(v)
        except ValueError:
            options[k] = v
SRC = os.path.join(REPO, 'assets_source', 'engine', 'world_items', 'models', f'item_{ICON}.glb')
OUT = os.path.join(PROJECT, 'work', ICON)
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
assert len(meshes) == 1, [o.name for o in meshes]
obj = meshes[0]
obj.data.transform(obj.matrix_world)
obj.matrix_world = Matrix.Identity(4)
bm = bmesh.new(); bm.from_mesh(obj.data)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(obj.data); bm.free()

# The source's shading (split normals) is kept: a copy before the weld gives its normals back afterwards.
orig = obj.copy(); orig.data = obj.data.copy(); orig.name = 'orig_normals'
bpy.context.scene.collection.objects.link(orig)
orig.hide_render = True

# Weld here: uv_atlas refuses a weld that reorders faces (item001, 7item010), which leaves hundreds of fragments. Face
# order does not matter for a static prop whose normals come back by position; faces the weld collapses are dropped.
bm = bmesh.new(); bm.from_mesh(obj.data)
n0 = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(obj.data); bm.free()
print('PREP weld', n0, '->', len(obj.data.vertices), 'vertices,', len(obj.data.polygons), 'tris', flush=True)

report = uv_atlas.unwrap(obj, **options)
json.dump(report, open(os.path.join(OUT, 'uv_report.json'), 'w'), indent=1)
print('UV_REPORT', json.dumps({k: report[k] for k in report if k in ('atlas', 'charts_used', 'packer_used',
                                                                    'fallbacks', 'islands', 'scale')}))

mod = obj.modifiers.new('normals', 'DATA_TRANSFER')
mod.object = orig
mod.use_loop_data = True
mod.data_types_loops = {'CUSTOM_NORMAL'}
mod.loop_mapping = 'POLYINTERP_NEAREST'
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier=mod.name)
for o in bpy.data.objects:
    o.select_set(o == obj)

# Orientation of the blade: long axis, tip end (the far side from the guard, the widest slice), flat face axis.
co = np.array([v.co for v in obj.data.vertices])
ext = co.max(0) - co.min(0)
order = np.argsort(ext)
long_ax, wide_ax, thin_ax = int(order[2]), int(order[1]), int(order[0])
lo, hi = co[:, long_ax].min(), co[:, long_ax].max()
bins = np.linspace(lo, hi, 41)
widths = [np.ptp(co[(co[:, long_ax] >= a) & (co[:, long_ax] <= b), wide_ax]) if
          ((co[:, long_ax] >= a) & (co[:, long_ax] <= b)).sum() > 2 else 0 for a, b in zip(bins[:-1], bins[1:])]
guard = (bins[int(np.argmax(widths))] + bins[int(np.argmax(widths)) + 1]) / 2
tip_sign = 1.0 if (hi - guard) > (guard - lo) else -1.0
# Upload frame (Blender): tip -> +Z, thin (face normal) axis -> -Y (toward the Blender front camera = glTF +Z, Meshy's
# front), the remaining axis -> +-X so the rotation is proper.
R = np.zeros((3, 3))
R[2, long_ax] = tip_sign
R[1, thin_ax] = -1.0
R[0, wide_ax] = 1.0
if np.linalg.det(R) < 0:
    R[0, wide_ax] = -1.0
json.dump({'long_axis': long_ax, 'thin_axis': thin_ax, 'wide_axis': wide_ax, 'tip_sign': tip_sign,
           'rotation_blender': R.tolist(), 'guard': float(guard), 'extent': ext.tolist()},
          open(os.path.join(OUT, 'orient.json'), 'w'), indent=1)

orig_name = obj.name
bpy.data.objects.remove(orig)

# Measurement copy: original orientation, placeholder 2048 base colour.
img = bpy.data.images.new(f'{ICON}_placeholder', 2048, 2048)
img.pixels[:] = np.full(2048 * 2048 * 4, 0.5, np.float32)
img.filepath_raw = os.path.join(OUT, 'placeholder.png'); img.file_format = 'PNG'; img.save()
mat = bpy.data.materials.new('placeholder'); mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
obj.data.materials.clear(); obj.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'uv.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'uv_measure.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False)

# Upload: the same mesh stood upright, no material.
M = Matrix(R.tolist()).to_4x4()
obj.data.materials.clear()
obj.data.transform(M)
obj.data.update()
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_materials='NONE')

# Guides: plain grey orthographic views of the upright mesh, one framing for all four.
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.6, 0.6, 0.6)
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 1024, 1536
scene.view_settings.view_transform = 'Standard'
co = np.array([v.co for v in obj.data.vertices])
ctr = Vector(((co.max(0) + co.min(0)) / 2).tolist())
height = float(np.ptp(co[:, 2]))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = height / 0.88 * 1.0   # ortho_scale spans the larger (vertical) side: 6 % margin top/bottom
cam.data.clip_end = 100
scene.camera = cam
views = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'left': Vector((1, 0, 0)), 'right': Vector((-1, 0, 0))}
for name, d in views.items():
    cam.location = ctr + d * 10
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'guide_{name}.png')
    bpy.ops.render.render(write_still=True)
print('PREP done', ICON, len(obj.data.polygons), 'tris')
