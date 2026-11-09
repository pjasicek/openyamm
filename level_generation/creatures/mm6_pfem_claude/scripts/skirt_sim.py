"""Bake skirt (Blender cloth) and braid (verlet) secondary motion into bone keys of an action.

Args: blend action mode [pre_roll]. mode: loop (simulate 3 cycles, keep the last) | once (pre-roll from the
first frame) | settle (once, plus extra hold frames appended for remains). Writes back into the same blend.
The skirt grid 'SimSkirt' (rings x 48, pinned top rings) collides with 'SimLegs' (armature-deformed) and a floor.
Chain bones Skirt_c_k are aimed along simulated meridians; the braid uses a damped verlet chain behind the back.
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, posing as P

args = sys.argv[sys.argv.index('--') + 1:]
action_name, mode = args[0], args[1]
extra = int(args[2]) if len(args) > 2 else 0
N_CHAINS, SEG = 12, 48
CHAIN_Z = [0.975, 0.73, 0.47, 0.19]
scene = bpy.context.scene
rig = bpy.data.objects['Peasant_Rig']
action = bpy.data.actions[action_name]
rig.animation_data.action = action
f0, f1 = int(action.frame_range[0]), int(action.frame_range[1])
length = f1 - f0 + 1

# Remove previous secondary keys so the body motion alone drives the simulation.
def strip_secondary(act):
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in list(bag.fcurves):
                    if '"Skirt_' in fc.data_path or '"Braid_' in fc.data_path:
                        bag.fcurves.remove(fc)
    if hasattr(act, 'fcurves'):
        for fc in list(act.fcurves):
            if '"Skirt_' in fc.data_path or '"Braid_' in fc.data_path:
                act.fcurves.remove(fc)
strip_secondary(action)


def all_fcurves(act):
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    if not out and hasattr(act, 'fcurves'):
        out = list(act.fcurves)
    return out


# Timeline: [pre-roll hold of first pose][cycles or clip][settle hold]
cycles = 3 if mode == 'loop' else 1
pre = 0 if mode == 'loop' else 24
sim_start = 1
sim_end = pre + length * cycles + (extra if mode == 'settle' else 0)


def clip_frame(sim_frame):
    """Map a simulation frame to the action frame (float)."""
    t = sim_frame - sim_start - pre
    if t < 0:
        return f0
    if mode == 'loop':
        return f0 + (t % length)
    return min(f0 + t, f1)


sim = bpy.data.objects['SimSkirt']
legs = bpy.data.objects['SimLegs']
sim.hide_viewport = False; legs.hide_viewport = False
for m in list(sim.modifiers):
    sim.modifiers.remove(m)
# Rigid follow of the hips for pinned rings: weights only to the hips.
for g in list(sim.vertex_groups):
    sim.vertex_groups.remove(g)
co = np.array([tuple(v.co) for v in sim.data.vertices])
hips_g = sim.vertex_groups.new(name='mixamorig:Hips'); hips_g.add(list(range(len(co))), 1.0, 'REPLACE')
pin = sim.vertex_groups.new(name='pin')
for i in range(len(co)):
    z = co[i, 2]
    if z > 0.945:
        pin.add([i], 1.0, 'REPLACE')
    elif z > 0.90:
        pin.add([i], (z - 0.90) / 0.045 * 0.6, 'REPLACE')
sim.parent = rig; sim.matrix_parent_inverse = rig.matrix_world.inverted()
am = sim.modifiers.new('Armature', 'ARMATURE'); am.object = rig
cloth = sim.modifiers.new('Cloth', 'CLOTH')
cs = cloth.settings
cs.quality = 10
cs.mass = 0.25
cs.air_damping = 2.0
cs.tension_stiffness = 20; cs.compression_stiffness = 20; cs.shear_stiffness = 8
cs.bending_stiffness = 0.6
cs.tension_damping = 6; cs.compression_damping = 6; cs.bending_damping = 1.0
cs.vertex_group_mass = 'pin'
cs.pin_stiffness = 1.0
cc = cloth.collision_settings
cc.use_collision = True
cc.distance_min = 0.006
cc.collision_quality = 4
cc.use_self_collision = mode == 'settle'
cc.self_distance_min = 0.006
cloth.point_cache.frame_start = sim_start
cloth.point_cache.frame_end = sim_end
if not any(m.type == 'COLLISION' for m in legs.modifiers):
    legs.modifiers.new('Collision', 'COLLISION')
legs.collision.thickness_outer = 0.005
legs.collision.cloth_friction = 3.0
floor = bpy.data.objects.get('SimFloor')
if floor is None:
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, -0.012))
    floor = bpy.context.active_object; floor.name = 'SimFloor'; floor.hide_render = True
    floor.modifiers.new('Collision', 'COLLISION')
    floor.collision.thickness_outer = 0.004
    floor.collision.cloth_friction = 8.0

# Drive the rig on the simulation timeline with a temporary action evaluation per frame.
scene.render.fps = 24
scene.frame_start, scene.frame_end = sim_start, sim_end
# Temporary timeline action: shifted by the pre-roll, cycled for loops. The depsgraph evaluates it per frame,
# so the cloth cache sees consistent, frame-driven armature input.
timeline = action.copy(); timeline.name = action_name + '_simtimeline'
for fc in all_fcurves(timeline):
    if '"Skirt_' in fc.data_path or '"Braid_' in fc.data_path:
        continue
    for kp in fc.keyframe_points:
        kp.co.x += sim_start + pre - f0
        kp.handle_left.x += sim_start + pre - f0
        kp.handle_right.x += sim_start + pre - f0
    if mode == 'loop':
        fc.modifiers.new('CYCLES')
rig.animation_data.action = timeline


def apply_clip_pose(frame):
    """Evaluate the body action at a (possibly fractional) clip frame into the pose."""
    for fc in all_fcurves(action):
        try:
            bone_name = fc.data_path.split('"')[1]
        except IndexError:
            continue
        bone = rig.pose.bones.get(bone_name)
        if bone is None:
            continue
        prop = fc.data_path.rsplit('.', 1)[1]
        getattr(bone, prop)[fc.array_index] = fc.evaluate(frame)


# Rest offset from the simulated surface point to each chain joint (joints sit slightly inside the cloth).
REST_OFFSET = {}
TRACK = {}
world_co = np.array([tuple(sim.matrix_world @ Vector(c)) for c in co])
for c in range(N_CHAINS):
    for k in range(4):
        joint = rig.data.bones[f'Skirt_{c}_{min(k, 2) + 1}']
        joint_pos = rig.matrix_world @ (joint.head_local if k < 3 else joint.tail_local)
        nearest = int(np.argmin(np.linalg.norm(world_co - np.array(joint_pos), axis=1)))
        TRACK[(c, k)] = nearest
        REST_OFFSET[(c, k)] = joint_pos - Vector(world_co[nearest])

CORPSE = tuple(int(x) for x in os.environ['CORPSE_BLEND'].split(',')) if os.environ.get('CORPSE_BLEND') else None
HIPS_REST_INV = (rig.matrix_world @ rig.data.bones['mixamorig:Hips'].matrix_local).inverted()
CHAIN_REST, CHAIN_LEN = {}, {}
for c in range(N_CHAINS):
    for k in range(3):
        bone = rig.data.bones[f'Skirt_{c}_{k + 1}']
        CHAIN_REST[(c, k)] = rig.matrix_world @ bone.head_local
        CHAIN_LEN[(c, k)] = bone.length
        if k == 2:
            CHAIN_REST[(c, 3)] = rig.matrix_world @ bone.tail_local

# Braid rest distances from the spine->neck axis (collision radius per braid joint).
_sp = rig.matrix_world @ rig.data.bones['mixamorig:Spine2'].head_local
_nk = rig.matrix_world @ rig.data.bones['mixamorig:Neck'].head_local
_ax = (_nk - _sp).normalized()
_pts = [rig.matrix_world @ rig.data.bones['Braid_1'].head_local] + \
    [rig.matrix_world @ rig.data.bones[f'Braid_{k}'].tail_local for k in (1, 2, 3)]
BRAID_REST_RADIUS = [((p - _sp) - _ax * (p - _sp).dot(_ax)).length for p in _pts]

# Braid verlet chain state.
braid_bones = ['Braid_1', 'Braid_2', 'Braid_3']
braid_len = [rig.data.bones[b].length for b in braid_bones]
braid_pts = None
braid_prev = None
chain_targets = []   # per sim frame: list of (chain, k) -> world direction
braid_targets = []
for frame in range(sim_start, sim_end + 1):
    scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = sim.evaluated_get(dg)
    me = ev.to_mesh()
    pts = np.array([tuple(sim.matrix_world @ v.co) for v in me.vertices])
    ev.to_mesh_clear()
    dirs = {}
    hips_rot = (rig.matrix_world @ rig.pose.bones['mixamorig:Hips'].matrix).to_quaternion() @ \
        (rig.matrix_world @ rig.data.bones['mixamorig:Hips'].matrix_local).to_quaternion().inverted()
    for c in range(N_CHAINS):
        heads = []
        for k in range(4):
            surface = Vector(pts[TRACK[(c, k)]])
            heads.append(surface + hips_rot @ REST_OFFSET[(c, k)])
        for k in range(3):
            dirs[(c, k)] = (heads[k], (heads[k + 1] - heads[k]).normalized())
    chain_targets.append(dirs)
    if os.environ.get('SIM_DEBUG') and frame % 6 == 0:
        mesh_obj = bpy.data.objects['Peasant']; mesh_obj.hide_render = True
        sim.hide_render = False; legs.hide_render = False
        common.workbench_clay(scene)
        common.render_views(os.path.join(common.REVIEW, 'tmp', f'simdbg_{frame:03d}'), 0.6, 1.3, views=('left',), resolution=(260, 260))
        sim.hide_render = True; legs.hide_render = True; mesh_obj.hide_render = False
    # Braid: root follows Braid_1 head (child of Head); gravity, damping, collision with the upper back.
    root = rig.matrix_world @ rig.pose.bones['Braid_1'].head
    spine = rig.matrix_world @ rig.pose.bones['mixamorig:Spine2'].head
    neck = rig.matrix_world @ rig.pose.bones['mixamorig:Neck'].head
    back_axis = (neck - spine).normalized()
    if braid_pts is None:
        braid_pts = [root.copy()]
        for b, l in zip(braid_bones, braid_len):
            braid_pts.append(rig.matrix_world @ rig.pose.bones[b].tail)
        braid_prev = [p.copy() for p in braid_pts]
    dt = 1.0 / 24
    new = [root.copy()]
    for i in range(1, 4):
        p, q = braid_pts[i], braid_prev[i]
        new.append(p + (p - q) * 0.86 + Vector((0, 0, -9.8)) * dt * dt)
    for _ in range(6):
        new[0] = root.copy()
        for i in range(3):
            a, b = new[i], new[i + 1]
            d = b - a
            corr = d.normalized() * (d.length - braid_len[i])
            if i == 0:
                new[i + 1] = b - corr
            else:
                new[i] = a + corr * 0.5; new[i + 1] = b - corr * 0.5
        for i in range(1, 4):  # never closer to the spine->neck axis than in the rest pose (minus 3 mm)
            rel = new[i] - spine
            along = rel.dot(back_axis)
            radial = rel - back_axis * along
            if radial.length < BRAID_REST_RADIUS[i] - 0.003:
                new[i] = spine + back_axis * along + radial.normalized() * (BRAID_REST_RADIUS[i] - 0.003)
    braid_prev, braid_pts = braid_pts, new
    braid_targets.append([(new[i + 1] - new[i]).normalized() for i in range(3)])

# Choose output frames and key them into the action.
if mode == 'loop':
    out = list(range(sim_end - length + 1, sim_end + 1))
    out_frames = [f0 + i for i in range(length)]
else:
    out = list(range(sim_start + pre, sim_end + 1))
    out_frames = [f0 + i for i in range(len(out))]
rig.animation_data.action = action
bpy.data.actions.remove(timeline)
if mode == 'settle' and extra:
    # Extend the action's held final pose so the settle frames exist for every body bone.
    pass
for sim_frame, act_frame in zip(out, out_frames):
    P.reset(rig)
    apply_clip_pose(min(clip_frame(sim_frame), f1))
    bpy.context.view_layer.update()
    dirs = chain_targets[sim_frame - sim_start]
    if CORPSE:
        # Deterministic corpse drape: skirt rigid with the hips, flattened over the lying legs, blended in
        # from the sim so the free cloth never has to resolve the 88-degree fall in 125 ms.
        b0, b1 = CORPSE
        wgt = min(max((act_frame - b0) / (b1 - b0), 0.0), 1.0); wgt = wgt * wgt * (3 - 2 * wgt)
        if wgt > 0:
            T = (rig.matrix_world @ rig.pose.bones['mixamorig:Hips'].matrix) @ HIPS_REST_INV
            blended = {}
            for c in range(N_CHAINS):
                pts = []
                for k in range(4):
                    q = T @ CHAIN_REST[(c, k)]
                    if k > 0:
                        # spread sideways from the leg axis (native corpse fans the skirt on the floor)
                        hips_w = T.to_translation(); axis = (T.to_3x3() @ Vector((0, 0, -1))); axis.z = 0
                        if axis.length > 1e-4:
                            axis.normalize(); rel = q - hips_w; rel.z = 0
                            perp = rel - axis * rel.dot(axis)
                            q += perp * (0.25 * k)
                        q.z = min(max(q.z, 0.012 + 0.006 * k), 0.245 - 0.01 * k)
                    pts.append(q)
                heads = [dirs[(c, k)][0] for k in range(3)] + [dirs[(c, 2)][0] + dirs[(c, 2)][1] * CHAIN_LEN[(c, 2)]]
                mixed = [heads[k].lerp(pts[k], wgt) for k in range(4)]
                for k in range(3):
                    blended[(c, k)] = (mixed[k], (mixed[k + 1] - mixed[k]).normalized())
            dirs = blended
    for c in range(N_CHAINS):
        for k in range(3):
            name = f'Skirt_{c}_{k + 1}'
            bone = rig.pose.bones[name]
            target_head, direction = dirs[(c, k)]
            inv = rig.matrix_world.inverted()
            current = (bone.tail - bone.head).normalized()
            q = current.rotation_difference(rig.matrix_world.to_quaternion().inverted() @ direction)
            rot = q @ bone.matrix.to_quaternion()
            bone.matrix = Matrix.LocRotScale(inv @ target_head if k > 0 else bone.head.copy(), rot, Vector((1, 1, 1)))
            bpy.context.view_layer.update()
    for i, name in enumerate(braid_bones):
        bone = rig.pose.bones[name]
        current = (bone.tail - bone.head).normalized()
        desired = rig.matrix_world.to_quaternion().inverted() @ braid_targets[sim_frame - sim_start][i]
        q = current.rotation_difference(desired)
        head = bone.head.copy()
        bone.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ bone.matrix
        bpy.context.view_layer.update()
    for bone in rig.pose.bones:
        if bone.name.startswith(('Skirt_', 'Braid_')):
            bone.keyframe_insert('rotation_quaternion', frame=act_frame)
            if bone.name.startswith('Skirt_'):
                bone.keyframe_insert('location', frame=act_frame)
        elif act_frame > f1:  # settle tail: hold the final body pose
            bone.keyframe_insert('rotation_quaternion', frame=act_frame)
            if bone.name == 'mixamorig:Hips':
                bone.keyframe_insert('location', frame=act_frame)
for m in list(sim.modifiers):
    sim.modifiers.remove(m)
print('SIMULATED', action_name, mode, 'frames', len(out))
bpy.ops.wm.save_mainfile()
