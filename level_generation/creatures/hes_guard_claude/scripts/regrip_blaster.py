"""Re-seat the blaster in the right fist (user review 2026-10-20: the fist held only the top of the grip, under the
receiver, and the grip stuck out below and in front of the fingers). seat_blaster.py put the prop's +Z on the fist's
solved grip tunnel, but the grip itself is raked 15 deg toward the barrel and the fingers wrap at the tunnel's upper
end. This applies one correction in the Blaster bone's frame (prop axes: X across, Y along the barrel, Z up the grip;
pivot at the grip centre): a rotation of A deg about X (positive tips the barrel up and swings the grip bottom forward,
along the fingers), then a shift (DX, DY, DZ) in metres. The gun mesh, the bone 'Blaster' and 'Socket_Muzzle' move together; the clips key the Blaster bone at its rest,
so every clip follows. Run on the textured master (rig_v6) and on the clip chain's rig_v5 (sync_actions keeps both).
Build setting (rebuild.sh, after seat_blaster.py): A=25 DZ=0.005. Env A, DX, DY, DZ; with SHOTS=<dir> also renders
close-ups of the gun hand (EEVEE, both sides and below) at the listed action:frame picks, without saving. Args: -- <in blend> <out blend | -> [action:frame ...]"""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, picks = a[0], a[1], a[2:]
A = float(os.environ.get('A', '0')); D = Vector(tuple(float(os.environ.get(k, '0')) for k in ('DX', 'DY', 'DZ')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; gun = bpy.data.objects['Blaster']; scene = bpy.context.scene
Mb = rig.matrix_world @ rig.data.bones['Blaster'].matrix_local
C = Matrix.Translation(D) @ Matrix.Rotation(math.radians(A), 4, 'X')
T = Mb @ C @ Mb.inverted()                                   # world rest-space correction
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
gun.data.transform(gun.matrix_world.inverted() @ T @ gun.matrix_world)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
inv = rig.matrix_world.inverted()
for n in ('Blaster', 'Socket_Muzzle'):
    eb = rig.data.edit_bones[n]
    eb.matrix = inv @ T @ rig.matrix_world @ eb.matrix
bpy.ops.object.mode_set(mode='OBJECT')
print('REGRIP A', A, 'shift', tuple(round(v, 3) for v in D))
if out != '-':
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
shots = os.environ.get('SHOTS')
if shots:
    os.makedirs(shots, exist_ok=True)
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scene.render.resolution_x = scene.render.resolution_y = 400
    w = bpy.data.worlds.new('W') if scene.world is None else scene.world
    scene.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.6, 0.6, 0.62, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.2
    ld = bpy.data.lights.new('Sun', 'SUN'); ld.energy = 3; lo = bpy.data.objects.new('Sun', ld); scene.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(40), 0, math.radians(30))
    cd = bpy.data.cameras.new('Cam'); cd.lens = 50; cam = bpy.data.objects.new('Cam', cd); scene.collection.objects.link(cam); scene.camera = cam
    for pick in picks:
        act, fr = pick.split(':')
        ac = bpy.data.actions[act]; rig.animation_data.action = ac
        if len(ac.slots):
            rig.animation_data.action_slot = ac.slots[0]
        scene.frame_set(int(fr))
        M = rig.matrix_world @ rig.pose.bones['Blaster'].matrix
        c = M.translation; x = M.to_3x3() @ Vector((1, 0, 0)); z = M.to_3x3() @ Vector((0, 0, 1)); y = M.to_3x3() @ Vector((0, 1, 0))
        for tag, d in (('xpos', x), ('xneg', -x), ('below', -z), ('behind', -y)):
            cam.location = c + d.normalized() * 0.42 + y * 0.03
            cam.rotation_euler = (c + y * 0.03 - cam.location).to_track_quat('-Z', 'Y' if tag != 'below' else 'Z').to_euler()
            scene.render.filepath = os.path.join(shots, f'{act}{fr}_{tag}.png'); bpy.ops.render.render(write_still=True)
