"""Build a user-friendly posing file for blocking a clip by hand (e.g. Attack2).

Args: source_action out_blend   (run on work/final_v1.blend)
The file gets:
  - control bones CTRL_Hand/Elbow/Foot/Knee_{L,R}: arms and legs follow them through IK (hand and foot also copy the
    control's rotation), so posing is grab/rotate of a few handles; body bones Hips/Spine/Spine1/Spine2/Neck/Head and
    both clavicles are posed directly; fingers, twist bones and the sword are hidden (handled by the ingest),
  - action <source>-based draft 'Attack2' keyed on frames 1,4,7,10,13,16 (native a-f) and 19 (ready pose),
  - auto-keying in Replace mode: moving a handle on a key frame updates that key, elsewhere nothing is recorded,
  - timeline markers a-f, a front-orthographic reference image of the native frame for the current time
    (visible in Front view, Numpad 1), and an orthographic front camera.
"""
import bpy, sys, os, json, math
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

args = sys.argv[sys.argv.index('--') + 1:]
source_action, out_blend = args[0], os.path.abspath(args[1])
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, '..', 'mm6_goblin', 'stage1_20261006', 'source', 'frames')
KEYS = [(1, 'a'), (4, 'b'), (7, 'c'), (10, 'd'), (13, 'e'), (16, 'f'), (19, 'ready')]
SIDES = (('Left', 'L'), ('Right', 'R'))
BODY = ['Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'LeftShoulder', 'RightShoulder']

rig = bpy.data.objects['Peasant_Rig']
scene = bpy.context.scene
mw = rig.matrix_world.copy()
inv = mw.inverted()


# ---------------------------------------------------------------- sample the draft poses
def sample(action, frame):
    rig.animation_data.action = bpy.data.actions[action]
    scene.frame_set(frame)
    data = {'local': {b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in rig.pose.bones}}
    for side, s in SIDES:
        data['hand' + s] = rig.pose.bones[f'mixamorig:{side}Hand'].matrix.copy()
        data['foot' + s] = rig.pose.bones[f'mixamorig:{side}Foot'].matrix.copy()
        sh = rig.pose.bones[f'mixamorig:{side}Arm'].head.copy()
        el = rig.pose.bones[f'mixamorig:{side}ForeArm'].head.copy()
        wr = rig.pose.bones[f'mixamorig:{side}Hand'].head.copy()
        line = (wr - sh).normalized(); off = (el - sh) - line * (el - sh).dot(line)
        data['elbowJ' + s] = el.copy()
        data['elbow' + s] = el + (off.normalized() if off.length > 1e-4 else Vector((0, 1, 0))) * 0.30
        hp = rig.pose.bones[f'mixamorig:{side}UpLeg'].head.copy()
        kn = rig.pose.bones[f'mixamorig:{side}Leg'].head.copy()
        an = rig.pose.bones[f'mixamorig:{side}Foot'].head.copy()
        line = (an - hp).normalized(); off = (kn - hp) - line * (kn - hp).dot(line)
        data['kneeJ' + s] = kn.copy()
        data['knee' + s] = kn + (off.normalized() if off.length > 1e-3 else Vector((0, -1, 0))) * 0.40
    return data


samples = {f: sample(source_action if f < 19 else 'Standing', f if f < 19 else 1) for f, _ in KEYS}
rig.animation_data.action = None
P.reset(rig)

# ---------------------------------------------------------------- control bones
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for side, s in SIDES:
    for name, src in (('Hand', 'Hand'), ('Foot', 'Foot')):
        b = eb.new(f'CTRL_{name}_{s}'); ref = eb[f'mixamorig:{side}{src}']
        b.head, b.tail, b.roll = ref.head.copy(), ref.head + (ref.tail - ref.head).normalized() * 0.12, ref.roll
        b.use_deform = False; b.parent = None
    for name, joint, d in (('Elbow', 'ForeArm', Vector((0, 0.3, 0))), ('Knee', 'Leg', Vector((0, -0.4, 0)))):
        b = eb.new(f'CTRL_{name}_{s}'); ref = eb[f'mixamorig:{side}{joint}']
        b.head = ref.head + d; b.tail = b.head + Vector((0, 0, 0.06)); b.use_deform = False; b.parent = None
bpy.ops.object.mode_set(mode='POSE')


def add_ik(side, s, lower, ctrl, pole, end, angle):
    pb = rig.pose.bones[f'mixamorig:{side}{lower}']
    c = pb.constraints.new('IK'); c.name = 'POSE_IK'
    c.target = rig; c.subtarget = f'CTRL_{ctrl}_{s}'; c.pole_target = rig; c.pole_subtarget = f'CTRL_{pole}_{s}'
    c.chain_count = 2; c.pole_angle = angle; c.use_tail = True
    e = rig.pose.bones[f'mixamorig:{side}{end}'].constraints.new('COPY_ROTATION'); e.name = 'POSE_ROT'
    e.target = rig; e.subtarget = f'CTRL_{ctrl}_{s}'
    return c


def place_controls(data):
    for side, s in SIDES:
        for ctrl, key in (('Hand', 'hand'), ('Foot', 'foot')):
            m = data[key + s].copy()
            rig.pose.bones[f'CTRL_{ctrl}_{s}'].matrix = m
        for ctrl, key in (('Elbow', 'elbow'), ('Knee', 'knee')):
            pb = rig.pose.bones[f'CTRL_{ctrl}_{s}']
            pb.matrix = Matrix.Translation(data[key + s]) @ pb.bone.matrix_local.to_3x3().to_4x4()
    bpy.context.view_layer.update()


def apply_body(data):
    for b in rig.pose.bones:
        if b.name.startswith('CTRL_'):
            continue
        q, loc, sc = data['local'][b.name]
        b.rotation_quaternion = q; b.location = loc; b.scale = sc
    for side, _ in SIDES:                                   # chain bones are driven by the constraints
        for part in ('Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot'):
            pb = rig.pose.bones[f'mixamorig:{side}{part}']
            pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    bpy.context.view_layer.update()


# pole angles: choose per chain so the solved elbow/knee matches the draft (frame 'a')
iks = {}
for side, s in SIDES:
    for lower, ctrl, pole, end, joint in (('ForeArm', 'Hand', 'Elbow', 'Hand', 'ForeArm'),
                                          ('Leg', 'Foot', 'Knee', 'Foot', 'Leg')):
        iks[(side, lower)] = add_ik(side, s, lower, ctrl, pole, end, 0.0)


def joint_error(side, lower, joint):
    err = 0.0
    for f in (1, 4, 7, 10, 13, 16):
        data = samples[f]
        apply_body(data); place_controls(data)
        s = 'L' if side == 'Left' else 'R'
        err += (rig.pose.bones[f'mixamorig:{side}{joint}'].head - data[('elbowJ' if lower == 'ForeArm' else 'kneeJ') + s]).length
    return err / 6


for (side, lower), c in iks.items():
    joint = 'ForeArm' if lower == 'ForeArm' else 'Leg'
    best = None
    for deg in range(-180, 180, 15):
        c.pole_angle = math.radians(deg)
        e = joint_error(side, lower, joint)
        if best is None or e < best[0]:
            best = (e, deg)
    for deg in range(best[1] - 14, best[1] + 15, 2):
        c.pole_angle = math.radians(deg)
        e = joint_error(side, lower, joint)
        if e < best[0]:
            best = (e, deg)
    c.pole_angle = math.radians(best[1])
    print('POLE', side, lower, best[1], 'error', round(best[0], 4))

# ---------------------------------------------------------------- keyed draft
action = bpy.data.actions.new('Attack2'); action.use_fake_user = True
rig.animation_data.action = action
KEYED = [b for b in rig.pose.bones if b.name.startswith('CTRL_') or b.name[10:] in BODY
         or ('Hand' in b.name and b.name[10:] not in ('LeftHand', 'RightHand')) or b.name == 'Sword']
for f, label in KEYS:
    data = samples[f]
    apply_body(data); place_controls(data)
    for b in KEYED:
        b.keyframe_insert('rotation_quaternion', frame=f)
        b.keyframe_insert('location', frame=f)
        if b.name == 'Sword':
            b.keyframe_insert('scale', frame=f)
    scene.timeline_markers.new(label, frame=f)
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
action['posing_keys'] = json.dumps([f for f, _ in KEYS])
for name in list(bpy.data.actions.keys()):
    if name != 'Attack2':
        bpy.data.actions[name].use_fake_user = False

# ---------------------------------------------------------------- visibility, colours
coll_ctrl = rig.data.collections.new('Controls'); coll_body = rig.data.collections.new('Body')
coll_rest = rig.data.collections.new('Internals')
for b in rig.data.bones:
    (coll_ctrl if b.name.startswith('CTRL_') else coll_body if b.name[10:] in BODY else coll_rest).assign(b)
    if b.name.startswith('CTRL_'):
        b.color.palette = 'THEME01' if b.name.endswith('_R') else 'THEME04'
    elif b.name[10:] in BODY:
        b.color.palette = 'THEME03'
coll_rest.is_visible = False
rig.show_in_front = True
rig.data.display_type = 'OCTAHEDRAL'
for b in rig.pose.bones:
    if b.name.startswith('CTRL_'):
        b.custom_shape = None
        if 'Hand' in b.name or 'Foot' in b.name:
            b.lock_scale = (True, True, True)
        else:
            b.lock_rotation = (True, True, True); b.lock_rotation_w = True; b.lock_scale = (True, True, True)

# ---------------------------------------------------------------- native reference sequence
from_frames = {1: 'gobata0', 4: 'gobatb0', 7: 'gobatc0', 10: 'gobatd0', 13: 'gobate0', 16: 'gobatf0', 19: 'gobsta0'}
ref_dir = os.path.join(os.path.dirname(out_blend), 'ref'); os.makedirs(ref_dir, exist_ok=True)
import shutil
for f in range(1, 20):
    key = max(k for k in from_frames if k <= f)
    shutil.copyfile(os.path.join(FRAMES, from_frames[key] + '.png'), os.path.join(ref_dir, f'ref_{f:04d}.png'))
img = bpy.data.images.load(os.path.join(ref_dir, 'ref_0001.png')); img.source = 'SEQUENCE'
ref = bpy.data.objects.new('REF_native_sprite', None)
scene.collection.objects.link(ref)
ref.empty_display_type = 'IMAGE'; ref.data = img
ref.image_user.frame_duration = 19; ref.image_user.frame_start = 1; ref.image_user.use_auto_refresh = True
PX = 1.57 / 256.0                                         # standing sprite is 256 px tall
ref.empty_display_size = 355 * PX
ref.empty_image_offset = (-186.0 / 355.0, 0.0)            # standing body centre over x = 0, feet on z = 0
ref.rotation_euler = (math.radians(90), 0, 0)
ref.location = (0, 0.45, 0)
ref.empty_image_depth = 'BACK'
ref.show_empty_image_perspective = False
ref.show_empty_image_only_axis_aligned = True
ref.color = (1, 1, 1, 0.55); ref.use_empty_image_alpha = True
ref.hide_select = True

cam_data = bpy.data.cameras.new('CAM_front'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 2.2
cam = bpy.data.objects.new('CAM_front', cam_data); scene.collection.objects.link(cam)
cam.location = (0, -6, 0.85); cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam
for o in bpy.data.objects:
    if o.name.startswith('Socket_') or o.name in ('rods',):
        o.hide_viewport = True

# ---------------------------------------------------------------- textured preview material (export builds its own)
T = os.path.join(ROOT, 'textures')
mat = bpy.data.materials.new('Goblin_A'); mat.use_nodes = True
nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex_img = bpy.data.images.load(os.path.join(T, 'gob_a_basecolor.png'))
tex_node = nt.nodes.new('ShaderNodeTexImage'); tex_node.image = tex_img
nt.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color']); nt.nodes.active = tex_node
mesh_obj = bpy.data.objects['Peasant']; mesh_obj.data.materials.clear(); mesh_obj.data.materials.append(mat)

# ---------------------------------------------------------------- scene setup for posing
scene.render.fps = 24; scene.frame_start = 1; scene.frame_end = 19; scene.frame_set(1)
ts = scene.tool_settings
ts.use_keyframe_insert_auto = True
ts.auto_keying_mode = 'REPLACE_KEYS'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    r3 = space.region_3d
                    r3.view_perspective = 'ORTHO'
                    r3.view_rotation = Matrix.Rotation(math.radians(90), 4, 'X').to_quaternion()
                    r3.view_location = (0, 0, 0.8); r3.view_distance = 2.4
                    space.shading.type = 'SOLID'; space.shading.color_type = 'TEXTURE'; space.overlay.show_bones = True
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=out_blend, relative_remap=True)
print('POSING FILE', out_blend)
