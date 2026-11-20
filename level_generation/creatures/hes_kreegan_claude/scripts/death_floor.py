"""Death on the floor (playbook "Feet and locomotion": the corpse must not sink or float). Per frame of the listed
clips: the lowest point of the evaluated body (the skirt, which robe_sim.py keeps above the floor itself, left out)
and of the rifle; the pelvis is raised by the depth below FLOOR, and once the body lies (pelvis below LIE x its
total drop) also lowered onto the floor, so Dead rests on it; offsets smoothed over time (Gaussian SIG frames,
the raise kept at least the depth). Keys B_Pelvis location. Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
FLOOR, LIE, SIG = 0.0, float(os.environ.get('LIE', '0.5')), 2.0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; gun = bpy.data.objects.get('Rifle'); sc = bpy.context.scene
gv = np.array([x.value for x in body.data.attributes['garment'].data]); keep = gv != 2
# hkr: the tail (Bone_015..Bone_020) and the carbine do not hold the corpse up: the stiff source tail and the held
# gun pierced the floor and raised the falling body 45 cm; tail_anim.py drapes the tail on the floor afterwards and
# death_carbine_floor.py lays the gun down in the export
_TB = {body.vertex_groups[n].index for n in ('Bone_015', 'Bone_016', 'Bone_017', 'Bone_018', 'Bone_019', 'Bone_020') if n in body.vertex_groups}
keep &= np.array([sum(e.weight for e in v.groups if e.group in _TB) < 0.5 for v in body.data.vertices])
gun = None


def lowest():
    dg = bpy.context.evaluated_depsgraph_get(); z = []
    for ob, m in [(body, keep), (gun, None)] + [(o, None) for o in bpy.data.objects if o.name.startswith('Arm_')]:  # gun None: skipped
        if ob is None:
            continue
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        co = co @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
        z.append(float((co[m] if m is not None else co)[:, 2].min())); ev.to_mesh_clear()
    return min(z)


for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); fr = list(range(f0, f1 + 1))
    pb = rig.pose.bones['B_Pelvis']; sc.frame_set(f0); h0 = (rig.matrix_world @ pb.matrix).translation.z
    hz, zm = [], []
    for f in fr:
        sc.frame_set(f); zm.append(lowest()); hz.append((rig.matrix_world @ pb.matrix).translation.z)
    down = h0 - LIE * (h0 - min(hz))                   # past LIE of the pelvis's total drop: the body is down
    lying = False; need = []
    for z_, h_ in zip(zm, hz):
        lying = lying or h_ < down
        need.append(FLOOR - z_ if (z_ < FLOOR or lying) else 0.0)
    print('DEATHFLOOR need cm', [round(x * 100, 1) for x in need])
    need = np.array(need); k = np.exp(-0.5 * (np.arange(-6, 7) / SIG) ** 2); k /= k.sum()
    sm = np.convolve(np.pad(need, 6, mode='edge'), k, mode='valid')
    off = np.maximum(sm, need)                          # never below the floor (lying frames need <= 0)
    # the pelvis location is in its parent space: move along world Z through the bone's rest-space mapping
    for f, d in zip(fr, off):
        sc.frame_set(f)
        M = rig.matrix_world @ pb.matrix; M.translation.z += float(d)
        pb.matrix = rig.matrix_world.inverted() @ M
        pb.keyframe_insert('location', frame=f)
    sc.frame_set(f1); end = lowest()
    worst = 9.0
    for f in fr:
        sc.frame_set(f); worst = min(worst, lowest())
    print('DEATHFLOOR', name, 'raise cm max', round(float(off.max()) * 100, 1), 'lowered cm', round(float(-off.min()) * 100, 1),
          'lowest after cm', round(worst * 100, 2), 'last frame cm', round(end * 100, 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
