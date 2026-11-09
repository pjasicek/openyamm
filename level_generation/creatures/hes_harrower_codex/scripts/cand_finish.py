"""Finishing passes for the candidate attacks, as finish_motion.py / cloth_fit.py / final_fit.py do for the bound
clips: claw-foot floor, tail, skirt strips and mantle simulated, cloth fitted to the body, then a small root lift
where any vertex dips under the floor. Args: -- <in blend> <out blend>"""
from pathlib import Path
import sys, runpy, os
import bpy, numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts'))
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
clips = [a.name for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]
W = P / 'work'


def run(script, a, b, args):
    sys.argv = [script, '--', str(a), str(b), *args]
    runpy.run_path(str(P / 'scripts' / script), run_name='__main__')


run('foot_floor.py', Path(src).resolve(), W / 'cand_f1.blend', clips)
run('tail_anim.py', W / 'cand_f1.blend', W / 'cand_f2.blend', clips)
run('cand_robe_sim.py', W / 'cand_f2.blend', W / 'cand_f3.blend', ['cloth', *clips])
run('cand_robe_sim.py', W / 'cand_f3.blend', W / 'cand_f4.blend', ['mantle', *clips])
run('cand_cloth_fit.py', W / 'cand_f4.blend', W / 'cand_f5.blend', [])
import armik
bpy.ops.wm.open_mainfile(filepath=str(W / 'cand_f5.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
for name in clips:
    act = bpy.data.actions[name]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    frames = range(int(act.frame_range[1]) + 1); samples = []
    for f in np.arange(0, act.frame_range[1] + .001, .5):
        sc.frame_set(int(f), subframe=float(f - int(f))); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh(); co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
        z = (co.reshape(-1, 3) @ np.array(body.matrix_world.to_3x3()).T)[:, 2] + body.matrix_world.translation.z
        samples.append(max(0., .0005 - float(z.min())))
    lifts = {f: max(samples[max(0, 2 * f - 1):min(len(samples), 2 * f + 2)]) for f in frames}; pose = {}
    for f in frames:
        sc.frame_set(f); M = armik.W(rig, 'B_Pelvis'); M.translation.z += lifts[f] if lifts[f] > .002 else 0
        armik.set_world(rig, 'B_Pelvis', M); pose[f] = rig.pose.bones['B_Pelvis'].location.copy()
    for f, p in pose.items():
        rig.pose.bones['B_Pelvis'].location = p; rig.pose.bones['B_Pelvis'].keyframe_insert('location', frame=f)
    print('ROOT_LIFT', name, round(max(lifts.values()), 4), flush=True)
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
