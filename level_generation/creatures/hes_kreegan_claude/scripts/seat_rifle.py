"""Seat the rifle (work/rifle.blend, make_rifle.py) on the right hand: prop space is the rifle frame of rifle_fit.py
(work/rifle_frame.json 'rifle_in_hand', rifle -> B_R_Hand local), so the pistol grip lies in the right fist's tunnel
and the handguard where the left fist closes in the source's hold. Adds bone 'Rifle' (child of B_R_Hand, at the grip,
+Y along the barrel, +Z up the grip), 'RifleGlow' (its child, same frame: the emissive parts) and 'Socket_Muzzle' (non-deforming, at the emitter tip: the shot leaves there).
The prop stays its own object 'Rifle', 100 % on bone Rifle (rigid; split into an attachment GLB at export).
Copies every action unchanged. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
for o in [o for o in bpy.data.objects if o.name.startswith('Rifle')]:
    bpy.data.objects.remove(o, do_unlink=True)
with bpy.data.libraries.load(os.path.join(common.WORK, 'rifle.blend'), link=False) as (s_, d_):
    d_.objects = ['Rifle']
gun = d_.objects[0]; scene.collection.objects.link(gun)
Hr = Matrix(json.load(open(os.path.join(common.WORK, 'rifle_frame.json')))['rifle_in_hand'])
M = rig.data.bones['B_R_Hand'].matrix_local @ Hr                       # rifle -> armature (rest)
gun.data.transform(M); gun.matrix_world = Matrix()
grip_w = M @ Vector((0, 0, 0)); barrel_w = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
muzzle_w = M @ Vector(gun['muzzle'])
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for n in ('Socket_Muzzle', 'RifleGlow', 'Rifle'):
    if n in eb:
        eb.remove(eb[n])
bb = eb.new('Rifle'); bb.head = grip_w; bb.tail = grip_w + barrel_w * 0.12; bb.parent = eb['B_R_Hand']
bb.align_roll(M.to_3x3() @ Vector((0, 0, 1)))
gb = eb.new('RifleGlow'); gb.head = grip_w; gb.tail = grip_w + barrel_w * 0.10; gb.parent = bb; gb.roll = bb.roll
k = eb.new('Socket_Muzzle'); k.head = muzzle_w; k.tail = muzzle_w + barrel_w * 0.04; k.parent = bb; k.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
gun.parent = rig
# the glowing parts (material 1: emitter tip, power-cell windows) ride bone RifleGlow, so they split into their own
# attachment (tools/split_attachment.py takes one primitive per item)
glow_v = {v for p in gun.data.polygons if p.material_index == 1 for v in p.vertices}
gun.vertex_groups.new(name='Rifle').add([i for i in range(len(gun.data.vertices)) if i not in glow_v], 1.0, 'REPLACE')
gun.vertex_groups.new(name='RifleGlow').add(sorted(glow_v), 1.0, 'REPLACE')
m = gun.modifiers.new('Armature', 'ARMATURE'); m.object = rig
print('SEAT rifle barrel world', [round(v, 3) for v in barrel_w], 'grip', [round(v, 3) for v in grip_w],
      'muzzle', [round(v, 3) for v in muzzle_w], 'tris', sum(len(p.vertices) - 2 for p in gun.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
