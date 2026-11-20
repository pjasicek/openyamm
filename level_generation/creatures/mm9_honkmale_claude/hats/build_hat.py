"""One hat mesh: Meshy return decimated, seated on the male head (rest pose, master coordinates), UV atlas, clay views for Codex paint.
Args (Blender): <meshy glb> <master blend> <out blend> <out dir> <name> <tris> <scale> <brim z> <dy> [yscale]"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, master, out, od, name, tris, s, zb, dy = a[0], a[1], a[2], a[3], a[4], int(a[5]), float(a[6]), float(a[7]), float(a[8])
ys = float(a[9]) if len(a) > 9 else 1.0
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared')))
import uv_atlas
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
h = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not h:
        for ch in o.children:
            mt = ch.matrix_world.copy(); ch.parent = None; ch.matrix_world = mt
        bpy.data.objects.remove(o)
h.name = 'Hat'
bpy.context.view_layer.objects.active = h; h.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
t0 = sum(len(p.vertices) - 2 for p in h.data.polygons)
dm = h.modifiers.new('D', 'DECIMATE'); dm.ratio = min(1, tris / t0); dm.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=dm.name)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
co = np.array([tuple(v.co) for v in h.data.vertices])
# brim: height of the widest band
zs = np.linspace(co[:, 2].min(), co[:, 2].max(), 60)
wid = [np.ptp(co[np.abs(co[:, 2] - z) < .02, 0]) if (np.abs(co[:, 2] - z) < .02).sum() > 2 else 0 for z in zs]
if name == 'goose':
    zbrim = co[:, 2].min()
else:
    zbrim = float(sys.argv and json.loads(os.environ.get('HAT_BRIM_Z', '-0.13')))
ring = co[np.abs(co[:, 2] - zbrim) < .03]
cx, cy = 0.5 * (ring[:, 0].min() + ring[:, 0].max()), 0.5 * (ring[:, 1].min() + ring[:, 1].max())
q = (co - np.array([cx, cy, zbrim])) * s
q[:, 1] *= ys
q += np.array([0, dy, zb])
for v, p in zip(h.data.vertices, q):
    v.co = Vector(p.tolist())
rep = uv_atlas.unwrap(h, fine=250, steps=0)
print('HATUV', json.dumps({k: rep[k] for k in ('use', 'charts')}), 'lo', q.min(0).round(3).tolist(), 'hi', q.max(0).round(3).tolist())
bpy.ops.wm.save_as_mainfile(filepath=out)
# clay views with the male head for scale, unlit-ish
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .72, .72); sh.show_cavity = False; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 1254; sc.render.film_transparent = True
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(np.ptp(q, 0).max()) * 1.15; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector(((q.min(0) + q.max(0)) / 2).tolist())
json.dump({'centre': list(c), 'ortho': cd.ortho_scale}, open(f'{od}/{name}_cam.json', 'w'))
for n, deg in (('front', 0), ('q34', 40), ('side', 90), ('sidem', -90), ('back', 180), ('backq', 140)):
    r = math.radians(deg); D = Vector((-math.sin(r), -math.cos(r), 0))
    cam.location = c + D * 5; cam.rotation_euler = (-D).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{od}/{name}_{n}.png'; bpy.ops.render.render(write_still=True)
print('HATDONE')
