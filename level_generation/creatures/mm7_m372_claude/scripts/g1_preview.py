"""G1: preview candidate clips on their own mannequins before modelling (front and side rows per clip).
Mixamo clips play on the library's Warrok character re-bound to the clip's skeleton (as mm8_m412_claude); humanoid-set
clips play on the set's own character (armature turned to face -Y, as mm6_natm_claude/scripts/rpg_preview.py).
Args: -- <out dir> <frames per clip> <item> [...]
  item = mx:<Mixamo file name without .fbx>  or  hs:<set glb name>:<clip suffix>
Writes <out dir>/<slug>_<view>_<i>.png and <out dir>/frames.json (rows for the sheet)."""
import bpy, sys, os, json, math
from pathlib import Path
from mathutils import Vector, Matrix

a = sys.argv[sys.argv.index('--') + 1:]
out, n, items = Path(a[0]), int(a[1]), a[2:]
out.mkdir(parents=True, exist_ok=True)
REPO = Path(__file__).resolve().parents[4]
MX = REPO / 'anim_library/mixamo'
HS = REPO / 'anim_library/humanoid_set'


def clay(scene):
    scene.render.engine = 'BLENDER_WORKBENCH'
    sh = scene.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.7, 0.68, 0.65)
    sh.show_cavity = True; sh.background_type = 'VIEWPORT'; sh.background_color = (0.82, 0.82, 0.8)
    scene.render.resolution_x, scene.render.resolution_y = 300, 420


def load_mixamo(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(MX / 'characters/warrok_w_kurniawan.fbx'))
    char = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    before = set(bpy.data.objects)
    path = MX / (name + '.fbx')
    if not path.exists():
        path = next(MX.glob('packs/*/' + name + '.fbx'))
    bpy.ops.import_scene.fbx(filepath=str(path))
    src = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    act = src.animation_data.action
    T = {b.name: src.matrix_world @ src.data.bones[b.name].matrix_local @ (char.matrix_world @ b.matrix_local).inverted()
         for b in char.data.bones if b.name in src.data.bones}
    for mesh in [o for o in before if o.type == 'MESH']:
        W = mesh.matrix_world.copy()
        for v in mesh.data.vertices:
            ws = [(T[mesh.vertex_groups[g.group].name], g.weight) for g in v.groups
                  if mesh.vertex_groups[g.group].name in T]
            tot = sum(w for _, w in ws)
            if tot:
                p = W @ v.co
                v.co = W.inverted() @ (sum((m @ p * w for m, w in ws), Vector()) / tot)
        for mod in mesh.modifiers:
            if mod.type == 'ARMATURE':
                mod.object = src
        mesh.parent = src; mesh.matrix_world = W
    bpy.data.objects.remove(char, do_unlink=True)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent is not src:
            o.hide_render = True
    return src, act, bpy.context.scene.render.fps / bpy.context.scene.render.fps_base


def load_set(glb, clip):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(HS / (glb + '.glb')))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    arm.rotation_mode = 'XYZ'; arm.rotation_euler = (0, 0, math.pi)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent is not arm:
            o.hide_render = True
    acts = {x.name.split('@')[-1].split('|')[-1]: x for x in bpy.data.actions}
    act = acts.get(clip) or next(x for k, x in acts.items() if k.endswith(clip))
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    return arm, act, bpy.context.scene.render.fps / bpy.context.scene.render.fps_base


rows = []
for it in items:
    kind, rest = it.split(':', 1)
    if kind == 'mx':
        arm, act, fps = load_mixamo(rest); label = 'mx ' + rest
    else:
        g, c = rest.split(':'); arm, act, fps = load_set(g, c); label = 'hs ' + c
    scene = bpy.context.scene; clay(scene)
    f0, f1 = act.frame_range
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
    scene.frame_set(int(f0)); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    zs = []
    for m in meshes:
        e = m.evaluated_get(dg); me = e.to_mesh()
        zs += [(m.matrix_world @ v.co).z for v in list(me.vertices)[::20]]; e.to_mesh_clear()
    H = max(zs) - min(zs); zc = min(zs) + H / 2
    slug = ''.join(ch if ch.isalnum() else '_' for ch in label)
    for view, ang in (('front', 0.0), ('side', 90.0)):
        row = []
        for i in range(n):
            f = f0 + (f1 - f0) * i / max(n - 1, 1)
            scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
            r = math.radians(ang)
            # Mixamo faces +Y, the set (turned) faces -Y: camera in front of each, centred on the hips each frame
            F = Vector((0, 1, 0)) if kind == 'mx' else Vector((0, -1, 0))
            d = Matrix.Rotation(r, 3, 'Z') @ F
            hb = next(b for b in arm.pose.bones if b.name.endswith(('Hips', 'B_Pelvis')))
            hp = arm.matrix_world @ hb.head
            tgt = Vector((hp.x, hp.y, zc))
            cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = H * 1.45
            cam = bpy.data.objects.new('c', cd); scene.collection.objects.link(cam)
            cam.location = tgt + d * 8
            cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
            scene.camera = cam
            p = out / f'{slug}_{view}_{i}.png'; scene.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam, do_unlink=True)
            row.append(str(p))
        rows.append({'label': f'{label} [{view}] {(f1 - f0) / fps:.2f}s', 'frames': row})
    print('G1', label, 'seconds', round((f1 - f0) / fps, 3))
json.dump(rows, open(out / 'frames.json', 'w'), indent=1)
