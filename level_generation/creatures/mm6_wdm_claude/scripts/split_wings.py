"""Classify wing vertices of the Meshy Smart Topology mesh (raw Meshy frame: x left/right, -y front, z up, height
~0.63). Wing = connected region (through mesh edges) of vertices behind the back plane (y > Y_BACK), off the spine
ridge (|x| > X_SPINE), above the tail spike (z > Z_MIN), root above the hips, seeded by the outer membrane (|x| > 0.3),
then grown into the leading-edge strut/hook above the shoulders.
Writes work/wing_mask.npy (bool per vertex, in Meshy vertex order), meshy_upload/body_only.glb (wing faces deleted,
for a clean Meshy auto-rig) and review/wing_split_<view>.png."""
import bpy, bmesh, os, sys, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Y_BACK, X_SPINE, Z_MIN, SEED_X = -0.035, 0.035, -0.02, 0.3
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = mesh.data
co = np.array([tuple(v.co) for v in me.vertices])
cand = (co[:, 1] > Y_BACK) & (np.abs(co[:, 0]) > X_SPINE) & (co[:, 2] > Z_MIN)
cand &= (np.abs(co[:, 0]) > 0.15) | (co[:, 2] > 0.07)          # wing root stays above the hips
adj = [[] for _ in range(len(co))]
for e in me.edges:
    a, b = e.vertices
    adj[a].append(b); adj[b].append(a)
wing = np.zeros(len(co), bool)
stack = [i for i in np.nonzero(cand & (np.abs(co[:, 0]) > SEED_X))[0]]
for i in stack:
    wing[i] = True
while stack:
    a = stack.pop()
    for b in adj[a]:
        if cand[b] and not wing[b]:
            wing[b] = True; stack.append(b)
# The leading-edge strut and the top hook curl forward past the back plane: grow the wing through connected
# vertices in the upper-outer zone (above the shoulders, away from the torso; spikes are separate pieces).
outer = (co[:, 2] > 0.21) & (np.abs(co[:, 0] + 0.00875) > 0.0875)
stack = list(np.nonzero(wing)[0])
while stack:
    a = stack.pop()
    for b in adj[a]:
        if outer[b] and not wing[b]:
            wing[b] = True; stack.append(b)
# Within the torso width the membrane sheet IS the back skin (Meshy built no separate back surface): keep it body.
wing &= np.abs(co[:, 0] + 0.00875) > 0.0455          # 0.13 m from the midline in the rig frame
print('WING verts', int(wing.sum()), 'of', len(co))
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
np.save(os.path.join(HERE, 'work', 'wing_mask.npy'), wing)

# Review renders: wing red, body grey.
col = me.color_attributes.new('split', 'FLOAT_COLOR', 'POINT')
for i, w in enumerate(wing):
    col.data[i].color = (0.9, 0.2, 0.2, 1) if w else (0.75, 0.75, 0.75, 1)
me.color_attributes.active_color = col
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x, sc.render.resolution_y = 800, 520
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.1
os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
for name, d in (('front', (0, 1, 0)), ('back', (0, -1, 0)), ('side', (-1, 0, 0)), ('top', (0, 0.15, -1))):
    d = Vector(d).normalized(); cam.location = -d * 5
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review', f'wing_split_{name}.png'); bpy.ops.render.render(write_still=True)
me.color_attributes.remove(col)

# Wingless body for the Meshy auto-rig.
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(wing)[0]], context='VERTS')
bm.to_mesh(me); bm.free()
os.makedirs(os.path.join(HERE, 'meshy_upload'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'meshy_upload', 'body_only.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE')
print('BODY verts', len(me.vertices))
