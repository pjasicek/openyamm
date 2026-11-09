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
ZONE_DM2 = []   # the 2026-11-02 sweep's classes (DM2's gate: head material = name ends with 'Head', so PeasantM1Head faces on the Head bone count as collar)
head_mat_dm2 = {i for i, m in enumerate(me.materials) if m and m.name.endswith('Head')}
for p in me.polygons:
    cnt = {}
    for vi in p.vertices:
        if dom_v[vi] >= 0:
            cnt[dom_v[vi]] = cnt.get(dom_v[vi], 0) + 1
    b = names[max(cnt, key=cnt.get)] if cnt else ''
    ZONE.append(zone_of_bone(b, p.material_index in head_mat))
    ZONE_DM2.append(zone_of_bone(b, p.material_index in head_mat_dm2))
ZONES = sorted(set(ZONE))

# normal-flipped twin with the same armature deform
twin = mesh.copy(); twin.data = me.copy(); twin.name = 'Twin'
bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bm.to_mesh(twin.data); bm.free()
mesh.color = (0.6, 0.6, 0.6, 1.0); twin.color = (1.0, 0.0, 0.0, 1.0)
# lining poke (lining=<npz of the lining triangles' GLB rest centres, line.py>): the lined mesh renders as two objects, the
# outer faces grey and the lining faces blue (render 1 alpha unchanged). A blue pixel is a visible lining face; it is a POKE
# when the ray, past the lining faces, meets a front face of the other geometry within 2 cm (the lining sits in front of the
# cloth it lines instead of behind it); seen through an opening, the next face is the garment's own back face.
LIN = set()
lin_obj = outer_obj = None
if opt.get('lining'):
    from mathutils.kdtree import KDTree
    z = np.load(opt['lining'])
    kd = KDTree(len(me.polygons))
    for p in me.polygons:
        kd.insert(mesh.matrix_world @ p.center, p.index)
    kd.balance()
    kinds = set(opt.get('poke_kinds', 'band,cap').split(','))   # own-paint fills and hair backs are meant to show
    keep = np.isin(z['kind'], list(kinds)) if 'kind' in z else np.ones(len(z['centre']), bool)
    for c in z['centre'][keep]:
        co, i, dist = kd.find((float(c[0]), float(-c[2]), float(c[1])))
        if dist < 1e-4:
            LIN.add(i)
    print('LINING faces matched', len(LIN), 'of', len(z['centre']))

    def part_copy(keep_lining, name, colour):
        o = mesh.copy(); o.data = me.copy(); o.name = name
        bpy.context.scene.collection.objects.link(o)
        b = bmesh.new(); b.from_mesh(o.data); b.faces.ensure_lookup_table()
        bmesh.ops.delete(b, geom=[f for f in b.faces if (f.index in LIN) != keep_lining], context='FACES')
        b.to_mesh(o.data); b.free(); o.color = colour
        return o
    outer_obj = part_copy(False, 'Outer', (0.6, 0.6, 0.6, 1.0))
    lin_obj = part_copy(True, 'Lining', (0.0, 0.0, 1.0, 1.0))
    mesh.hide_render = True
POKE = {}

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


