"""Head close-ups for diagnosis (rework 2026-10-30): solid shading + wire overlay, front / q34 / both profiles.
Args: -- <file .blend|.glb> <out dir> <prefix> [--align <fit blend>] [--pose ACTION@FRAME] [--tex]
The head centre is MM9 'Bip01 Head' (from the file's rig or the --align blend's MM9_Rig). A raw Meshy GLB is aligned
to the fit blend's Body by Kabsch on the head vertices (same vertex order after remove_doubles)."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
src, outd, pre = a[0], a[1], a[2]
opt = {a[i]: a[i + 1] for i in range(3, len(a) - 1) if a[i].startswith('--')}
TEX = '--tex' in a
os.makedirs(outd, exist_ok=True)
ref_head = None
if '--align' in opt:
    bpy.ops.wm.open_mainfile(filepath=opt['--align'])
    rig = bpy.data.objects['MM9_Rig']
    ref_head = rig.matrix_world @ rig.data.bones['Bip01 Head'].head_local
    ref_M = (rig.matrix_world @ rig.data.bones['Bip01 Head'].matrix_local).to_3x3()
    fb = bpy.data.objects['Body']
    REF = np.array([tuple(fb.matrix_world @ v.co) for v in fb.data.vertices])
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
rigs = [o for o in sc.objects if o.type == 'ARMATURE']
meshes = [o for o in sc.objects if o.type == 'MESH' and o.name in ('Body', 'Wmut')]
if not meshes:
    meshes = [o for o in sc.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')]
for o in sc.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
if rigs and '--pose' in opt:
    act, tsec = opt['--pose'].split('@')
    A = next(x for x in bpy.data.actions if x.name == act or x.name.startswith(act + '_') or x.name.startswith(act))
    rigs[0].animation_data_create(); rigs[0].animation_data.action = A
    if hasattr(rigs[0].animation_data, 'action_slot') and A.slots:
        rigs[0].animation_data.action_slot = A.slots[0]
    fps = sc.render.fps / sc.render.fps_base
    f = float(tsec) * fps
    sc.frame_set(int(f), subframe=f - int(f))
elif rigs:
    if rigs[0].animation_data:
        rigs[0].animation_data.action = None
    for pb in rigs[0].pose.bones:
        pb.matrix_basis.identity()
bpy.context.view_layer.update()
if rigs:
    r = rigs[0]
    hb = r.pose.bones['Bip01 Head']
    head = r.matrix_world @ hb.head
    HM = (r.matrix_world @ hb.matrix).to_3x3()
    # creature forward: MM9 rig faces -Y in Blender after import
else:
    # raw meshy: merge, align to the fit by Kabsch on vertices near the fitted head
    o = meshes[0]
    bm = bmesh.new()
    for m in meshes:
        t = bmesh.new(); t.from_mesh(m.data); t.transform(m.matrix_world)
        me_t = bpy.data.meshes.new('t'); t.to_mesh(me_t); bm.from_mesh(me_t); t.free()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    P = np.array([tuple(v.co) for v in bm.verts])
    sel = np.linalg.norm(REF - np.array(ref_head), axis=1) < 0.12
    X, Y = P[sel], REF[sel]
    cx, cy = X.mean(0), Y.mean(0)
    s = np.sqrt(((Y - cy) ** 2).sum() / ((X - cx) ** 2).sum())
    U, S_, Vt = np.linalg.svd((X - cx).T @ (Y - cy))
    d = np.sign(np.linalg.det(U @ Vt))
    R = (U @ np.diag([1, 1, d]) @ Vt).T
    P2 = (s * (R @ (P - cx).T)).T + cy
    for v, p in zip(bm.verts, P2):
        v.co = p
    me = bpy.data.meshes.new('raw'); bm.to_mesh(me)
    for m in meshes:
        m.hide_render = True
    o = bpy.data.objects.new('raw', me); sc.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    meshes = [o]
    head = ref_head
    HM = ref_M
    print('ALIGN rms', float(np.sqrt(((P2[sel] - Y) ** 2).sum(1).mean())), 'scale', s)
# render setup
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE' if TEX else 'SINGLE'
sh.single_color = (0.72, 0.72, 0.74)
sc.render.resolution_x = sc.render.resolution_y = 640
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.32, 0.33, 0.36)
# wire overlay: evaluated copy with a wireframe modifier
if not TEX:
    for m in meshes:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = m.evaluated_get(dg)
        me2 = bpy.data.meshes.new_from_object(ev)
        me2.transform(m.matrix_world)
        w = bpy.data.objects.new(m.name + '_wire', me2); sc.collection.objects.link(w)
        mod = w.modifiers.new('wf', 'WIREFRAME'); mod.thickness = 0.0006; mod.use_replace = True; mod.use_even_offset = False
        mat = bpy.data.materials.new('wire'); mat.diffuse_color = (0.08, 0.08, 0.1, 1); me2.materials.append(mat)
        w.color = (0.05, 0.05, 0.08, 1)
    sh.color_type = 'OBJECT'
    for m in meshes:
        m.color = (0.75, 0.75, 0.77, 1)
# MM9 head frame: z = face forward (down-forward in the bind pose), x = up the head, y = the creature's right
F, U, SIDE = HM.col[2].normalized(), HM.col[0].normalized(), HM.col[1].normalized()
hc = Vector(head) + F * float(opt.get('--fwd', 0.05)) + U * float(opt.get('--up', 0.0))
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(opt.get('--scale', 0.24)); cd.clip_start = 0.01
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, (f, s_, u) in (('front', (1, 0, 0.05)), ('q34', (1, 0.7, 0.15)), ('profR', (0, 1, 0.05)),
                       ('profL', (0, -1, 0.05)), ('below', (0.6, 0, -0.8))):
    dv = (F * f + SIDE * s_ + U * u).normalized()
    cam.location = hc + dv * 2
    zc = dv; xc = U.cross(zc).normalized(); yc = zc.cross(xc)
    cam.matrix_world = Matrix((xc, yc, zc)).transposed().to_4x4()
    cam.location = hc + dv * 2
    sc.render.filepath = os.path.join(outd, f'{pre}_{nm}.png')
    bpy.ops.render.render(write_still=True)
print('DIAG done', pre, tuple(head))
