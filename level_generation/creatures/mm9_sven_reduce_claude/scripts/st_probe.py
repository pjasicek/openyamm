"""PeasantM2d reduction probe (copy of the creature's see-through gate set-up): for one clip, 30 fps frame and view
(opt clip=, f30=, view=azAAA_elEE) print the faces hit by the HOLE pixels (rest centroid in glTF y-up) -> json out.
Original: See-through gate (2026-11-02, user on PeasantDM2: "holes in sleeves + some in knees (e.g. running anim 12)").

Args (Blender): <glb> <out json> [key=value: step 3 (30 fps frames), px_mm 3.0, views 8x2 (8 azimuths at level and
                at the party's 20 deg down), clips (comma list, default all), extra Running:12,... (always sampled),
                shots 4 (annotated worst-case images per zone), only (comma list of zones for the shots)]

The LOD0 mesh only (LODs, shadow meshes dropped), every clip at every `step`-th 30 fps frame (plus `extra`), from 16
directions (8 azimuths x elevations 0 and 20 deg down, the party's view of a standing townsman), orthographic, full body,
fixed pixel size `px_mm`, no anti-aliasing. Two Workbench renders per view, back faces culled as in the game:
  1. the mesh alone: alpha = a front face somewhere along the pixel's ray;
  2. the mesh plus a normal-flipped twin coloured red: alpha = any face; red = the nearest face is a back face of the
     mesh (the view goes into an opening: inside a sleeve, a boot shaft, under a hem).
HOLE pixels are covered in 2 but not in 1: only back faces along the ray, so the game shows the background through the
cloth. INSIDE pixels are red in 2 (a hole, or a view through an opening onto other parts of the body).
Each hole / inside pixel is attributed by a ray cast from the pixel to the nearest face of the posed mesh (any facing):
its zone comes from the dominant bone of the face's vertices: sleeve L/R (UpperArm, Forearm, Hand, fingers), boot L/R
(Calf, Foot, Toe), trousers L/R (Thigh), torso (Pelvis, Spine*: hem, belt), collar (Neck, or the Head bone on the body
material), head (Head bone on the head material: beard sheet, eyes). Reported per clip and zone: worst frame's pixels
(with its frame and view), frames with any hole, the worst per camera elevation; totals; annotated images of the worst cases (holes yellow, inside red
on a flat grey render) next to the json.
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = a[0], a[1]
opt = dict(x.split('=', 1) for x in a[2:])
STEP = int(opt.get('step', 3))
PX = float(opt.get('px_mm', 3.0)) / 1000.0
CLIPS = [c for c in opt.get('clips', '').split(',') if c]
EXTRA = {}
for x in opt.get('extra', 'Running:12').split(','):
    if x:
        c, f = x.split(':'); EXTRA.setdefault(c, set()).add(int(f))
SHOTS = int(opt.get('shots', 4))
ELEV = [float(x) for x in opt.get('elev', '0,20').split(',')]
AZ = [i * 45.0 for i in range(8)]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name
            and 'Shadow' not in o.name)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not mesh:
        bpy.data.objects.remove(o)
me = mesh.data
names = [g.name for g in mesh.vertex_groups]
head_mat = {i for i, m in enumerate(me.materials) if m and 'Head' in m.name}
# zone per polygon (dominant bone of its vertices, summed weights)
dom_v = np.full(len(me.vertices), -1)
for v in me.vertices:
    if len(v.groups):
        dom_v[v.index] = max(v.groups, key=lambda g: g.weight).group


def zone_of_bone(n, head):
    s = ' L ' if ' L ' in n else ' R ' if ' R ' in n else None
    side = s.strip() if s else ''
    if any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger', 'Clavicle')):
        return 'sleeve ' + side
    if any(k in n for k in ('Calf', 'Foot', 'Toe')):
        return 'boot ' + side
    if 'Thigh' in n:
        return 'trousers ' + side
    if 'Head' in n or 'Neck' in n:
        return 'head' if head else 'collar'
    if n.startswith('MP_'):
        return 'sleeve ?'
    return 'torso'


ZONE = []
for p in me.polygons:
    cnt = {}
    for vi in p.vertices:
        if dom_v[vi] >= 0:
            cnt[dom_v[vi]] = cnt.get(dom_v[vi], 0) + 1
    b = names[max(cnt, key=cnt.get)] if cnt else ''
    ZONE.append(zone_of_bone(b, p.material_index in head_mat))
ZONES = sorted(set(ZONE))

# normal-flipped twin with the same armature deform
twin = mesh.copy(); twin.data = me.copy(); twin.name = 'Twin'
bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bm.to_mesh(twin.data); bm.free()
mesh.color = (0.6, 0.6, 0.6, 1.0); twin.color = (1.0, 0.0, 0.0, 1.0)

sc = bpy.context.scene
FPS = sc.render.fps / sc.render.fps_base
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_backface_culling = True
sc.display.render_aa = 'OFF'
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
odir = os.path.dirname(os.path.abspath(OUT))
tmp = os.path.join(odir, '_see_through_tmp'); os.makedirs(tmp, exist_ok=True)
stem = os.path.splitext(os.path.basename(OUT))[0]


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    W, H = im.size
    px = np.array(im.pixels[:], np.float32).reshape(H, W, 4)
    bpy.data.images.remove(im)
    return px



CL = opt['clip']; F30 = int(opt['f30']); VW = opt['view']
az = float(VW[2:5]); el = float(VW[8:10])
rest_c = np.array([tuple(p.center) for p in me.polygons])        # bind pose (rig not posed yet), Blender z-up
rig.animation_data_create(); act = bpy.data.actions[CL]; rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = act.frame_range; f = f0 + F30 / 30.0 * FPS
sc.frame_set(int(f), subframe=f % 1.0)
dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); em = ev.to_mesh()
P = np.array([tuple(ev.matrix_world @ v.co) for v in em.vertices])
bvh = BVHTree.FromPolygons([Vector(p) for p in P], [p.vertices[:] for p in em.polygons]); ev.to_mesh_clear()
cen = (P.min(0) + P.max(0)) / 2
d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
rot = (-d).to_track_quat('-Z', 'Y').to_matrix(); right, up, fwd = rot.col[0], rot.col[1], -rot.col[2]
Q = P - cen; ex = max(np.abs(Q @ np.array(right)).max(), np.abs(Q @ np.array(up)).max()) * 2 + 0.04
res = int(math.ceil(ex / PX)); cd.ortho_scale = res * PX; sc.render.resolution_x = sc.render.resolution_y = res
cam.location = Vector(cen) + d * 4.0; cam.rotation_euler = rot.to_euler()
twin.hide_render = True; p1 = render(os.path.join(tmp, 'pa.png')); twin.hide_render = False; p2 = render(os.path.join(tmp, 'pb.png'))
hole = (p2[..., 3] > 0.5) & ~(p1[..., 3] > 0.5)
hits = {}
for i, j in zip(*np.nonzero(hole)):
    x = (j + 0.5) / res - 0.5; y = (i + 0.5) / res - 0.5
    o = cam.location + right * (x * res * PX) + up * (y * res * PX)
    h = bvh.ray_cast(o, fwd, 10.0)
    if h[0] is not None:
        hits[h[2]] = hits.get(h[2], 0) + 1
out = [{'face': int(k), 'px': v, 'zone': ZONE[k], 'mat': me.materials[me.polygons[k].material_index].name,
        'rest_gltf': [float(rest_c[k][0]), float(rest_c[k][2]), float(-rest_c[k][1])]} for k, v in sorted(hits.items(), key=lambda t: -t[1])]
json.dump({'holes': int(hole.sum()), 'res': res, 'pixels': [[int(i), int(j)] for i, j in zip(*np.nonzero(hole))], 'faces': out}, open(OUT, 'w'), indent=1)
if opt.get('pix'):                                   # first hit (any facing) at the given pixels of another run
    first = {}
    for i, j in json.load(open(opt['pix']))['pixels']:
        x = (j + 0.5) / res - 0.5; y = (i + 0.5) / res - 0.5
        o = cam.location + right * (x * res * PX) + up * (y * res * PX)
        h = bvh.ray_cast(o, fwd, 10.0)
        if h[0] is not None and not hole[i, j]:
            first[h[2]] = first.get(h[2], 0) + 1
    print('FIRST', res, sorted([(v, int(k), ZONE[k], [round(float(c), 3) for c in (rest_c[k][0], rest_c[k][2] + 0.847262, -rest_c[k][1])]) for k, v in first.items()], reverse=True)[:12])
print('PROBE', int(hole.sum()), [(o['face'], o['px'], o['zone'], [round(c, 3) for c in o['rest_gltf']]) for o in out[:12]])
