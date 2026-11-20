"""Lining poke gate (render): is any lining face seen from outside where the installed cloth was seen?
Args (Blender): <lined glb> <out json> <orig face counts per LOD0 primitive, comma list (2270,6135)> [key=value: step 4,
                px_mm 4, clips (comma list), elev 0,20, shots 3]
The LOD0 mesh of the lined GLB, every clip at every step-th 30 fps frame, 16 orthographic views (as see_through_gate.py), back
faces culled. Render A: every face, lining faces (each primitive's faces past its original count) green, the rest grey.
Render B: the original faces plus their normal-flipped red twin, so the nearest original face along each pixel's ray shows:
grey when it is a front face (cloth seen from outside), red when it is a back face (a view into an opening). POKE pixels:
green in A where B is grey (the lining is nearer than the outside of the cloth: dark specks on the cloth). FILL pixels:
green in A where B is red or empty (the lining closes an opening).
With report=<glb_lining json> the rim strips are blue and their pixels over outside cloth are EDGE (the cloth's cut edge,
seen by design), not POKE. BLOB = poke pixels surviving a 3x3 erosion (a lining patch showing on the cloth). Reports per clip the worst view's poke pixels, frames with any poke, the fill and edge maxima; annotated worst images (poke
magenta, fill green, grey cloth) next to the json."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT, COUNTS = a[0], a[1], [int(x) for x in a[2].split(',')]
opt = dict(x.split('=', 1) for x in a[3:])
# classes of the added triangles (glb_lining.py report: L lining twin, S rim strip); strips are the cloth's cut edge, seen
# from outside by design, and are counted apart (EDGE) from the lining (POKE)
CLASSES = {}
if opt.get('report'):
    r = json.load(open(opt['report']))
    CLASSES = {int(k): v['classes'] for k, v in r['lods']['0']['_added'].items()}
STEP = int(opt.get('step', 4)); PX = float(opt.get('px_mm', 4.0)) / 1000.0
CLIPS = [c for c in opt.get('clips', '').split(',') if c]
ELEV = [float(x) for x in opt.get('elev', '0,20').split(',')]; AZ = [i * 45.0 for i in range(8)]
SHOTS = int(opt.get('shots', 3))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name and 'Shadow' not in o.name)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not mesh:
        bpy.data.objects.remove(o)
me = mesh.data
# lining flag per polygon: polygons come per material in primitive order; within a material, original faces first
mats = [p.material_index for p in me.polygons]
flag = np.zeros(len(me.polygons), bool); strip = np.zeros(len(me.polygons), bool); seen = {}
for i, m in enumerate(mats):
    k = seen.get(m, 0); seen[m] = k + 1
    flag[i] = k >= COUNTS[m]
    if flag[i] and m in CLASSES and CLASSES[m][k - COUNTS[m]] == 'S':
        strip[i] = True
print('POKE lining faces', int(flag.sum()), 'of', len(flag))
col = me.color_attributes.new('Flag', 'BYTE_COLOR', 'CORNER')
cols = np.zeros((len(me.loops), 4), np.float32)
for p in me.polygons:
    c = (0, 0, 1, 1) if strip[p.index] else (0, 1, 0, 1) if flag[p.index] else (0.5, 0.5, 0.5, 1)
    cols[p.loop_start:p.loop_start + p.loop_total] = c
col.data.foreach_set('color', cols.ravel())
me.color_attributes.active_color = col
orig = mesh.copy(); orig.data = me.copy(); orig.name = 'Orig'
bpy.context.scene.collection.objects.link(orig)
bm = bmesh.new(); bm.from_mesh(orig.data); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(flag)[0]], context='FACES_ONLY')
bm.to_mesh(orig.data); bm.free()
# the original faces' normal-flipped red twin: the nearest original face along a ray is a back face (a view into an opening)
twin = orig.copy(); twin.data = orig.data.copy(); twin.name = 'Twin'
bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(twin.data); bm.free()
tc = twin.data.color_attributes['Flag']
tc.data.foreach_set('color', np.tile(np.array([1, 0, 0, 1], np.float32), len(twin.data.loops)))
sc = bpy.context.scene
FPS = sc.render.fps / sc.render.fps_base
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'VERTEX'; sh.show_backface_culling = True
sc.display.render_aa = 'OFF'; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
odir = os.path.dirname(os.path.abspath(OUT)); tmp = os.path.join(odir, '_poke_tmp'); os.makedirs(tmp, exist_ok=True)
stem = os.path.splitext(os.path.basename(OUT))[0]


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path); W, H = im.size
    px = np.array(im.pixels[:], np.float32).reshape(H, W, 4); bpy.data.images.remove(im)
    return px


rep = {'glb': GLB, 'step': STEP, 'px_mm': PX * 1000, 'clips': {}}
worst = []
rig.animation_data_create()
for act in [x for x in bpy.data.actions if not CLIPS or x.name in CLIPS]:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    n30 = int(round((f1 - f0) / FPS * 30)) + 1
    rc = rep['clips'][act.name] = {'poke_max': 0, 'poke_worst': None, 'poke_frames': 0, 'fill_max': 0}
    for f30 in range(0, n30, STEP):
        f = f0 + f30 / 30.0 * FPS
        sc.frame_set(int(f), subframe=f % 1.0)
        dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); em = ev.to_mesh()
        P = np.array([tuple(ev.matrix_world @ v.co) for v in em.vertices]); ev.to_mesh_clear()
        cen = (P.min(0) + P.max(0)) / 2; anyp = False
        for el in ELEV:
            for az in AZ:
                d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)),
                            -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
                rot = (-d).to_track_quat('-Z', 'Y').to_matrix()
                right, up = rot.col[0], rot.col[1]
                Q = P - cen
                ex = max(np.abs(Q @ np.array(right)).max(), np.abs(Q @ np.array(up)).max()) * 2 + 0.04
                res = int(math.ceil(ex / PX)); cd.ortho_scale = res * PX
                sc.render.resolution_x = sc.render.resolution_y = res
                cam.location = Vector(cen) + d * 4.0; cam.rotation_euler = rot.to_euler()
                orig.hide_render = True; twin.hide_render = True; mesh.hide_render = False
                pa = render(os.path.join(tmp, 'a.png'))
                orig.hide_render = False; twin.hide_render = False; mesh.hide_render = True
                pb = render(os.path.join(tmp, 'b.png'))
                green = (pa[..., 3] > 0.5) & (pa[..., 1] > 0.8) & (pa[..., 0] < 0.2)
                # B: original faces plus their red twin: grey = the nearest original face is a front face (cloth seen
                # from outside); red = a back face (into an opening); none = background
                frontb = (pb[..., 3] > 0.5) & ~((pb[..., 0] > 0.9) & (pb[..., 1] < 0.1))
                blue = (pa[..., 3] > 0.5) & (pa[..., 2] > 0.8) & (pa[..., 0] < 0.2) & (pa[..., 1] < 0.2)
                poke = green & frontb; fill = green & ~frontb
                npk, nfl = int(poke.sum()), int(fill.sum())
                # BLOB: poke pixels left after a 3x3 erosion (a lining patch on the cloth, DM2's dark specks), as opposed to
                # the one-pixel lines along a lined rim or at the edge of a fill, where the lining meets the cloth's edge
                er = poke.copy()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        er &= np.roll(np.roll(poke, dy, 0), dx, 1)
                rc['blob_max'] = max(rc.get('blob_max', 0), int(er.sum()))
                rc['fill_max'] = max(rc['fill_max'], nfl)
                rc['edge_max'] = max(rc.get('edge_max', 0), int((blue & frontb).sum()))
                anyp |= npk > 0
                if npk > rc['poke_max']:
                    rc['poke_max'] = npk; rc['poke_worst'] = [f30, f'az{int(az):03d}_el{int(el):02d}']
                    img = np.where((pa[..., 3] > 0.5)[..., None], np.array([0.6, 0.6, 0.6, 1.0]), np.array([1.0, 1, 1, 1]))
                    img[fill] = (0.1, 0.8, 0.1, 1); img[blue] = (0.2, 0.3, 1, 1); img[poke] = (1, 0, 1, 1)
                    worst.append((npk, act.name, f30, rc['poke_worst'][1], img.astype(np.float32), res))
                    worst.sort(key=lambda w: -w[0]); worst = worst[:SHOTS]
        rc['poke_frames'] += anyp
    print('POKE', act.name, json.dumps(rc))
rep['poke_max'] = max(r['poke_max'] for r in rep['clips'].values())
shots = []
for npk, c, f30, vname, img, res in worst:
    im = bpy.data.images.new('S', res, res, alpha=True); im.pixels.foreach_set(img.ravel())
    p = os.path.join(odir, f'{stem}_{c}_{f30}_{vname}.png'); im.filepath_raw = p; im.file_format = 'PNG'; im.save()
    shots.append({'clip': c, 'frame30': f30, 'view': vname, 'poke_px': npk, 'png': p})
rep['shots'] = shots
rep['edge_max'] = max(r.get('edge_max', 0) for r in rep['clips'].values())
rep['blob_max'] = max(r.get('blob_max', 0) for r in rep['clips'].values())
json.dump(rep, open(OUT, 'w'), indent=1)
print('POKE_SUMMARY', rep['poke_max'], 'blob', rep['blob_max'], 'edge', rep['edge_max'], json.dumps({c: r['poke_max'] for c, r in rep['clips'].items()}))
