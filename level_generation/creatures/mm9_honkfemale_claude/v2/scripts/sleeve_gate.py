"""Sleeve gate (2026-10-30, user on Yrsa: "hands - cut off, floating?"): every clip at 48 fps, both sleeves.

Args (Blender): <glb> <out json> <bone prefix: FHP | Bip01> [fps 48] [views front,above34,below,q34] [res 160]
1. See-through: each view, framed on the forearm and hand (0.17 m half width), is rendered twice on a magenta
   background, with back faces culled (as the game) and without. A pixel that is background only when back faces
   are culled shows the scene through the back of a single-sided surface (into a sleeve and out through its far side);
   only pixels within 7 cm of the forearm (its outer 55 % and the wrist) count.
   Reported per clip, side and view: the worst frame's pixel count; the worst frames' culled tiles are saved next to
   the json with those pixels in green.
2. Forearm inside the sleeve: from every LOD0 vertex weighted mostly to the side's forearm bone and drawn with the
   head + hands material that lies inside the sleeve at rest (less than 75 % of the forearm from the elbow: the
   forearm sleeve_lining.py adds), 12 rays leave perpendicular
   to the posed forearm; one that leaves the model without a hit is skin poking out of the sleeve.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT, TOK = a[0], a[1], a[2]
FPS = float(a[3]) if len(a) > 3 else 48.0
VIEWS = (a[4] if len(a) > 4 else 'front,above34,below,q34').split(',')
RES = int(a[5]) if len(a) > 5 else 160
DIRS = {'front': (0, -1, 0), 'above34': (-0.45, -0.75, 0.55), 'above34r': (0.45, -0.75, 0.55),
        'below': (0, -0.35, -1), 'q34': (0.57, -0.82, 0), 'q34l': (-0.57, -0.82, 0), 'side': (1, 0, 0)}
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
head_mat = {i for i, m in enumerate(me.materials) if m and m.name.endswith('Head')}
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = RES
sc.world = bpy.data.worlds.new('W'); sc.world.color = (1.0, 0.0, 1.0)
sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 0.34
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tmp = os.path.join(os.path.dirname(os.path.abspath(OUT)), '_sleeve_gate_tmp')
os.makedirs(tmp, exist_ok=True)
probe = {}
for S in 'LR':
    fa = f'{TOK} {S} Forearm'
    gi = names.index(fa)
    ids = set()
    for p in me.polygons:
        if p.material_index in head_mat:
            for v in p.vertices:
                g = max(me.vertices[v].groups, key=lambda g: g.weight, default=None)
                if g is not None and g.group == gi:
                    ids.add(v)
    # only vertices inside the sleeve at rest: up to 75 % of the forearm from the elbow (the hand stub's ring sits at
    # 84 %, its wrist outside the cuff)
    e0 = rig.matrix_world @ rig.data.bones[fa].head_local
    w0 = rig.matrix_world @ rig.data.bones[f'{TOK} {S} Hand'].head_local
    L0 = (w0 - e0).length
    probe[S] = sorted(i for i in ids if ((mesh.matrix_world @ me.vertices[i].co) - e0).dot((w0 - e0) / L0) < 0.75 * L0)


def render(path, cull):
    sh.show_backface_culling = cull
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    px = np.array(im.pixels[:]).reshape(RES, RES, 4)[..., :3]
    bpy.data.images.remove(im)
    return (px[..., 0] > 0.9) & (px[..., 1] < 0.1) & (px[..., 2] > 0.9)


YY, XX = np.mgrid[0:RES, 0:RES] + 0.5


def sleeve_mask(p, q, radius=0.07):
    """pixels within `radius` (m) of the forearm segment p-q in the image (row 0 at the bottom, as Blender's pixels):
    only the sleeve and cuff count, not other single-sided cloth in the frame"""
    a2 = np.array(world_to_camera_view(sc, cam, p)[:2]) * RES
    b2 = np.array(world_to_camera_view(sc, cam, q)[:2]) * RES
    d = b2 - a2
    t = np.clip(((XX - a2[0]) * d[0] + (YY - a2[1]) * d[1]) / max(d @ d, 1e-9), 0, 1)
    dist = np.hypot(XX - (a2[0] + t * d[0]), YY - (a2[1] + t * d[1]))
    return dist < radius * RES / cd.ortho_scale


rep = {'fps': FPS, 'views': VIEWS, 'probe_vertices': {s: len(v) for s, v in probe.items()}, 'clips': {}}
rig.animation_data_create()
for act in bpy.data.actions:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    dur = (act.frame_range[1] - act.frame_range[0]) / 24.0
    rc = rep['clips'][act.name] = {}
    for fi, t in enumerate(np.arange(0, dur + 1e-6, 1.0 / FPS)):
        f = act.frame_range[0] + t * 24.0
        sc.frame_set(int(f), subframe=f % 1.0)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = mesh.evaluated_get(dg)
        em = ev.to_mesh()
        P = [ev.matrix_world @ v.co for v in em.vertices]
        bvh = BVHTree.FromPolygons(P, [p.vertices[:] for p in em.polygons])
        ev.to_mesh_clear()
        for S in 'LR':
            pb_f, pb_h = rig.pose.bones[f'{TOK} {S} Forearm'], rig.pose.bones[f'{TOK} {S} Hand']
            e, w = rig.matrix_world @ pb_f.head, rig.matrix_world @ pb_h.head
            ax = (w - e).normalized()
            u = ax.orthogonal().normalized(); v2 = ax.cross(u)
            out = 0
            for i in probe[S]:
                for k in range(12):
                    d = u * math.cos(k * math.pi / 6) + v2 * math.sin(k * math.pi / 6)
                    if bvh.ray_cast(P[i] + d * 0.002, d, 5.0)[0] is None:
                        out += 1
                        break
            r = rc.setdefault(S, {'poke_frames': 0, 'poke_max': 0, 'see': {}})
            if out:
                r['poke_frames'] += 1; r['poke_max'] = max(r['poke_max'], out)
            tgt = (e + w) / 2 * 0.4 + w * 0.6
            for vw in VIEWS:
                d = Vector(DIRS[vw]).normalized()
                cam.location = tgt + d * 3.0
                cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
                p1 = os.path.join(tmp, f'{act.name}_{S}_{vw}_c.png')
                culled = render(p1, True)
                both = render(os.path.join(tmp, 'n.png'), False)
                near = sleeve_mask(e.lerp(w, 0.45), w + ax * 0.03)
                n = int((culled & ~both & near).sum())
                s = r['see'].setdefault(vw, {'max_px': 0, 'frames': 0, 'worst_frame48': None})
                if n:
                    s['frames'] += 1
                if n > s['max_px']:
                    s['max_px'], s['worst_frame48'] = n, fi
                    im = bpy.data.images.load(p1)
                    px = np.array(im.pixels[:]).reshape(RES, RES, 4)
                    px[culled & ~both & near] = (0.0, 1.0, 0.0, 1.0)           # see-through pixels in green
                    im.pixels.foreach_set(px.astype(np.float32).ravel())
                    im.filepath_raw = os.path.join(os.path.dirname(os.path.abspath(OUT)),
                                                   f'sleeve_gate_{act.name}_{S}_{vw}.png')
                    im.save()
                    bpy.data.images.remove(im)
    print('SLEEVE_GATE', act.name, json.dumps(rc))
json.dump(rep, open(OUT, 'w'), indent=1)
print('SLEEVE_GATE done', OUT)
