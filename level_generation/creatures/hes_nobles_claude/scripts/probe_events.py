"""Measure the event times of every set on the full assembly (work/assembly_all.blend), at 48 Hz:
- `speed` (`speed>t`: from t s on): the fastest motion of a point while it is in front of the chest (y below the chest's - 0.15 m): a blow's
  contact (the playbook: fastest tip motion while pointing at the target);
- `forward`: the point furthest forward of the chest: a thrown bolt, a flick, a sweep's wave;
- `height`: the point at its highest: a raised spell;
- `fixed:<s>`: a library time (the rifles' shot, FireRifle1 at 0.367 s after the clip's lead).
Points: a bone name (release sockets, Palm_L) or `tip:<weapon object>` (the weapon vertex farthest from its socket).
Writes work/events.json. Args: none"""
import bpy, sys, os, json
from mathutils import Vector
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work', 'assembly_all.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
PLAN = {
    'Noble': {'attack_melee': ('Noble_AttackMelee', 'speed', 'tip:W_noble_fang'),
              'attack_ranged': ('Noble_AttackRanged', 'forward', 'Palm_L'), 'cast': ('Noble_Cast', 'height', 'Palm_L')},
    'Ssekh': {'attack_melee': ('Ssekh_AttackMelee', 'fixed:0.78125', 'tip:W_ssekh_fang_r'),
              'attack_ranged': ('Ssekh_AttackRanged', 'forward', 'Tip_Ssekh_R'), 'cast': ('Ssekh_Cast', 'height', 'Palm_L')},
    'Mraal': {'attack_melee': ('Mraal_AttackMelee', 'speed', 'Blade_Mraal'),
              'attack_ranged': ('Mraal_AttackRanged', 'speed', 'Blade_Mraal'), 'cast': ('Mraal_Cast', 'height', 'Blade_Mraal')},
    'Xith': {'attack_melee': ('Xith_AttackMelee', 'speed>0.4', 'Muzzle_Xith'),
             'attack_ranged': ('Xith_AttackRanged', 'fixed:0.617', 'Muzzle_Xith'), 'cast': ('Xith_Cast', 'fixed:0.632', 'Muzzle_Xith')},
    'Gate': {'attack_melee': ('Gate_AttackMelee', 'speed>0.4', 'Muzzle_Gate'),
             'attack_ranged': ('Gate_AttackRanged', 'fixed:0.617', 'Muzzle_Gate'), 'cast': ('Gate_Cast', 'fixed:0.632', 'Muzzle_Gate')},
}


def point_fn(spec):
    if spec.startswith('tip:'):
        W = bpy.data.objects[spec[4:]]; sock = rig.data.bones[W['socket']].matrix_local.translation
        i = max(range(len(W.data.vertices)), key=lambda k: (W.data.vertices[k].co - sock).length)
        def f(dg):
            e = W.evaluated_get(dg); m = e.to_mesh(); p = (W.matrix_world @ m.vertices[i].co).copy(); e.to_mesh_clear(); return p
        return f
    return lambda dg: (rig.matrix_world @ rig.pose.bones[spec].head).copy()


res = {}
for setn, plan in PLAN.items():
    res[setn] = {}
    for role, (clip, kind, pt) in plan.items():
        act = bpy.data.actions[clip]; rig.animation_data.action = act
        if act.slots: rig.animation_data.action_slot = act.slots[0]
        f = point_fn(pt); T = []
        for fr in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
            sc.frame_set(fr); dg = bpy.context.evaluated_depsgraph_get()
            T.append((f(dg), (rig.matrix_world @ rig.pose.bones['B_Spine2'].head).copy()))
        if kind.startswith('fixed:'):
            i = round(float(kind[6:]) * 48)
        elif kind.startswith('speed'):
            t0 = float(kind[6:]) if '>' in kind else 0.0
            cand = [((T[i + 1][0] - T[i - 1][0]).length * 24, i) for i in range(1, len(T) - 1)
                    if T[i][0].y < T[i][1].y - 0.15 and i / 48 >= t0]
            i = max(cand)[1] if cand else max(((T[i + 1][0] - T[i - 1][0]).length, i) for i in range(1, len(T) - 1))[1]
        elif kind == 'forward':
            i = min(range(len(T)), key=lambda k: T[k][0].y - T[k][1].y)
        else:
            i = max(range(len(T)), key=lambda k: T[k][0].z)
        res[setn][role] = {'impact': round(i / 48, 4), 'clip': clip, 'rule': kind, 'point': pt}
    print('EVENTS', setn, {k: v['impact'] for k, v in res[setn].items()}, flush=True)
json.dump(res, open(os.path.join(P, 'work', 'events.json'), 'w'), indent=1)
sys.stdout.flush(); os._exit(0)
