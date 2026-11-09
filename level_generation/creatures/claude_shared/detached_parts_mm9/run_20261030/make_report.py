"""Writes ../../detached_parts_mm9.md from final2/*.json (the hand-written verdicts are below)."""
import glob
import json
from pathlib import Path
import sys

here = Path(__file__).resolve().parent
shared = here.parent.parent
sys.path.insert(0, str(shared))
sys.dont_write_bytecode = True
import detached_parts_audit as audit  # noqa: E402

results = [json.loads(Path(f).read_text())[0] for f in sorted(glob.glob(str(here / 'final2' / 'mm9_*.json')))]
by = {Path(r['glb']).stem: r for r in results}
r3 = json.loads((here / 'final2' / 'before_eyesfins_r3.json').read_text())[0]
out = shared / 'detached_parts_mm9.md'
body = shared / 'detached_parts_mm9' / 'run_20261030' / 'per_creature.md'
audit.write_md(results, body)
crop = 'detached_parts_mm9/run_20261030/final2/crops'


def worst(name, part):
    p = by[name]['parts'][str(part)]
    w = p['worst']
    return f"{w['gap'] * 1000:.1f} mm, {w['clip']} frame {w['frame']} ({w['time']:.2f} s), {p['detached_poses']}/{p['poses']} poses"


def fins():
    rows = []
    for k, p in sorted(r3['parts'].items(), key=lambda kv: -kv[1]['worst']['gap']):
        w = p['worst']
        rows.append(f"| {k} | {p['joint']} | {p['bind_gap'] * 1000:.1f} mm | {w['gap'] * 1000:.1f} mm ({w['kind']}), "
                    f"{w['clip']} {w['frame']} | {p['detached_poses']}/{p['poses']} ({p['carried_poses']} carried) |")
    return '\n'.join(rows)


