"""Textured see-through views (diagnostic and before/after sheets): the LOD0 mesh posed at given clip frames, rendered with
its textures and back faces culled as in the game; pixels covered only by back faces (the see-through gate's HOLE pixels)
are painted yellow, the background white. Optional crop around the holes (or a given box) scaled up.
Args (Blender): <glb> <out dir> <spec> [<spec> ...] [px_mm=3] [crop=1]
  spec = name:clip:frame30:azimuth:elevation[:cx,cy,half (metres in the image plane from the body centre)]
Writes <out dir>/<name>.png (full) and <name>_crop.png (holes' bounding box + 6 cm, at least 30 cm, scaled to 600 px)."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = a[0], a[1]
specs = [x for x in a[2:] if '=' not in x]
opt = dict(x.split('=', 1) for x in a[2:] if '=' in x)
PX = float(opt.get('px_mm', 3.0)) / 1000.0
CROP = opt.get('crop', '1') == '1'
MAT = int(opt.get('mat', '-1'))   # colour holes on this material index cyan and crop around them only
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name
            and 'Shadow' not in o.name)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not mesh:
        bpy.data.objects.remove(o)
twin = mesh.copy(); twin.data = mesh.data.copy(); twin.name = 'Twin'
bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bm.to_mesh(twin.data); bm.free()
twin.color = (1, 0, 0, 1)
sc = bpy.context.scene
FPS = sc.render.fps / sc.render.fps_base
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.show_backface_culling = True
sc.display.render_aa = 'OFF'
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tmp = os.path.join(OUT, '_tmp'); os.makedirs(tmp, exist_ok=True)


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    W, H = im.size
    px = np.array(im.pixels[:], np.float32).reshape(H, W, 4)
    bpy.data.images.remove(im)
    return px


def save(img, path):
    H, W = img.shape[:2]
    im = bpy.data.images.new('S', W, H, alpha=True)
    im.pixels.foreach_set(img.astype(np.float32).ravel())
    im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)


rig.animation_data_create()
hitf = {}
for spec in specs:
    parts = spec.split(':')
    name, clip, f30, az, el = parts[0], parts[1], int(parts[2]), float(parts[3]), float(parts[4])
    box = [float(x) for x in parts[5].split(',')] if len(parts) > 5 else None
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0 = act.frame_range[0]
    f = f0 + f30 / 30.0 * FPS
    sc.frame_set(int(f), subframe=f % 1.0)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg); em = ev.to_mesh()
    P = np.array([tuple(ev.matrix_world @ v.co) for v in em.vertices])
    pmat = [p.material_index for p in em.polygons]
    bvh = BVHTree.FromPolygons([Vector(p) for p in P], [p.vertices[:] for p in em.polygons]); ev.to_mesh_clear()
    cen = (P.min(0) + P.max(0)) / 2
    d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)),
                math.sin(math.radians(el))))
    rot = (-d).to_track_quat('-Z', 'Y').to_matrix()
    right, up = rot.col[0], rot.col[1]
    Q = P - cen
    ex = max(np.abs(Q @ np.array(right)).max(), np.abs(Q @ np.array(up)).max()) * 2 + 0.04
    res = int(math.ceil(ex / PX))
    cd.ortho_scale = res * PX
    sc.render.resolution_x = sc.render.resolution_y = res
    cam.location = Vector(cen) + d * 4.0
    cam.rotation_euler = rot.to_euler()
    twin.hide_render = True
    sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
    pt = render(os.path.join(tmp, 't.png'))
    twin.hide_render = False
    sh.light = 'FLAT'; sh.color_type = 'OBJECT'
    p2 = render(os.path.join(tmp, 'b.png'))
    front = pt[..., 3] > 0.5
    hole = (p2[..., 3] > 0.5) & ~front
    img = np.ones_like(pt)
    img[front] = pt[front]; img[..., 3] = 1
    img[hole] = (1.0, 0.85, 0.0, 1.0)
    if MAT >= 0:
        fwd = -rot.col[2]; sel = np.zeros_like(hole)
        for i, j in zip(*np.nonzero(hole)):
            o = cam.location + right * (((j + 0.5) / res - 0.5) * res * PX) + up * (((i + 0.5) / res - 0.5) * res * PX)
            h = bvh.ray_cast(o, fwd, 10.0)
            if h[0] is not None and pmat[h[2]] == MAT:
                sel[i, j] = True
                hitf.setdefault(name, []).append(int(h[2]))
        img[sel] = (0.0, 0.9, 0.9, 1.0)
        hole = sel
    save(img, os.path.join(OUT, name + '.png'))
    print('HOLEVIEW', name, int(hole.sum()), res)
    if CROP:
        if box:
            cx, cy, hw = box
            ci, cj = res / 2 + cy / PX, res / 2 + cx / PX
            i0, i1, j0, j1 = ci - hw / PX, ci + hw / PX, cj - hw / PX, cj + hw / PX
        elif hole.any():
            ii, jj = np.nonzero(hole)
            m = 0.06 / PX
            i0, i1, j0, j1 = ii.min() - m, ii.max() + m, jj.min() - m, jj.max() + m
            s = max(i1 - i0, j1 - j0, 0.3 / PX)
            ci, cj = (i0 + i1) / 2, (j0 + j1) / 2
            i0, i1, j0, j1 = ci - s / 2, ci + s / 2, cj - s / 2, cj + s / 2
        else:
            continue
        i0, j0 = max(0, int(i0)), max(0, int(j0)); i1, j1 = min(res, int(i1)), min(res, int(j1))
        c = img[i0:i1, j0:j1]
        k = max(1, int(600 / max(c.shape[:2])))
        save(np.repeat(np.repeat(c, k, 0), k, 1), os.path.join(OUT, name + '_crop.png'))

if hitf:
    import json
    me = mesh.data
    out = {k: sorted({(f, tuple(round(x, 4) for x in me.polygons[f].center)) for f in v}) for k, v in hitf.items()}
    json.dump(out, open(os.path.join(OUT, 'hit_faces.json'), 'w'))
