"""Render a GLB at given clip times (textured, workbench), LOD0 only, camera centred on the posed mesh.

Args: <glb> <jobs.json> [size] [ortho] [view: q34|right|front]
jobs.json: [{"clip": "AttackMelee" | null (bind pose), "time": 0.5, "out": "/abs/path.png"}, ...]
Clip times are seconds; the action is evaluated at subframes of the scene fps.
"""
import bpy, sys, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, JOBS = argv[:2]
SIZE = int(argv[2]) if len(argv) > 2 else 400
ORTHO = float(argv[3]) if len(argv) > 3 else 3.2
VIEW = argv[4] if len(argv) > 4 else 'q34'
DIRS = {'q34': Vector((1.0, -1.1, 0.55)), 'right': Vector((1, 0, 0.1)), 'front': Vector((0, -1, 0.1))}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = []
for o in sc.objects:
    if o.type == 'MESH':
        name = o.name + ' ' + o.data.name
        if 'LOD1' in name or 'LOD2' in name or 'LOD3' in name or 'Shadow' in name or o.name.startswith('Icosphere'):
            o.hide_render = True
        else:
            meshes.append(o)
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'TEXTURE'
sh.show_backface_culling = False
sc.view_settings.exposure = 1.3  # the charcoal skins read better a little brighter
sc.render.resolution_x = sc.render.resolution_y = SIZE
w = bpy.data.worlds.new('w'); sc.world = w
w.color = (0.24, 0.25, 0.27)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ORTHO; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
fps = sc.render.fps / sc.render.fps_base
for job in json.load(open(JOBS)):
    arm.animation_data_create()
    if job['clip'] is None:
        arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        act = bpy.data.actions[job['clip']]
        arm.animation_data.action = act
        try:
            arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        f = act.frame_range[0] + job['time'] * fps
        f = min(f, act.frame_range[1])
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        me = o.evaluated_get(dg).to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    d = DIRS[VIEW].normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = job['out']
    bpy.ops.render.render(write_still=True)
print('RENDERED', len(json.load(open(JOBS))))