clean = [n for n, r in by.items() if not r['parts']]
flagged = [n for n, r in by.items() if r['parts']]
text = f"""# Detached parts: MM9 creatures (2026-10-30, root rules)

Audit of every installed `assets_source/worlds/mm9/models/mm9_*.glb` ({len(by)} models) with
[`detached_parts_audit.py`](detached_parts_audit.py), bind pose and every clip at 30 fps. Read-only: no creature was
changed. This replaces the chain-rule report of the same day. Models changed during the run (animal agents and rework
agents), so each result is for the file hashed in `detached_parts_mm9/run_20261030/final2/md5_*.txt` (later lists
win); anything installed later is not covered. Crops: the part red, the rest grey, the gap yellow; they are untextured
and nothing here was checked in the review viewer.

```sh
python3 level_generation/creatures/claude_shared/detached_parts_audit.py assets_source/worlds/mm9/models/mm9_*.glb \\
  --crops <dir> --json out.json --md out.md
python3 level_generation/creatures/claude_shared/test_detached_parts_audit.py
python3 level_generation/creatures/claude_shared/detached_parts_mutation.py assets_source/worlds/mm9/models/mm9_*.glb
```

## Rules

The tool's docstring has the detail. `--rules chain` still runs the old rule; the command line and the JSON keys are
unchanged (new keys only), and the exit status still means a visible detached part.

- Distances are directed and signed with angle-weighted pseudo-normals. The old smoothed-normal sign put points far
  behind a thin plate's corner "inside" it, which is one reason fins passed.
- The body and larger parts hold a part. **This is weaker than requested.** "Strictly larger only" failed correct
  approved models, which hang large parts on small connectors: Dagrell's skull and feet on thin bones, the Eye's
  stalk segments, Magreeb's Bone24 on Bone21. So smaller connectors and same-size neighbours can still hold a part,
  and only a plate is barred from resting on a neighbour when a larger part lies alongside it.
- **The gap along the root is measured only for plates at bind** (base edge in 10 slices, largest gap, after
  `fin_gates.py`). Other parts at bind still pass on one touching vertex: there is no general way to tell where a
  limb's root should be, and every general attempt failed approved limbs and wings.
- In clips every part's bind contact vertices are measured against the holder they had at bind: median over 8 mm
  fails (`parted`); 90th percentile over 8 mm alone is listed as a root lift and does not fail, because a limb pivoting
  in its socket looks the same.
- Loose clusters report one break.

## Calibration

Sea Monster r3 (`mm9_seamon_claude/work/before_eyesfins_r3.glb`, the regression case in
[`test_detached_parts_audit.py`](test_detached_parts_audit.py)): all six floating fins fail; the chain rule passed all
of them; the front fin, which touches, passes, and the installed fixed model is clean.

| Part | Joint | Bind gap | Worst | Poses |
|---|---|---|---|---|
{fins()}

Part 24 touches the back at one end; its gap is a slice minimum, so it reads less than `fin_gates.py`'s 5.9 cm.

Clean on all poses: {', '.join(clean)}. Flagged: {', '.join(flagged)}.

**The thresholds were tuned on these same approved creatures**, so their passing is not independent evidence. Only
`mm9_fish`, `mm9_goose`, `mm9_hen`, `mm9_mouse`, `mm9_pig`, `mm9_ram`, `mm9_rooster` and `mm9_sheep` were not used for
tuning.

### What it still misses

`detached_parts_mutation.py` damaged good models in memory and counted the catches (`run_20261030/mutation_final.txt`;
631 valid mutants on the 25 models installed then, which predates the later reinstalls).

| Damage | Caught as a failure | Held by another part | Passed on the same holder |
|---|---|---|---|
| Part pulled clear of its holder | 322/419 | 96 | 1 |
| Root tilted, one end touching, present at bind | 1/212 | 3 | 208 |
| Same tilt in a clip | 10/212 | 25 | 177 |

So the tool does **not** yet guarantee catching every floating part. A part pulled clear that still touches any other
part passes (23 %). A tilted root in a clip is at least listed as a root lift (by construction, not measured), among
many harmless ones. A tilted root at bind is effectively invisible unless the part is a plate that stands upright, and
even then the sample was 1 of 8.

## Findings

| Creature | Part | Worst gap | Verdict |
|---|---|---|---|
| Lobber (approved) | 2, upper arm `XCarm01` | {worst('mm9_lobber', 2)} | **Real, new**: the arm's end stops visibly short of the head. [crop]({crop}/mm9_lobber_part2.png) |
| Dagrell (approved) | 40, neck `XneckB` | {worst('mm9_dagrell', 40)} | **Probably real, new**; the head above it is then counted as carried. [crop]({crop}/mm9_dagrell_part40.png) |
| Dagrell (approved) | 71, tail `XtailB` | {worst('mm9_dagrell', 71)} | **Probably real, new**, held in the Dead pose. [crop]({crop}/mm9_dagrell_part71.png) |
| Lobber (approved) | 14, head piece `Xheadpiv` | {worst('mm9_lobber', 14)} | Small, inside the mouth. [crop]({crop}/mm9_lobber_part14.png) |
| Greater Demon (approved) | 120, 116, 101, 72: 12-20 tri pieces | up to {by['mm9_greaterdemon']['parts']['120']['worst']['gap'] * 1000:.1f} mm | Small, new. [crop]({crop}/mm9_greaterdemon_part120.png) |
| Rooster | 45, 12, 81: 1-2 tri slivers | up to {by['mm9_rooster']['parts']['45']['worst']['gap'] * 1000:.1f} mm | Real, tiny: stray triangles. [crop]({crop}/mm9_rooster_part45.png) |

Marked artefacts, not gaps; do not act on them:

- Greater Demon wings 126 and 1 (up to {by['mm9_greaterdemon']['parts']['126']['worst']['gap'] * 1000:.0f} mm, {by['mm9_greaterdemon']['parts']['126']['detached_poses']} and {by['mm9_greaterdemon']['parts']['1']['detached_poses']} poses): the plate rule misfiring on a wing spreading past its root; no gap in the crop.
- Dagrell 66 and 84 (up to {by['mm9_dagrell']['parts']['66']['worst']['gap'] * 1000:.0f} mm): knock-on of the neck break above; a skull chip measured against the nearest attached part. The skull is intact.
- Rooster comb 42: comes from the same plate rule and looks seated in the crop. Check in the viewer before acting.

The remaining flags are 1-7 frames at about 1 cm or less on Dragon King, Jelly, Nagate, Lobber and Greater Demon
(tables below). Root lifts are unreviewed: most are pivoting joints, and values over 1 m come from bind contacts
along a limb, so they are leads at best.

No longer flagged compared with the first report: Annud's left hand and Yrsa's hands (8-13 mm in their sleeves on
the previous install, which the chain rule's sign error had passed), Magreeb, Terror, Wolf and the Sea Monster.

## Per creature

"""
pc = body.read_text().replace('](run_20261030/', '](detached_parts_mm9/run_20261030/').replace('](final2/', '](detached_parts_mm9/run_20261030/final2/')
out_tmp = out.with_suffix('.md.tmp')
out_tmp.write_text(text + pc)
out_tmp.replace(out)
print(len(text.splitlines()), 'head lines', len(pc.splitlines()), 'body lines')
