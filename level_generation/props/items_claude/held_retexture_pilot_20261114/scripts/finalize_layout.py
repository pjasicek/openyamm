"""Step 1c of the held-sword retexture pilot (README.md): give the laid-out mesh the source's exact shading back and
write the files the paint needs.

The welds in prep.py / uv_atlas keep every face and vertex position; only vertex sharing changes. Each new face is
matched to its source face by its corner positions and each corner takes the source corner's normal, so the hard edges
of the source stay where they were (a nearest-surface data transfer smeared them on the thin blades).

Usage: blender --background --python finalize_layout.py -- <icon> <tag>
Reads work/<icon>/uv_<tag>.blend and the source GLB; writes work/<icon>/layout.blend (locked layout), layout_measure.glb,
upload.glb (upright, for Meshy) and guide_{front,back,left,right}.png.
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
argv = sys.argv[sys.argv.index('--') + 1:]
ICON, TAG = argv[0], argv[1]
OUT = os.path.join(PROJECT, 'work', ICON)
SRC = os.path.join(REPO, 'assets_source', 'engine', 'world_items', 'models', f'item_{ICON}.glb')

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, f'uv_{TAG}.blend'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
bpy.ops.import_scene.gltf(filepath=SRC)
src = next(o for o in bpy.data.objects if o.type == 'MESH' and o is not obj)
sm = src.data
sm.transform(src.matrix_world)
spos = np.array([v.co for v in sm.vertices])
key = lambda p: tuple(np.round(p, 5))
by_corners = {}
for p in sm.polygons:
    pts = [key(spos[v]) for v in p.vertices]
    by_corners[tuple(sorted(pts))] = p
me = obj.data
pos = np.array([v.co for v in me.vertices])
normals = []
missing = 0
for p in me.polygons:
    pts = [key(pos[v]) for v in p.vertices]
    sp = by_corners.get(tuple(sorted(pts)))
    for li, v in zip(p.loop_indices, p.vertices):
        if sp is None:
            normals.append(tuple(p.normal)); continue
        k = key(pos[v])
        for sl, sv in zip(sp.loop_indices, sp.vertices):
            if key(spos[sv]) == k:
                normals.append(tuple(sm.loops[sl].normal)); break
        else:
            normals.append(tuple(p.normal))
    missing += sp is None
me.normals_split_custom_set(normals)
me.update()
fn = np.array([p.normal[:] for p in me.polygons])
idx = np.concatenate([[p.index] * p.loop_total for p in me.polygons])
ln = np.array([l.normal[:] for l in me.loops])
dot = (ln * fn[idx]).sum(1)
print('FINAL normals: faces unmatched', missing, 'of', len(me.polygons), '; loops dot<0.5:', int((dot < 0.5).sum()))
bpy.data.objects.remove(src)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'layout.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'layout_measure.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False)
R = json.load(open(os.path.join(OUT, 'orient.json')))['rotation_blender']
me.materials.clear()
me.transform(Matrix(R).to_4x4())
me.update()
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_materials='NONE')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.6, 0.6, 0.6)
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 1024, 1536
scene.view_settings.view_transform = 'Standard'
co = np.array([v.co for v in me.vertices])
ctr = Vector(((co.max(0) + co.min(0)) / 2).tolist())
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = float(np.ptp(co[:, 2])) / 0.88
cam.data.clip_end = 100
scene.camera = cam
views = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'left': Vector((1, 0, 0)), 'right': Vector((-1, 0, 0))}
for name, d in views.items():
    cam.location = ctr + d * 10
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'guide_{name}.png')
    bpy.ops.render.render(write_still=True)
print('FINAL done', ICON, TAG)
