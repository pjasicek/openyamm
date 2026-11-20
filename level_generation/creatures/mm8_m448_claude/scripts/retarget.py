"""Retarget clips of the source set onto our rig (work/rig_v1.blend, frames cloned from the source by build_rig.py).

World rule (exact): our rest frame is q @ R_src_rest (build_rig.py), so the deformation D = R(t) R_rest^-1 that maps
our rest segment onto the source's posed segment is S(t) R_src_rest^-1 q^-1, i.e. R_ours(t) = S(t): a plain WORLD
rotation copy. (A first version used S R_src^-1 q R_src, which applies the T-pose -> pose rotation to an A-pose mesh.) Pelvis position
= source pelvis (turned 180 degrees) scaled by the pelvis-height ratio. Output keys at the source's 30 fps frames.
H4 test: the same frame through a plain local copy (matrix_basis of the source) is compared per bone (degrees).
Args: -- <in blend> <out blend> <set glb>:<clip>:<ActionName> [...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src_blend, out_blend, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
OFF = json.loads(scene['rig_offsets'])
TURN = Matrix.Rotation(math.pi, 4, 'Z')
names = [b.name for b in rig.data.bones]                                       # parents first
Rr = {n: Matrix([Vector(r) for r in OFF[n]['R_src']]) for n in names}
Q = {n: Quaternion(OFF[n]['q']).to_matrix() for n in names}
ABD_DEG = float(os.environ.get('ARM_ABDUCT_DEG', '0'))
# the chest's forward direction in B_Spine2's local rest frame (character faces -Y); right arm abducts toward -X
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
# sign: a +angle about the forward (-Y) axis turns a hanging arm toward +X, i.e. OUT for the left arm (+X side) and IN
# for the right arm; the first version had the signs swapped and adducted both arms into the body (gob2 G6 trial)
ABD = {'B_L_UpperArm': math.radians(ABD_DEG), 'B_R_UpperArm': -math.radians(ABD_DEG)} if ABD_DEG else {}
report = {}
for item in items:
    glb, clip, act_name = item.rsplit(':', 2)
    before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    new = set(bpy.data.objects) - before
    src = next(o for o in new if o.type == 'ARMATURE')
    srcacts = {x.name.split('@')[-1].split('|')[-1]: x for x in set(bpy.data.actions) - acts_before}
    sact = srcacts[clip]
    src.animation_data.action = sact
    if getattr(sact, 'slots', None) is not None and len(sact.slots):
        src.animation_data.action_slot = sact.slots[0]
    # Blender's glTF import maps the source's seconds to frames at the SCENE rate (24 here), not the file's 30 fps:
    # read it back, or every clip plays 25 % fast (caught by the viewer's clip durations, TEST_DRIVE.md)
    fps_src = scene.render.fps / scene.render.fps_base
    f0, f1 = sact.frame_range
    # keys at the source's own frames (30 fps): resampling to 24 fps turned the attack's 148 deg/frame whip into
    # ~185 deg between keys, which interpolates the wrong way round (TEST_DRIVE.md)
    OUT_FPS = 30.0
    n_out = int(round((f1 - f0) / fps_src * OUT_FPS))
    SW = TURN @ src.matrix_world
    # pelvis height ratio from the rest poses
    for pb in src.pose.bones:
        pass
    k = rig.data.bones['B_Pelvis'].head_local.z / (SW @ src.data.bones['B_Pelvis'].head_local).z
    if act_name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[act_name])
    act = bpy.data.actions.new(act_name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    h4 = []
    for i in range(n_out + 1):
        sf = f0 + i / OUT_FPS * fps_src
        scene.frame_set(int(math.floor(sf)), subframe=sf - math.floor(sf))
        for n in names:
            S = (SW @ src.pose.bones[n].matrix).to_3x3().normalized()
            R = S                                               # source frames drive limbs
            if n in ('B_Neck', 'B_Head'):
                # Keep the Ratman's horizontal neck and skull instead of imposing a human neck rest angle.
                R = S @ Rr[n].inverted() @ rig.data.bones[n].matrix_local.to_3x3()
            if n in ABD:
                # proportion compensation (G2/G6): narrower shoulders + wider hips than the source -> constant extra
                # abduction of the upper arm about the chest's forward axis, away from the body
                ch = rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix
                fwd = (ch.to_3x3() @ CHEST_FWD).normalized()
                R = Matrix.Rotation(ABD[n], 3, fwd) @ R
            M = R.to_4x4()
            pb = rig.pose.bones[n]
            if n == 'B_Pelvis':
                M.translation = (SW @ src.pose.bones[n].matrix).translation * k
            else:
                M.translation = rig.matrix_world @ pb.head
            pb.rotation_mode = 'QUATERNION'
            pb.matrix = rig.matrix_world.inverted() @ M
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=i)
            if i % 4 == 0:
                qs = src.pose.bones[n].matrix_basis.to_quaternion()
                qo = pb.matrix_basis.to_quaternion()
                h4.append((n, math.degrees(qs.rotation_difference(qo).angle)))
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n_out
    rig.animation_data.action = None
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    for x in set(bpy.data.actions) - acts_before - {act}:
        bpy.data.actions.remove(x)
    scene.render.fps = 24; scene.render.fps_base = 1               # keep the import rate stable for the next clip
    by = {}
    for n, d in h4:
        by[n] = max(by.get(n, 0), min(d, 360 - d))
    worst = sorted(by.items(), key=lambda kv: -kv[1])[:5]
    arm_bones = [n for n in by if any(t in n for t in ('UpperArm', 'Forearm', 'Hand', 'Clavicle'))]
    print(f'RETARGET {act_name} <- {clip}: {n_out + 1} frames = {n_out / OUT_FPS:.3f} s (source {(f1 - f0) / fps_src:.3f} s); H4 local-copy vs world rule, max deg: arm bones '
          f'{round(max(by[n] for n in arm_bones), 2)}, worst {[(n, round(d, 1)) for n, d in worst]}')
    report[act_name] = {'clip': clip, 'frames': n_out + 1, 'h4_local_copy_max_deg': {n: round(d, 2) for n, d in by.items()}}
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
scene.render.fps = 30; scene.render.fps_base = 1
prev = json.loads(scene.get('retarget_report', '{}')); prev.update(report)
scene['retarget_report'] = json.dumps(prev)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
