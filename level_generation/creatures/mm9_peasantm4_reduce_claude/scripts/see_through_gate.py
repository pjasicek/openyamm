"""See-through gate (2026-11-02, user on PeasantDM2: "holes in sleeves + some in knees (e.g. running anim 12)").

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
head_mat = {i for i, m in enumerate(me.materials) if m and 'Head' in m.name}   # (PeasantM7 reduction: head materials PeasantM7Head_A/_B)
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


rep = {'glb': GLB, 'step': STEP, 'px_mm': PX * 1000, 'views': len(AZ) * len(ELEV), 'clips': {}, 'zones': ZONES}
worst = []          # (px, zone, clip, frame, view, image path)
rig.animation_data_create()
acts = [x for x in bpy.data.actions if not CLIPS or x.name in CLIPS]
for act in acts:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    n30 = int(round((f1 - f0) / FPS * 30)) + 1
    frames = sorted(set(range(0, n30, STEP)) | {f for f in EXTRA.get(act.name, ()) if f < n30})
    rc = rep['clips'][act.name] = {'frames30': frames, 'zones': {}}
    for f30 in frames:
        f = f0 + f30 / 30.0 * FPS
        sc.frame_set(int(f), subframe=f % 1.0)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = mesh.evaluated_get(dg)
        em = ev.to_mesh()
        P = np.array([tuple(ev.matrix_world @ v.co) for v in em.vertices])
        bvh = BVHTree.FromPolygons([Vector(p) for p in P], [p.vertices[:] for p in em.polygons])
        ev.to_mesh_clear()
        cen = (P.min(0) + P.max(0)) / 2
        for el in ELEV:
            for az in AZ:
                vname = f'az{int(az):03d}_el{int(el):02d}'
                d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)),
                            -math.cos(math.radians(az)) * math.cos(math.radians(el)),
                            math.sin(math.radians(el))))          # camera direction from the target
                rot = (-d).to_track_quat('-Z', 'Y').to_matrix()
                right, up, fwd = rot.col[0], rot.col[1], -rot.col[2]
                Q = P - cen
                ex = max(np.abs(Q @ np.array(right)).max(), np.abs(Q @ np.array(up)).max()) * 2 + 0.04
                res = int(math.ceil(ex / PX))
                cd.ortho_scale = res * PX
                sc.render.resolution_x = sc.render.resolution_y = res
                cam.location = Vector(cen) + d * 4.0
                cam.rotation_euler = rot.to_euler()
                twin.hide_render = True
                p1 = render(os.path.join(tmp, 'a.png'))
                twin.hide_render = False
                p2 = render(os.path.join(tmp, 'b.png'))
                front = p1[..., 3] > 0.5
                anyf = p2[..., 3] > 0.5
                red = anyf & (p2[..., 0] > 0.9) & (p2[..., 1] < 0.1)
                hole = anyf & ~front
                ii, jj = np.nonzero(red)
                zc_h, zc_i = {}, {}
                for i, j in zip(ii, jj):
                    x = (j + 0.5) / res - 0.5; y = (i + 0.5) / res - 0.5
                    o = cam.location + right * (x * res * PX) + up * (y * res * PX)
                    hit = bvh.ray_cast(o, fwd, 10.0)
                    z = ZONE[hit[2]] if hit[0] is not None else 'none'
                    zc_i[z] = zc_i.get(z, 0) + 1
                    if hole[i, j]:
                        zc_h[z] = zc_h.get(z, 0) + 1
                for z in set(zc_h) | set(zc_i):
                    r = rc['zones'].setdefault(z, {'hole_max': 0, 'hole_frames': [], 'worst': None, 'inside_max': 0,
                                                   'hole_max_by_elev': {}})
                    nh, ni = zc_h.get(z, 0), zc_i.get(z, 0)
                    ek = str(int(el))
                    r['hole_max_by_elev'][ek] = max(r['hole_max_by_elev'].get(ek, 0), nh)
                    r['inside_max'] = max(r['inside_max'], ni)
                    if nh and f30 not in r['hole_frames']:
                        r['hole_frames'].append(f30)
                    if nh > r['hole_max']:
                        r['hole_max'] = nh; r['worst'] = [f30, vname]
                        img = np.where(front[..., None], np.array([0.55, 0.55, 0.55, 1.0]), np.array([1.0, 1.0, 1.0, 1.0]))
                        img[red] = (0.85, 0.1, 0.1, 1.0)
                        img[hole] = (1.0, 0.85, 0.0, 1.0)
                        worst.append((nh, z, act.name, f30, vname, img.astype(np.float32), res))
                        worst.sort(key=lambda w: -w[0])
                        # keep the top SHOTS per zone in memory
                        keep, per = [], {}
                        for w in worst:
                            per[w[1]] = per.get(w[1], 0) + 1
                            if per[w[1]] <= SHOTS:
                                keep.append(w)
                        worst = keep
    tot = {z: r['hole_max'] for z, r in rc['zones'].items()}
    print('SEE_THROUGH', act.name, json.dumps({z: [r['hole_max'], r['worst'], len(r['hole_frames']), r['inside_max']]
                                              for z, r in sorted(rc['zones'].items())}))
summary = {}
for c, rc in rep['clips'].items():
    for z, r in rc['zones'].items():
        s = summary.setdefault(z, {'hole_max': 0, 'worst': None, 'clips_with_holes': 0, 'frames_with_holes': 0,
                                   'hole_max_by_elev': {}})
        for ek, v in r['hole_max_by_elev'].items():
            s['hole_max_by_elev'][ek] = max(s['hole_max_by_elev'].get(ek, 0), v)
        if r['hole_max']:
            s['clips_with_holes'] += 1; s['frames_with_holes'] += len(r['hole_frames'])
        if r['hole_max'] > s['hole_max']:
            s['hole_max'] = r['hole_max']; s['worst'] = [c] + r['worst']
rep['summary'] = summary
shots = []
for k, (nh, z, c, f30, vname, img, res) in enumerate(worst):
    im = bpy.data.images.new('S', res, res, alpha=True)
    im.pixels.foreach_set(img.ravel())
    p = os.path.join(odir, f'{stem}_{z.replace(" ", "")}_{c}_{f30}_{vname}.png')
    im.filepath_raw = p; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    shots.append({'zone': z, 'clip': c, 'frame30': f30, 'view': vname, 'hole_px': nh, 'png': p})
rep['shots'] = shots
json.dump(rep, open(OUT, 'w'), indent=1)
print('SEE_THROUGH_SUMMARY', json.dumps(summary))
print('SEE_THROUGH done', OUT)
