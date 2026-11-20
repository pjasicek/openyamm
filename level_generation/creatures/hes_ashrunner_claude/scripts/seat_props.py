"""Seat the three guns in the right fist and the tier gear on the body (after seat_rifle.py's rule): every gun shares the
rifle frame of rifle_fit.py (work/rifle_frame.json 'rifle_in_hand': origin = the right fist's grip tunnel, +Z up the
grip, +Y along the barrel), so the clips that drive bone Rifle (rifle_drive.py, support_hand.py) carry the carbine too,
and the pistol sits in the same fist.
- gun bones (children of B_R_Hand, the same rest frame): Rifle / Carbine / Pistol, each with a <Gun>Glow child (the
  emissive parts, split into their own attachment) and a non-deforming muzzle socket (Socket_Muzzle, _C, _P);
- tier gear (rigid, children of their body bone, the attachment node = the bone): ChestPlate (B_Spine2, tier B) and
  Buckler + BucklerGlow (B_L_Forearm, tier C), from work/chest_plate.blend and work/buckler.blend (make_gear.py), when
  they exist.
Objects keep their names, 100 % on their bone; every action is copied unchanged. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
GUNS = [('rifle', 'Rifle', 'Rifle', 'RifleGlow', 'Socket_Muzzle'), ('carbine', 'Carbine', 'Carbine', 'CarbineGlow', 'Socket_Muzzle_C'),
        ('pistol', 'Pistol', 'Pistol', 'PistolGlow', 'Socket_Muzzle_P')]
GUNS = [] if os.environ.get('GEAR_ONLY') else GUNS   # GEAR_ONLY=1: add the tier gear to a finished clip blend
GEAR = [('chest_plate', 'ChestPlate', 'B_Spine2', None), ('buckler', 'Buckler', 'B_L_Forearm', 'BucklerGlow')]
names = [g[1] for g in GUNS] + [g[1] for g in GEAR]
for o in [o for o in bpy.data.objects if o.name in names]:
    bpy.data.objects.remove(o, do_unlink=True)
Hr = Matrix(json.load(open(os.path.join(common.WORK, 'rifle_frame.json')))['rifle_in_hand'])
M = rig.data.bones['B_R_Hand'].matrix_local @ Hr
loaded = []
for blend, obn, bone, glow, sock in GUNS:
    with bpy.data.libraries.load(os.path.join(common.WORK, f'{blend}.blend'), link=False) as (s_, d_):
        d_.objects = [obn]
    gun = d_.objects[0]; scene.collection.objects.link(gun)
    gun.data.transform(M); gun.matrix_world = Matrix(); loaded.append((gun, bone, glow, sock, M @ Vector(gun['muzzle'])))
gear = []
for blend, obn, parent, glow in GEAR:
    p = os.path.join(common.WORK, f'{blend}.blend')
    if not os.path.exists(p):
        continue
    with bpy.data.libraries.load(p, link=False) as (s_, d_):
        d_.objects = [obn]
    ob = d_.objects[0]; scene.collection.objects.link(ob); gear.append((ob, obn, parent, glow))
grip_w = M @ Vector((0, 0, 0)); barrel_w = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for g in GUNS:
    for n in g[2:]:
        if n in eb:
            eb.remove(eb[n])
for _, n, _, glow in gear:
    for x in (n, glow):
        if x and x in eb:
            eb.remove(eb[x])
for gun, bone, glow, sock, muzzle_w in loaded:
    bb = eb.new(bone); bb.head = grip_w; bb.tail = grip_w + barrel_w * 0.12; bb.parent = eb['B_R_Hand']
    bb.align_roll(M.to_3x3() @ Vector((0, 0, 1)))
    gb = eb.new(glow); gb.head = grip_w; gb.tail = grip_w + barrel_w * 0.10; gb.parent = bb; gb.roll = bb.roll
    k = eb.new(sock); k.head = muzzle_w; k.tail = muzzle_w + barrel_w * 0.04; k.parent = bb; k.use_deform = False
for ob, n, parent, glow in gear:
    pb = eb[parent]
    b = eb.new(n); b.head = pb.head; b.tail = pb.tail; b.roll = pb.roll; b.parent = pb
    if glow:
        g = eb.new(glow); g.head = pb.head; g.tail = pb.tail; g.roll = pb.roll; g.parent = b
bpy.ops.object.mode_set(mode='OBJECT')
for gun, bone, glow, sock, muzzle_w in loaded:
    gun.parent = rig
    gv = {v for p in gun.data.polygons if p.material_index == 1 for v in p.vertices}
    gun.vertex_groups.new(name=bone).add([i for i in range(len(gun.data.vertices)) if i not in gv], 1.0, 'REPLACE')
    gun.vertex_groups.new(name=glow).add(sorted(gv), 1.0, 'REPLACE')
    m = gun.modifiers.new('Armature', 'ARMATURE'); m.object = rig
    print('SEAT', bone, 'tris', sum(len(p.vertices) - 2 for p in gun.data.polygons), 'muzzle', [round(v, 3) for v in muzzle_w])
for ob, n, parent, glow in gear:
    ob.parent = rig
    gv = {v for p in ob.data.polygons if p.material_index == 1 for v in p.vertices} if glow else set()
    ob.vertex_groups.new(name=n).add([i for i in range(len(ob.data.vertices)) if i not in gv], 1.0, 'REPLACE')
    if glow:
        ob.vertex_groups.new(name=glow).add(sorted(gv), 1.0, 'REPLACE')
    m = ob.modifiers.new('Armature', 'ARMATURE'); m.object = rig
    print('SEAT gear', n, 'on', parent, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons))
print('SEAT barrel world', [round(v, 3) for v in barrel_w], 'grip', [round(v, 3) for v in grip_w])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
