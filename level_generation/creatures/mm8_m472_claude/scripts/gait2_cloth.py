"""gait2 (2026-10-21), garments of the new walk and run: work/gait2_motion.blend -> work/gait2_gated.blend.
garment_sim.py (the production chain solver: damped robe/cuff/hair/tassel chains, leg capsules enclosed by the robe,
floor contact) on Walk2 and Run2 only -> the hem opening of finish_geometry.py for HEM_OPEN clips (the lowest robe
controls move up to 10 cm outward, as on Running) -> surface_clearance.py (garment-only translation correctives: robe
out of the shoes, cloth 3 mm above the floor; without it the long strides put the hem on the floor and the floor lift
below raised the whole body 4-5 cm, feet off the ground) -> finish_geometry.py's visible-surface floor lift (lowest
visible vertex >= 3 mm) -> check_deformation.py on the new clips (robe vs shoes, stretch, floor; work/deformation.json)."""
from pathlib import Path
import runpy, json
import numpy as np
p = Path(__file__).resolve().parents[1]; W = p / 'work'
CLIPS = ['Walk2', 'Run2']; HEM_OPEN = {'Run2': .10}
runpy.run_path(str(p / 'scripts/garment_sim.py'), init_globals={'INPUT_BLEND': 'gait2_motion.blend', 'OUTPUT_BLEND':
               'gait2_sim.blend', 'CLIPS': CLIPS, 'LOOPS': CLIPS}, run_name='__main__')
import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=str(W / 'gait2_sim.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene


def setact(a):
    rig.animation_data.action = a
    if a is not None and a.slots: rig.animation_data.action_slot = a.slots[0]


chains = [c for c in json.loads(sc['garment_chains']) if c['kind'] == 'robe']
robe = [n for c in chains for n in c['bones']]
assert not any(rig.data.bones[n].use_connect for n in robe)
for name in CLIPS:
    a = bpy.data.actions[name]; amount = HEM_OPEN.get(name, 0.); rows = []
    for frame in range(int(a.frame_range[1]) + 1):
        setact(a)
        for n in robe: rig.pose.bones[n].location = (0, 0, 0)
        sc.frame_set(frame); snap = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
        matrices = {n: rig.pose.bones[n].matrix.copy() for n in robe}
        setact(None)
        for b in rig.pose.bones: b.matrix_basis = snap[b.name]
        bpy.context.view_layer.update()
        for c in chains:
            direction = Vector((np.sin(c['angle']), np.cos(c['angle']), 0))
            for k, n in enumerate(c['bones']):
                M = matrices[n].copy(); M.translation += direction * (amount * (k / 3) ** 2)
                rig.pose.bones[n].matrix = M; bpy.context.view_layer.update()
        rows.append({n: rig.pose.bones[n].location.copy() for n in robe})
    setact(a)
    for frame, row in enumerate(rows):
        for n, loc in row.items(): rig.pose.bones[n].location = loc; rig.pose.bones[n].keyframe_insert('location', frame=frame)
setact(None)
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'gait2_hem.blend'))
runpy.run_path(str(p / 'scripts/surface_clearance.py'), init_globals={'INPUT_BLEND': 'gait2_hem.blend', 'OUTPUT_BLEND':
               'gait2_clear.blend', 'CLIPS': CLIPS, 'LOOPS': CLIPS}, run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(W / 'gait2_clear.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
for name in CLIPS:
    a = bpy.data.actions[name]; setact(a)
    # visible surface on the floor (finish_geometry.py): lift only colliding samples, spread over neighbours
    lows = []; mats = []
    for f in range(int(a.frame_range[1]) + 1):
        sc.frame_set(f); mats.append(rig.pose.bones['B_Pelvis'].matrix.copy())
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); lows.append(min(v.co.z for v in m.vertices)); ev.to_mesh_clear()
    lifts = np.maximum(.003 - np.array(lows), 0)
    lifts = np.maximum.reduce([np.roll(lifts, k) * (.5 ** abs(k)) for k in range(-2, 3)])
    assert lifts.max() < .08, (name, float(lifts.max()))
    for f, (M, lift) in enumerate(zip(mats, lifts)):
        sc.frame_set(f); M.translation.z += float(lift); pb = rig.pose.bones['B_Pelvis']; pb.matrix = M; pb.keyframe_insert('location', frame=f)
    for fc in [fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]:
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    print('GAIT2_CLOTH', name, 'hem opening', HEM_OPEN.get(name, 0.), 'visible floor lift cm', round(float(lifts.max()) * 100, 2), flush=True)
setact(None)
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'gait2_gated.blend'))
runpy.run_path(str(p / 'scripts/check_deformation.py'), init_globals={'INPUT_BLEND': 'gait2_gated.blend', 'CLIPS': CLIPS + ['Walking', 'Running']},
               run_name='__main__')
