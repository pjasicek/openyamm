"""The Nobles' rig: work/source.blend -> work/rig.blend.
- Removes the Overseer-only socket bones (PulsePistol, CollarRod, ArcMaul, HipSaber, CollarKey, HolsterPistol,
  Socket_*), keeping their frames: Grip_R = CollarRod's frame (the Overseer's fitted round-handle fist on B_R_Hand:
  handle centre at the bone head, handle axis along the bone's local Z, forward with the arm hanging), Grip_L = its
  mirror on B_L_Hand (the rig is symmetric: X mirrored, Z negated).
- The right fist's finger pose (hes_overseer_codex/work/grip_pose.json, the round handle) and its mirror for the left
  hand ((w, x, y, z) -> (w, -x, -y, z)) go to work/grips.json, applied by the clip author.
Args: none"""
import bpy, os, sys, json
from pathlib import Path
from mathutils import Matrix
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'source.blend'))
rig = bpy.data.objects['Rig']
grip = json.loads((P.parent / 'hes_overseer_codex' / 'work' / 'grip_pose.json').read_text())
S = Matrix.Diagonal((-1, 1, 1, 1)); D = Matrix.Diagonal((1, 1, -1, 1))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
MR = eb['CollarRod'].matrix.copy()
OLD = ['PulsePistol', 'Socket_Muzzle', 'CollarRod', 'Socket_Rod', 'ArcMaul', 'Socket_Maul', 'HipSaber', 'CollarKey',
       'HolsterPistol']
for n in OLD:
    if n in eb: eb.remove(eb[n])


def add(name, parent, M, length=0.05):
    b = eb.new(name); b.head = (0, 0, 0); b.tail = (0, length, 0)
    b.matrix = M; b.parent = eb[parent]; b.use_deform = True    # props ride them (armature modifier)
    return b


add('Grip_R', 'B_R_Hand', MR)
add('Grip_L', 'B_L_Hand', S @ MR @ D)
# the holstered sidearm on the left hip (fam_nobles.png); armature-aligned frame, the mount turns the pistol
add('Holster_L', 'B_Pelvis', Matrix.Translation((0.200, -0.040, 0.800)))
# spell and bolt release at the left palm: between the wrist and the finger roots, in the hand's frame
palm = sum((eb[f'B_L_Finger{d}'].head for d in range(1, 6)), eb['B_L_Hand'].head * 0) / 5
M = eb['B_L_Hand'].matrix.copy(); M.translation = eb['B_L_Hand'].head * 0.35 + palm * 0.65
add('Palm_L', 'B_L_Hand', M)
# the Gatekeeper's Bastion Emitter on the outer left forearm (Z up the forearm, X outward) and his gorget at the throat
from mathutils import Vector
fa = eb['B_L_Forearm']; z = (fa.head - eb['B_L_Hand'].head).normalized(); x = Vector((1, 0, 0)); x = (x - z * x.dot(z)).normalized()
M = Matrix((x, z.cross(x), z)).transposed().to_4x4(); M.translation = (fa.head + eb['B_L_Hand'].head) / 2 + x * 0.13
add('Emitter_L', 'B_L_Forearm', M)
add('Gorget', 'B_Spine2', Matrix.Translation((0.0, -0.235, 1.075)))
bpy.ops.object.mode_set(mode='OBJECT')
mirror = lambda q: [q[0], -q[1], -q[2], q[3]]
R = grip['R']['finger_local']
L = {n.replace('B_R_', 'B_L_').replace('Finger0.001', 'Finger01').replace('Finger0.002', 'Finger02'): mirror(q) for n, q in R.items()}
(P / 'work' / 'grips.json').write_text(json.dumps({'R': R, 'L': L, 'radius_m': grip['R']['radius_m'],
                                                   'source': 'hes_overseer_codex/work/grip_pose.json R (round handle)'}, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'rig.blend'))
print('SOCKETS', [b.name for b in rig.data.bones if b.name.startswith(('Grip', 'Holster', 'Palm', 'Emitter', 'Gorget'))]); sys.stdout.flush(); os._exit(0)
