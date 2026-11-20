"""Installed vs lined from outside (Blender): both GLBs' LOD0 posed at the same clip frames, rendered with their textures,
back faces culled as in the game, white background, no anti-aliasing. Per spec writes <name>.png: installed | lined |
difference, where the difference is black where both match, yellow where the installed pixel was a see-through hole
(only back faces along the ray: the change a lining should make) and magenta for any other change (a lining seen from
outside, or anything else that moved). Prints the counts.
Args: <installed glb> <lined glb> <out dir> <spec> [...] [px_mm=3] [zoom=cx,cy,half in metres of the image plane]
  spec = name:clip:frame30:azimuth:elevation[:cx,cy,half]"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
GA, GB, OUT = a[0], a[1], a[2]
specs = [x for x in a[3:] if '=' not in x]
opt = dict(x.split('=', 1) for x in a[3:] if '=' in x)
PX = float(opt.get('px_mm', 3.0)) / 1000.0
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path, tag):
    before = set(bpy.data.objects); acts = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == 'ARMATURE')
    mesh = next(o for o in new if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name and 'Shadow' not in o.name)
    for o in new:
        if o.type == 'MESH' and o is not mesh:
            bpy.data.objects.remove(o)
    newacts = {x.name.rsplit('.', 1)[0] if x.name[-4:-3] == '.' else x.name: x for x in bpy.data.actions if x not in acts}
    return rig, mesh, newacts


RA, MA, AA = load(GA, 'A')
RB, MB, AB = load(GB, 'B')
twin = MA.copy(); twin.data = MA.data.copy(); twin.name = 'TwinA'
bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(twin.data); bm.free()
sc = bpy.context.scene
FPS = sc.render.fps / sc.render.fps_base
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.show_backface_culling = True
sc.display.render_aa = 'OFF'; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tmp = os.path.join(OUT, '_tmp'); os.makedirs(tmp, exist_ok=True)


def render(path):
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path); W, H = im.size
    px = np.array(im.pixels[:], np.float32).reshape(H, W, 4); bpy.data.images.remove(im)
    return px


def save(img, path):
    H, W = img.shape[:2]
    im = bpy.data.images.new('S', W, H, alpha=True)
    im.pixels.foreach_set(img.astype(np.float32).ravel())
    im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)


def show(objs):
    for o in (MA, MB, twin):
        o.hide_render = o not in objs


for o in (RA, RB):
    o.animation_data_create()
tot = {}
for spec in specs:
    parts = spec.split(':')
    name, clip, f30, az, el = parts[0], parts[1], int(parts[2]), float(parts[3]), float(parts[4])
    box = [float(x) for x in parts[5].split(',')] if len(parts) > 5 else None
    for rig, acts in ((RA, AA), (RB, AB)):
        act = acts[clip]; rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
    f0 = AA[clip].frame_range[0]
    f = f0 + f30 / 30.0 * FPS
    sc.frame_set(int(f), subframe=f % 1.0)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = MA.evaluated_get(dg); em = ev.to_mesh()
    P = np.array([tuple(ev.matrix_world @ v.co) for v in em.vertices]); ev.to_mesh_clear()
    cen = (P.min(0) + P.max(0)) / 2
    d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)),
                math.sin(math.radians(el))))
    rot = (-d).to_track_quat('-Z', 'Y').to_matrix(); right, up = rot.col[0], rot.col[1]
    if box:
        cx, cy, hw = box
        cen = np.array(cen) + np.array(right) * cx + np.array(up) * cy
        ex = 2 * hw
    else:
        Q = P - cen
        ex = max(np.abs(Q @ np.array(right)).max(), np.abs(Q @ np.array(up)).max()) * 2 + 0.04
    res = int(math.ceil(ex / PX)); cd.ortho_scale = res * PX
    sc.render.resolution_x = sc.render.resolution_y = res
    cam.location = Vector(cen) + d * 4.0; cam.rotation_euler = rot.to_euler()
    sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
    show([MA]); pa = render(os.path.join(tmp, 'a.png'))
    show([MB]); pb = render(os.path.join(tmp, 'b.png'))
    sh.light = 'FLAT'; sh.color_type = 'OBJECT'
    show([MA, twin]); p2 = render(os.path.join(tmp, 'c.png'))
    fa, fb = pa[..., 3] > 0.5, pb[..., 3] > 0.5
    hole = (p2[..., 3] > 0.5) & ~fa
    ia = np.ones_like(pa); ia[fa] = pa[fa]; ia[..., 3] = 1
    ib = np.ones_like(pb); ib[fb] = pb[fb]; ib[..., 3] = 1
    diff = np.abs(ia - ib)[..., :3].max(-1) > 0.02
    dimg = np.zeros_like(ia); dimg[..., 3] = 1
    dimg[diff & hole] = (1.0, 0.85, 0.0, 1.0)
    other = diff & ~hole
    dimg[other] = (1.0, 0.0, 1.0, 1.0)
    save(np.concatenate([ia, ib, dimg], 1), os.path.join(OUT, name + '.png'))
    print('DIFFVIEW', name, 'holes', int(hole.sum()), 'closed', int((diff & hole).sum()), 'other', int(other.sum()),
          'still_hole_in_B', int((hole & ~fb).sum()))
