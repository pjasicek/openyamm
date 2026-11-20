"""Close-up review renders of a GLB at viewer times (48 fps frames), Workbench textured, perspective-free ortho.

Args: <glb> <outdir> <prefix> <shot> [<shot> ...]
shot = name:clip:frame48:view:target:ortho  (clip '-' = bind pose; target 'eyes' (upper eyeballs), 'mouth' (teeth),
       'belly' (pelvis area) or x,y,z in Blender coordinates; views as render_views.py plus 'below' (front, from
       below) and 'q34l'/'q34' three-quarters).
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, shots = argv[0], argv[1], argv[2], argv[3:]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and o.name != 'Terror':
        o.hide_render = True
body = bpy.data.objects['Terror']
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
fps = sc.render.fps / sc.render.fps_base
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError as e:
    print(e)
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'TEXTURE'
sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 640
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); w.color = (0.35, 0.36, 0.38); sc.world = w
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.35)), 'q34l': Vector((1.0, -1.25, 0.35)), 'front': Vector((0, -1, 0.12)),
        'below': Vector((0, -1, -0.45)), 'left': Vector((1, -0.15, 0.05)), 'right': Vector((-1, -0.15, 0.05))}
# shells of the bind mesh, for targets
me = body.data
n = len(me.vertices)
P0 = np.array([v.co[:] for v in me.vertices])
key = np.round(P0, 5)
_, weld = np.unique(key, axis=0, return_inverse=True)
weld = weld.ravel()
par = np.arange(weld.max() + 1)


def find(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a


for e in me.edges:
    a, b = find(weld[e.vertices[0]]), find(weld[e.vertices[1]])
    if a != b:
        par[a] = b
shell = np.array([find(x) for x in weld])
ids, cnt = np.unique(shell, return_counts=True)
main = ids[cnt.argmax()]
small = [np.nonzero(shell == s)[0] for s in ids if s != main]
eyes = [v for v in small if len(v) >= 60 and np.ptp(P0[v], 0).max() / max(np.ptp(P0[v], 0).min(), 1e-6) < 1.3]
teeth = np.concatenate([v for v in small if not any(v is e for e in eyes)])
upper_eyes = np.concatenate(sorted(eyes, key=lambda v: -P0[v][:, 2].mean())[:2])


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    m = ev.to_mesh()
    P = np.array([body.matrix_world @ v.co for v in m.vertices])
    ev.to_mesh_clear()
    return P


for s in shots:
    name, clip, f48, view, target, ortho = s.split(':')
    if clip == '-':
        if arm.animation_data:
            arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.matrix_basis.identity()
    else:
        act = bpy.data.actions[clip]
        arm.animation_data_create()
        arm.animation_data.action = act
        try:
            arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        f = float(f48) / 48 * fps + act.frame_range[0]
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    bpy.context.view_layer.update()
    P = evaluated()
    if target == 'eyes':
        c = Vector(P[upper_eyes].mean(0)) + Vector((0, 0, -0.08))
    elif target == 'mouth':
        c = Vector(P[teeth].mean(0))
    elif target == 'belly':
        c = Vector((P[:, 0].mean(), P[:, 1].mean(), 0.95))
    else:
        c = Vector([float(x) for x in target.split(',')])
    cd.ortho_scale = float(ortho)
    d = dirs[view].normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{name}.png')
    bpy.ops.render.render(write_still=True)
print('SHOTS', prefix, len(shots))
