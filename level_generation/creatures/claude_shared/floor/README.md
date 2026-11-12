# Creature floor contact: audit and clip fixes

Step 2 of the [creature post-process](../../CREATURE_POSTPROCESS.md).

The engine never snaps a 3D actor to the floor: model-space y = 0 is the actor's floor (`preciseZ`), indoors and
outdoors, for walkers and fliers alike, and `z_offset` moves the living actor and its corpse together
(`game/fx/WorldFxSystem.cpp`). Floor contact is therefore a property of each GLB's clips, checked and fixed here
without Blender (`glb_pose.py` evaluates the hierarchy, LINEAR/STEP samplers and skinning; it matches Blender's
evaluated meshes exactly on the MM8 set).

## Rules (user decision, 2026-10-21)

- **Ground actors:** the standing pose on the floor; walking never below it and never with every foot off it (a run
  may have a suspension phase); every living clip above it; the corpse resting on it.
- **Fliers and hoverers** (`canFly` in `monster_data.txt`, plus `HOVERERS` in `floor_audit.py`: Efreeti, Dragon
  Turtle): the lowest point over all living clips (standing, walking, running, attacks, cast, hit, fidget) meets the
  floor. A flier at floor height then neither cuts the ground with its wing strokes nor floats far above it. The lift
  lives in the clips (`floor_fix.py --hover`), and the death clip eases it out, so the corpse rests on the floor.
  There is no runtime hover key: a runtime offset that eases out cannot know when the authored fall reaches the floor,
  and a negative one sank Raven Man 12 units mid-death.
