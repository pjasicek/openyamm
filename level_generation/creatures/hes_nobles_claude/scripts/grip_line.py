"""The two-handed sets' handle line: in each set's carry clip (frame 0, the library trunk and arms on our rig) the left
grip socket's position in the right grip socket's frame. Its direction is the weapon's support line (the source grip
axis, playbook "Rules"), its length the hands' spacing. Writes scripts/grip_lines.json. Args: none"""
import bpy, sys, os, json
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_lib as cl
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'rig.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
out = {}
for key, glb, clip in [('2HandAxe', '2Hand Axe.glb', '2HandAxeIdle'), ('2HandShooting', '2Hand Shooting.glb', '2HandShootingIdle')]:
    src = cl.load_sources(ROOT, {glb: [clip]}, sc)
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for n in ['B_Pelvis'] + cl.TRUNK[1:] + cl.CLAV + cl.ARM['L'] + cl.ARM['R']:
        cl.set_world_rot(rig, n, cl.sample(src, clip, 0.0, n))
    R = rig.pose.bones['Grip_R'].matrix; L = rig.pose.bones['Grip_L'].matrix
    d = R.inverted() @ L.translation
    out[key] = {'clip': clip, 'left_in_right_grip': [round(x, 4) for x in d], 'spacing_m': round(d.length, 4),
                'direction': [round(x, 4) for x in d.normalized()]}
    print('LINE', key, out[key])
(P / 'scripts' / 'grip_lines.json').write_text(json.dumps(out, indent=1))
sys.stdout.flush(); os._exit(0)
