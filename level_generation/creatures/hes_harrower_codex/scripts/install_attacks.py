"""Install the user's picked library attacks (2026-10-24) into the master: the finished candidate clips of
work/cand_final.blend (run_cands.sh) replace Harrower_Attack and Harrower_Attack2 and add Harrower_ChargeStrike;
every other action and object of the master is left as it is. Args: -- <master blend> <candidate blend> <out blend>"""
from pathlib import Path
import sys, json
import bpy
P = Path(__file__).resolve().parents[1]
master, cand, out = (str(Path(x).resolve()) for x in sys.argv[sys.argv.index('--') + 1:][:3])
PICK = {'Harrower_CandTwinCross': 'Harrower_Attack', 'Harrower_CandCrossCut': 'Harrower_Attack2',
        'Harrower_CandRunStrike': 'Harrower_ChargeStrike'}
bpy.ops.wm.open_mainfile(filepath=master)
before = sorted(a.name for a in bpy.data.actions)
with bpy.data.libraries.load(cand, link=False) as (src, dst):
    missing = [n for n in PICK if n not in src.actions]
    assert not missing, missing
    dst.actions = list(PICK)
report = {}
for a in dst.actions:
    target = PICK[a.name]; old = bpy.data.actions.get(target); fake = old.use_fake_user if old else True
    if old: bpy.data.actions.remove(old)
    report[target] = {'from': a.name, 'replaced': old is not None, 'frames': list(a.frame_range)}
    a.name = target; a.use_fake_user = fake
    assert a.name == target, a.name
after = sorted(a.name for a in bpy.data.actions)
assert set(after) == set(before) | {'Harrower_ChargeStrike'}, (before, after)
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out)
(P / 'review/install_attacks.json').write_text(json.dumps(report, indent=2) + '\n')
print('INSTALLED', json.dumps(report), flush=True)
