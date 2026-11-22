"""G1 numeric probe of Mixamo clips: duration, per hand the max forward reach (m, relative to the hips, along the
character's rest forward = heel->toe), its time and the hand height then; hips travel and lowest hips height.
Args: -- <fbx> [...]"""
import bpy, sys, os, math
from mathutils import Vector
for fbx in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    sc = bpy.context.scene
    src = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    pre = next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
    act = src.animation_data.action
    f0, f1 = act.frame_range
    fps = sc.render.fps / sc.render.fps_base
    W = src.matrix_world
    P = lambda n: W @ src.pose.bones[pre + n].head
    sc.frame_set(int(f0))
    fwd = Vector((0, -1, 0))
    right = Vector((1, 0, 0))  # character left = +X
    h0 = P('Hips')
    leg = (P('LeftUpLeg') - P('LeftFoot')).length
    best = {s: (-9, 0, 0, 0) for s in ('Left', 'Right')}
    hmin = 9; travel = 0
    for f in range(int(f0), int(f1) + 1):
        sc.frame_set(f)
        hp = P('Hips'); hmin = min(hmin, (hp.z) / leg); travel = max(travel, (hp - h0).length)
        for s in ('Left', 'Right'):
            d = P(s + 'Hand') - hp
            fr = d.dot(fwd)
            if fr > best[s][0]:
                best[s] = (fr, (f - f0) / fps, d.z, d.dot(right))
    out = ' '.join(f"{s[0]}:fwd{best[s][0] / leg:.2f}@{best[s][1]:.2f}s z{best[s][2] / leg:+.2f} side{best[s][3] / leg:+.2f}" for s in best)
    print(f'PROBE {os.path.basename(fbx)[:34]:34s} {(f1 - f0) / fps:5.2f}s hips_min {hmin:.2f} travel {travel / leg:.2f} | {out}')
