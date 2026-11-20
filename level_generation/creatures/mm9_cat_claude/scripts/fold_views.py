"""Close review renders of a runtime GLB at viewer frames (48 fps): textured and plain clay (creases read better).

Args: <glb> <outdir> <shot> [<shot> ...]
A shot is name:clip:frame:view:ortho[:cx:cy:cz] with frame at 48 fps (the viewer's frame counter) and view one of
front, back, left, right, q34, q34r, under (Blender axes after import: the wolf faces -Y). Writes <name>_tex.png and
<name>_clay.png. Env BONES / MARK add a vertex-colour render (see below). Env SIZE (default 420), SKIN (material image name substring for tier renders, optional).
"""
import bpy, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir, shots = argv[0], argv[1], argv[2:]
size = int(os.environ.get('SIZE', '420'))
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 48
sc.render.fps_base = 1
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in sc.objects:
    if o.type == 'MESH':
        nm = o.name.lower() + ' ' + o.data.name.lower()
        o.hide_render = ('lod' in nm and 'lod0' not in nm) or 'shadow' in nm or o.name.startswith('Icosphere')
# optional weight colours: BONES="Bone16=1,0,0;Bone32=0,0,1" (other bones grey) -> <name>_w.png
BONES = [(b.split('=')[0], tuple(float(x) for x in b.split('=')[1].split(','))) for b in
         os.environ.get('BONES', '').split(';') if '=' in b]
if BONES:
    for o in sc.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        gi = {g.index: g.name for g in o.vertex_groups}
        col = o.data.color_attributes.new('wcol', 'FLOAT_COLOR', 'POINT')
        lut = dict(BONES)
        for v in o.data.vertices:
            c = [0.0, 0.0, 0.0]
            for g in v.groups:
                rgb = lut.get(gi[g.group], (0.35, 0.35, 0.35))
                for k in range(3):
                    c[k] += g.weight * rgb[k]
            col.data[v.index].color = (*c, 1.0)
        o.data.color_attributes.active_color = col
# optional marks: MARK=<npy of GLB rest positions as Blender (x, -z, y)> -> those vertices red in <name>_mark.png
MARK = os.environ.get('MARK', '')
if MARK:
    import numpy as np
    from mathutils.kdtree import KDTree
    pts = np.load(MARK)
    for o in sc.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        kd = KDTree(len(o.data.vertices))
        for v in o.data.vertices:
            kd.insert(v.co, v.index)   # mesh-local rest = the GLB positions (y up -> z up)
        kd.balance()
        hit = set()
        for p in pts:
            for _, i, dist in kd.find_range(Vector(tuple(p)), 1e-4):
                hit.add(i)
        col = o.data.color_attributes.new('mark', 'FLOAT_COLOR', 'POINT')
        for v in o.data.vertices:
            col.data[v.index].color = (0.95, 0.1, 0.1, 1) if v.index in hit else (0.75, 0.72, 0.68, 1)
        o.data.color_attributes.active_color = col
        print('MARKED', len(hit), 'of', len(pts))
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading
sh.light = 'STUDIO'
sh.show_backface_culling = True
sh.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w')
sc.world = w
cd = bpy.data.cameras.new('cam')
cd.type = 'ORTHO'
cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd)
sc.collection.objects.link(cam)
sc.camera = cam
dirs = {'front': Vector((0, -1, 0.15)), 'back': Vector((0, 1, 0.15)), 'left': Vector((1, 0, 0.1)),
        'right': Vector((-1, 0, 0.1)), 'q34': Vector((-0.8, -1, 0.3)), 'q34r': Vector((0.8, -1, 0.3)),
        'under': Vector((0.0, -0.6, -1.0)), 'side_low': Vector((-1, -0.3, -0.35)),
        'side_low_r': Vector((1, -0.3, -0.35))}
for spec in shots:
    parts = spec.split(':')
    name, clip, frame, view, ortho = parts[0], parts[1], float(parts[2]), parts[3], float(parts[4])
    centre = Vector(tuple(float(x) for x in parts[5:8])) if len(parts) >= 8 else Vector((0, 0, 0.4))
    act = bpy.data.actions[clip]
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f = act.frame_range[0] + frame
    sc.frame_set(int(f), subframe=f - int(f))
    cd.ortho_scale = ortho
    d = dirs[view].normalized()
    cam.location = centre + d * 10
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for mode in ('TEXTURE', 'SINGLE') + (('VERTEX',) if BONES or MARK else ()):
        sh.color_type = mode
        sh.single_color = (0.78, 0.74, 0.68)
        sc.render.filepath = os.path.join(outdir, f"{name}_{dict(TEXTURE='tex', SINGLE='clay', VERTEX='mark' if MARK else 'w')[mode]}.png")
        bpy.ops.render.render(write_still=True)
print('FOLD_VIEWS done', len(shots))