- **Exceptions:** bindings with `z_offset` (Will o' Wisp, a light with no body; the School of Fish) are listed, not
  judged. `ACCEPTED` notes the Efreeti's flame-vortex tail tip, which whips up to 14 cm under the floor for 0.3 s as
  the body contracts into the flask.
- **Tolerance:** the larger of 2.5 world units and 1 % of the standing height (a 9 m dragon's 3 units are 2 mm in its
  model).

## Tools

```sh
# Every binding of a world: standing/walking/living/corpse heights in world units, problems, suggested hover.
python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world mm8 [--match 'Phoenix*'] [--json out.json]

# Fix a project's export (back it up to work/floor_fix_base/ first), then install it as usual.
F=level_generation/creatures/claude_shared/floor/floor_fix.py
python3 $F work/floor_fix_base/x.glb export/x.glb --ground-loop Walking            # walk/idle: foot on the floor
python3 $F work/floor_fix_base/x.glb export/x.glb --raise Attack                   # attack/hit/cast/run: no sinking
python3 $F work/floor_fix_base/x.glb export/x.glb --ground-death Death Dead        # corpse onto the floor
python3 $F work/floor_fix_base/x.glb export/x.glb --lift-joints Death Dead --lift-only 'Cloak*' --ground-death Death Dead
python3 $F work/floor_fix_base/x.glb export/x.glb --hover 0.266206 Death Dead      # flier rule
python3 tools/install_model.py export/x.glb --world mm8
```

- `--ground-loop` puts the lowest point on the floor at every key (both directions): use it for walks and idles only.
  A run or attack may leave the floor on purpose (a running stride's flight phase, a lunge): use `--raise` there,
  which only lifts what is under the floor.
- A flier's travel loop whose wings beat below the body takes `--raise-uniform` (one lift for the whole loop: the
  depth of its lowest point over the loop), never per-key `--raise`, which follows the wing tips and bobs the body
  with the stroke (MM9 Dragon King 2026-10-30: a 2.5-unit root bob on a loop whose own head motion is 0.6).
- Bend cloth, not limbs: `--lift-joints` with `--lift-only` naming the cloth or membrane chains (`Cloak*`, `Shroud*`,
  `Dress*`, a bat's `Finger*`, a tail). Unrestricted, it bent a Barbarian's clavicle 35 degrees to save 3 cm and swung a
  Druidess's legs until the corpse sank further. Body or limb penetration goes to `--ground-death`/`--raise`, or is
  accepted when the cloth covers it (an `ACCEPTED` note in `floor_audit.py`).
- A pass that must solve on an earlier pass's result (cloth lifted after a hover) runs as a second call on the first
  call's output, since one call's operations run in the fixed order above.
- A root joint a clip leaves at rest gets its own keys when the root moves (MM6 peasant `HemOpening`).

`floor_fix.py` changes only animation samplers (new accessors appended; meshes, skins, materials, variants and LODs
are kept). The editable `.blend` masters are not updated: rerun the same operation after any re-export from them.

## MM8 pass, 2026-10-21

| Model | Fix | Before (world units, tier A) |
| --- | --- | --- |
| Unicorn m544 | `--ground-loop Walking` | every hoof off the floor by up to 7.4 |
| Plane Guardian m592 | `--ground-loop Walking` | every foot off by up to 3.0 |
| Juggernaut m608 | `--ground-death` | rubble corpse 4.8 above the floor |
| Dark Elf Warrior m432 | `--ground-death` | falling body 11.7 under the floor mid-death |
| Dark Elf Female m428 | `--lift-joints Death Dead --ground-death` | skirt strips 7.4 under the floor (strip tops bend at most 9 degrees) |
| Dire Wolf | `--ground-death` | landing 2.9 under the floor (tier C) |
| Thunderbird m552 | `--hover 0.266206` | wing strokes 151 under the floor |
| Phoenix m572 | `--hover 0.288783` | wing strokes 162 under the floor |
| Bone Dragon m616 | `--hover 0.018007` | wings 5.5 under the floor |
| Air Elemental m508 | `--hover -0.079833` | 8 above the floor at its lowest |
| Fire Elemental m496 | `--hover -0.056103` | 5.4 above the floor at its lowest |
| Raven Man m584 | `--hover -0.397589` | 29.8 above the floor at its lowest (stood 41.5 up) |
| Dragon Turtle m580 | `--hover -0.017098` | 11 above the floor at its lowest |

The audit then passes all 198 MM8 bindings. The Centaur's apparent 10/25-unit walk/run penetration is its parked
arrow, 0.9 mm long, now excluded as a collapsed part. (MM8's `--ground-loop` runs used its first, lift-only form.)

## MM6 pass, 2026-10-21

Seven models were installed from `claude_shared/material_pass/batch/`, not a project export, so every MM6 fix starts
from a copy of the installed source in the project's `work/floor_fix_base/`, writes `export/mm6_<x>_floor.glb` and
installs it with `--name mm6_<x>.glb`; each project README records its operation and the values before.

| Model | Fix | Before (world units, tier A) |
| --- | --- | --- |
| Peasant M2, Guard, Titan, Jackalman, Minotaur | `--ground-loop Walking` | every foot off by 2.6–12.4 |
| Goblin gob2 | `--ground-loop` idles and walk, `--raise` run/attack/cast/hit, `--ground-death` | whole body 5–6 into the floor in every clip, cast 11.7 |
| Rat, Ogre | `--ground-loop` walk (and run), `--raise` attack/hit | paws/feet 3.8–9.9 under |
| Barbarian | `--raise Hit --ground-death` | hit 4.7, corpse 3.1 under |
| Nobleman | `--lift-joints Attack` | cloak 4.9 under in the attack |
| Druidess, Cleric | `--lift-joints Death Dead --lift-only 'Cloak*'` | cloak 15 / 14 under; legs under the cloak accepted |
| Skeleton, Ghost | `--lift-joints Death Dead --ground-death` | skull 5.5, shroud heap 15 under |
| Peasant F4 | `--ground-death` | corpse 3.3 above |
| Beholder, Bat, Bloodsucker, Wasp Demon | `--hover 0.116799 / 0.175229 / 0.193200 / 0.041315` (Bat, Bloodsucker: then wing/tail lifts) | 6–33 under |
| Robot, Air and Fire Elementals | `--hover -0.237515 / -0.144721 / -0.056268` | 4–38 above at their lowest |

Accepted (notes in `floor_audit.py`): the Sea Serpent, Water Elemental and Demon Queen sink away by design; the Air
and Fire Elemental corpses are empty; the Fire Elemental's ember cards drift under the floor at the end; legs under
the Druidess's and Cleric's cloaks. `death_effect` bindings (burn, disintegration, explosion) are not judged for
their death and corpse. The audit then passes all 173 MM6 bindings.

## MM7 pass, 2026-10-21

41 of the installed MM7 models were fixed from the audit's own findings (operations per model in each project
README's "Floor fix" note; pre-fix exports in `work/floor_fix_base/`):

- **Cloth first:** robes, skirts and coats (`--lift-joints ... --lift-only 'B_Skirt*,Robe_*,…'`) bend their strips
  up before any body move, so the Wight's walk (skirt 18.3 under the floor), the Necromancer and the Clerics keep
  their feet where they were. The Troglodyte's tail lifts out of its fidget (27.1 under) with `--lift-only 'B_Tail*'`.
- **Ground actors:** `--ground-loop` on sunk or hopping stands, walks and runs (Titan stood 8.4 under, Lich walk 11,
  Skeleton 3.4, Minotaur/Manticore/Blaster Guy hops), `--raise` on sunk attacks, hits, casts and fidgets, and
  `--ground-death` on every sinking death or corpse (Elf Spearman 26.5, Cleric Sun corpse 7.5).
- **Fliers:** `--hover` at the suggested amount, plus `--ground-death` where the fall sank: Roc 0.266206 (the MM8
  Thunderbird body), Bat 0.234281, Beholder 0.036502, Gargoyle 0.029246, Angel 0.023967 (death 42 under), Sea Monster
  0.021724, Harpy −0.023936 (death 70 under).

The audit then passes 270 of 273 MM7 bindings. Left open: the Behemoth's Attack, whose left claw strikes 16.6–20.8
world units into the ground at the blow; raising the root would hop the whole body, so it waits for a decision.
Fixed 2026-11-11 (MM6–MM8 audit, anim stream): the left upper arm lifts at most 9.4° around the blow
([mm7_m162_animfix_claude](../../mm7_m162_animfix_claude/README.md)); the floor audit passes.

`--smooth CLIP SECONDS` and `--smooth-loop` (with `--smooth-hold`, `--smooth-median`) low-pass a clip's root offsets instead of
solving each key alone; use them when the lowest point is flying cloth or a limb and the jitter gate fails on the
root (MM9 Yrsa, `../../mm9_yrsa_claude/README.md`).