POKE_FACES = np.zeros(len(me.polygons), np.int64)       # poke pixels per (first-hit lining) polygon
FACE_HOLES = np.zeros(len(me.polygons), np.int64)      # hole pixels per polygon over every frame and view (which back faces show)
REST_CEN = np.array([tuple(mesh.matrix_world @ p.center) for p in me.polygons])
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
                if LIN:
                    blue = front & (p1[..., 2] > 0.9) & (p1[..., 0] < 0.1)
                    pk = np.zeros(blue.shape, bool)
                    for i, j in zip(*np.nonzero(blue)):
                        x = (j + 0.5) / res - 0.5; y = (i + 0.5) / res - 0.5
                        o = cam.location + right * (x * res * PX) + up * (y * res * PX)
                        hit = bvh.ray_cast(o, fwd, 10.0); n_skip = 0; f_first = hit[2]
                        while hit[0] is not None and hit[2] in LIN and n_skip < 20:
                            o2 = hit[0] + fwd * 1e-5; first = hit[0] if n_skip == 0 else first
                            hit = bvh.ray_cast(o2, fwd, 10.0); n_skip += 1
                        if n_skip and hit[0] is not None and (hit[0] - first).length < 0.02 and hit[1].dot(fwd) < 0:
                            pk[i, j] = True
                            POKE_FACES[f_first] += 1
                    pr_ = POKE.setdefault(act.name, {'max_px': 0, 'worst': None, 'frames': [], 'visible_max': 0})
                    pr_['visible_max'] = max(pr_['visible_max'], int(blue.sum()))
                    npk = int(pk.sum())
                    if npk and f30 not in pr_['frames']:
                        pr_['frames'].append(f30)
                    if npk > pr_['max_px']:
                        pr_['max_px'] = npk; pr_['worst'] = [f30, vname]
                        img = np.where(front[..., None], np.array([0.55, 0.55, 0.55, 1.0]), np.array([1.0, 1.0, 1.0, 1.0]))
                        img[blue] = (0.1, 0.3, 1.0, 1.0); img[pk] = (1.0, 0.0, 1.0, 1.0)
                        pr_['img'] = (img.astype(np.float32), res)
                anyf = p2[..., 3] > 0.5
                red = anyf & (p2[..., 0] > 0.9) & (p2[..., 1] < 0.1)
                hole = anyf & ~front
                ii, jj = np.nonzero(red)
                zc_h, zc_i = {}, {}
                zd_h = {}
                for i, j in zip(ii, jj):
                    x = (j + 0.5) / res - 0.5; y = (i + 0.5) / res - 0.5
                    o = cam.location + right * (x * res * PX) + up * (y * res * PX)
                    hit = bvh.ray_cast(o, fwd, 10.0)
                    z = ZONE[hit[2]] if hit[0] is not None else 'none'
                    zc_i[z] = zc_i.get(z, 0) + 1
                    if hole[i, j]:
                        zc_h[z] = zc_h.get(z, 0) + 1
                        z2 = ZONE_DM2[hit[2]] if hit[0] is not None else 'none'
                        zd_h[z2] = zd_h.get(z2, 0) + 1
                        if hit[0] is not None:
                            FACE_HOLES[hit[2]] += 1
                for z2, nh2 in zd_h.items():
                    r2 = rc.setdefault('zones_dm2', {}).setdefault(z2, {'hole_max': 0, 'worst': None})
                    if nh2 > r2['hole_max']:
                        r2['hole_max'] = nh2; r2['worst'] = [f30, vname]
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
if LIN:
    for c, pr_ in POKE.items():
        if 'img' in pr_:
            img, res = pr_.pop('img')
            im = bpy.data.images.new('S', res, res, alpha=True); im.pixels.foreach_set(img.ravel())
            p = os.path.join(odir, f'{stem}_poke_{c}_{pr_["worst"][0]}_{pr_["worst"][1]}.png')
            im.filepath_raw = p; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im); pr_['png'] = p
    rep['poke'] = POKE
    print('LINING_POKE', json.dumps({c: [v['max_px'], v['worst'], len(v['frames']), v['visible_max']] for c, v in POKE.items()}))
json.dump(rep, open(OUT, 'w'), indent=1)
np.savez(os.path.splitext(OUT)[0] + '_faces.npz', holes=FACE_HOLES, pokes=POKE_FACES, rest_centre=REST_CEN,
         material=np.array([p.material_index for p in me.polygons]), materials=np.array([m.name for m in me.materials]))
print('SEE_THROUGH_SUMMARY', json.dumps(summary))
print('SEE_THROUGH done', OUT)
