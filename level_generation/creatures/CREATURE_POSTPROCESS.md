# Creature post-process: a world's installed 3D monsters

A pass over every installed 3D monster of one world, after its creatures are produced: sizes against the native
tables, floor contact, walk/run choice and playback rate, and texture crispness. MM8 and MM6 were done on 2026-10-21
(results below); run the same steps for MM7 (`--world mm7`) and later worlds. Every tool reads the world's
`assets_dev/worlds/<world>/models/actors.yml` and the installed sources in `assets_source/`, and needs no Blender.

| Step | Tool | Fixes go into |
| --- | --- | --- |
| 1. Scales | `claude_shared/postprocess/scale_audit.py` | `actors.yml` (`scale`, `scale_reference`) |
| 2. Floor contact | `claude_shared/floor/floor_audit.py` | the GLB's clips, with `claude_shared/floor/floor_fix.py` |
| 3. Strides, walk/run/sprint and playback rate | `claude_shared/postprocess/stride_audit.py`, then `gait_audit.py` (also `--ruleset maw`) | `actors.yml` (`stride_length`, `run_stride_length`, `sprint`, `sprint_stride_length`, `animation.gait_rate`), else the clips |
| 4. Textures | `claude_shared/postprocess/texture_audit.py` | nothing by default (the cook rules apply), else a `<model>.cook.yml` |
| 5. In-game look | `tools/run_game.sh --isolated` with a tour | — |
| 6. Head bob of bipeds | `claude_shared/postprocess/bob_audit.py` | the GLB's walk/run clips, with `claude_shared/postprocess/bob_fix.py` |

Paths are relative to `level_generation/creatures/`. Run the tools from the repository root, for example
`python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world mm7`. Each takes `--match` with a
descriptor glob (texture audit: a file glob) to look at one family.

## 1. Scales

```sh
python3 level_generation/creatures/claude_shared/postprocess/scale_audit.py --world mm7
```

- **Rule:** each tier's effective scale relative to tier A must equal the ratio of their standing sprite scales
  (sprite frame data, `scale` of the first standing frame). The effective scale is `scale`, times
  sprite scale(descriptor) / sprite scale(`scale_reference`) when the binding names one (`WorldFxSystem.cpp`).
- A `MISMATCH` row is a binding error. Fix it with explicit per-tier scales (preferred; `scale_reference` broke a
  cross-world lazy load once, see `mm8_m404`), then record the values in the project README. MM8's only mismatch was
  Triton B/C copying tier A's scale (now 144.71 and 155.85).
- The absolute column compares native front-frame height × sprite scale with the model's standing height. It is
  informational: native frames include raised weapons, wings and hover padding, fliers are fitted by silhouette area,
  and each project README says what its scale was fitted to. Read the README of every `look` row before changing
  anything; on MM8 every one was explained.
- `monster_descriptors.txt` Height is the collision height, not a visual size: never scale to it.
- MM6 monster sprites are atlas entries (`atlas:mm6_ske/skesta`), so the absolute column is unavailable there; the tier
  check still applies. When a tier check and a headless regression disagree, check the original table
  (`reference/mmerge_data_forus/Data/Tables/SFT.txt`, scale / 65536): MM6's Skeleton and MM8's Triton regressions had
  encoded equal tier scales that the original data does not have.

## 2. Floor contact

```sh
python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world mm7 --json /tmp/floor.json
```

The engine never snaps a model to the floor: model y = 0 is the actor's floor, and `z_offset` moves the corpse too.
The rules, tolerance (larger of 2.5 world units and 1 % of the standing height) and every operation are in
[the floor README](claude_shared/floor/README.md). In short:

- **Ground actors:** standing on the floor, walking never below it nor with every foot off it, every living clip above
  it, death never through it, corpse on it.
- **Fliers and hoverers** (`canFly`, or the world's families in `HOVERERS` in `floor_audit.py`): the lowest point over
  all living clips meets the floor, baked with `floor_fix.py --hover <suggested hover>`; never `z_offset`.
- **Exceptions** are explicit: `z_offset` bindings (a bodiless light, a fish school) are listed, not judged, and
  `ACCEPTED` in `floor_audit.py` holds a reasoned note per family. Add the new world's hoverers and accepted notes there.

Fix workflow per model, from the project whose export matches the installed source (`sha256sum` both; on MM8 the
installed sources were the `*_reduce_claude/export/` files). When no project export matches (MM6: seven models came
from `claude_shared/material_pass/batch/`), start from a copy of the installed source in the project's
`work/floor_fix_base/`, write `export/<model>_floor.glb` and install it with `--name <model>.glb`, as the MM6 pass did:

```sh
d=level_generation/creatures/<project>; m=<model>
mkdir -p $d/work/floor_fix_base && cp --update=none $d/export/$m.glb $d/work/floor_fix_base/$m.glb
python3 level_generation/creatures/claude_shared/floor/floor_fix.py $d/work/floor_fix_base/$m.glb $d/export/$m.glb \
  <--ground-loop Walking | --ground-death Death Dead | --lift-joints Death Dead --ground-death Death Dead |
   --hover <amount> Death Dead>
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $d/export/$m.glb
python3 tools/install_model.py $d/export/$m.glb --world <world>
```

Then re-run the audit, and add a dated "Floor fix" note to the project README (the `.blend` master predates it).
Judge before fixing: a fall's few-centimetre dip into grass is invisible, while a whole body or a skirt under the floor
is not. A model shared between worlds (MM8's Air Elemental export is byte-identical to MM7's) is fixed per world copy.

## 3. Strides, walk/run/sprint choice and playback rate

```sh
python3 level_generation/creatures/claude_shared/postprocess/stride_audit.py --world mm7
python3 level_generation/creatures/claude_shared/postprocess/gait_audit.py --world mm7 [--ruleset maw]
```

Clip time follows the distance travelled: one loop of the walk, run or sprint per `stride_length`
(`run_stride_length`, `sprint_stride_length`) of travel, so how a gait looks depends only on the game's speed against the stride, never on the clip's length (retiming
a clip changes nothing in game). Two things must hold:

- **The binding stride is what the clip's feet cover.** Otherwise planted feet slide: a binding longer than the clip's
  stride skates them forwards, a shorter one backwards. `stride_audit.py` measures every walk and run clip twice:
  the backward speed of the foot vertices on the floor, and of the foot joints while they are low, each times the clip
  length. Where the two agree (within 12 %) the measurement is trusted and a binding more than 10 % off is flagged
  (`<<`): write the measured value. Where they disagree, a binding that neither supports is marked `??` for a look by
  eye: robed shuffles (the MM8 Necromancer's feet pivot under the robe with no planted phase), slithering bodies with
  no feet (Cobra, Medusa, Naga, Couatl, Salamander, oozes; any stride is as good there) and runs with little floor
  contact. A run that reuses the walk clip (`run: Walking`) needs `run_stride_length` equal to `stride_length`; the
  default 1.55 x slides its feet while chasing.
- **The stride suits the game's speeds.** A monster wanders at its `monster_data.txt` speed, pursues at twice that
  and flees at twice that (`PursueMoveSpeedMultiplier`, `FleeMoveSpeedMultiplier`, as the original:
  `re_mm8/CREATURE_MOVEMENT.md`; pursuit was 1.75 from 2026-10-22 until commit 40b7e8c47, and the stride pass and
  walk-as-run rule below were measured with it). The audits take a Wimp (AI type, peasants: it only flees) at the
  flight speed. So the walk should suit the wandering speed and the run the chasing one.
- **MAW's fast melee monsters need a sprint.** Under the MAW ruleset a hostile melee monster faster than 150 moves at
  Spd / 2 + 300 (`MawMonsterRules.cpp`), so it chases at up to twice Standard's speed. Running faster is mostly a
  longer stride, not a quicker one, so such a model gets a third clip, `animation.sprint` with its
  `sprint_stride_length` (pilot 2026-10-31: MM6 Ogre and KnightPlate, the MM6/MM7/MM8 rats), authored for MAW's chase;
  the run stays authored for Standard's. `gait_audit.py --ruleset maw` and `gait_gate.py` show the speeds.

The engine (`game/gameplay/ActorModelPresentation.h`, `actorModelGait`) plays the clip that suits the speed best: each
clip's misfit is the log of the rate it would play at, doubled below 1x (a crawling run reads worse than a quick walk),
with a small preference (1.25x) for the run or sprint while hurrying and the walk while wandering, and an 8 % margin
for the clip playing now. A chaser whose run would play in slow motion therefore walks, and one too fast for its run
sprints. Clip time then follows the distance, up to a ceiling of twice the clip's authored rate
(`ActorModelDefaultMaxGaitRate`); above it the feet slide. That ceiling (2026-10-31, the user's choice when MAW's
speeds played runs at up to x5 as frantic skipping) is a safety net for clips not yet fixed, not a substitute for a
suitable stride: a 1.5x cap tried on 2026-10-21 made two thirds of the ground monsters slide and was removed the same
day. A world's actors.yml may say `gait: intent` (MM9's): its models play the clip the AI asks for (walk while
wandering, run or sprint while hurrying) while it plays within [1 / sqrt(max), max], as MM9's WalkTo and RunTo
(`actorModelIntendedGait`; `gait_audit.py` mirrors it and takes MM9's `mm9_ai` walk and run speeds).
Bindings set their own playback range with `animation.gait_rate: [min, max]` (max 0: uncapped):

- `[0.8, 1.5]` for fliers and swimmers, so a slow drifter keeps beating and a fast one glides;
- `[0, 0]` for rolling bodies (the MM8 Malevolent Boulder), whose contact follows the distance at any rate.

`gait_audit.py` prints, for wandering and chasing, the clip, the model-space speed and the playback rate, flags rates
outside 0.75-1.5 for bodies with foot contact, and ends with the flagged models, worst first, with their rates over
every tier, and a `slide` where the ceiling holds the clip back. Fix the strides first (above), then set `gait_rate`
for the world's fliers and swimmers; whatever stays flagged is clip authoring: the clip covers far less (or more)
ground per loop than the game moves the monster. Fix those in the creature project with a new stride, not a retime:
procedural gaits (the quadruped playbook) regenerated with the stride the target speed needs, humanoids with a
better-suited walk, jog or sprint from the animation library, heavy bodies with shorter, heavier steps. Then measure
again and write the binding. Do not lower a walking body's ceiling below the default, which slides it. Stationary monsters (`monster_data.txt` Move `stand`, the MM7 Treants) never move and are left out.

Gate for new clips, before the install:

```sh
python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world mm8 --model mm8_m472.glb
python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world mm8 --model mm8_m472.glb \
    --candidate <project>/export/mm8_m472.glb --set walking=Walk2 --set run=Jog [--set sprint=Sprint]
```

Without `--candidate` it prints the model's targets under Standard and MAW: every tier's wandering and chasing speed,
the authored speed (stride over clip length) a walk, a run and a sprint need to keep every tier inside the window, and
whether one clip can serve two of them. With it, the candidate GLB and the `--set` binding changes must pass the stride
check (`stride_audit.py`), the window on every tier (`gait_audit.py`: Standard's wandering and chasing, MAW's chasing)
and the floor rules (`floor/floor_audit.py`); the stride of a changed or new clip left out of `--set` is taken from a
trusted measurement. A sprint must strike with the same foot at the same phase as the walk and run: the engine keeps
one gait phase and switches clips at it. Add new clips under new names, keep the old ones, record playbacks of old and new with the creature
review wrapper, then install and write the printed values to `actors.yml`.

Stride pass (2026-10-21, all three worlds): measured strides written for 86 MM6, 129 MM7 and 48 MM8 descriptors (most of
the walk-as-run peasants and casters carried the 1.55 x default; the MM6 Barbarian's walk was bound at 1/1.55 of its
run, the Monk's at 3.4x its 0.46 m shuffle, and the MM8 Cyclops and Pirate Mage runs at twice their clips). Left for
clip work: the MM8 Necromancer (robe shuffle, unmeasurable) and every `??` row. After the pass, `gait_audit.py` flags 37
MM6, 46 MM7 and 43 MM8 models; the worst are the MM6 Monk and Spider, MM7 Robot, Rat, Treant (no walk clip; it is
stationary, which the game now honours) and Titan (slow motion), and MM8 Crystal Walker, Wererat Rat Form, Necromancer
and the pirates.

Walk-as-run rule (2026-10-22, with pursuit at 1.75x). User: slow monsters (the MM8 pirates) should walk, not run,
when they hurry. A human-sized biped (1.3-2.6 m) whose hurried speed is a walking pace, Froude number v^2 / (g x hip
height) <= 0.65 (people change to running near 0.5), binds its walk as the run, per tier, when a walk clip covers that
speed at 0.75-1.5x: `run: <walk clip>`, `run_stride_length` = that walk's measured stride. 34 tiers: MM6 LizardArch A;
MM7 AMinotaur C, ATroll A/B, Elf Archer A, Golem A-C; MM8 Pirate Mage, Pirate Crossbowman (all tiers), Wimpy Pirate
Mage, Wimpy Pirate Crossbowman, Wimpy Pirate Warrior A-C, Pirate Warrior A (Regnan Bandit, by the user's choice: x1.61), Ogre Mage A and the Ogre, Troll and Dark Elf Female
peasants. Pirates use whichever of `Walk2` (stroll) or `Walking` (brisk) plays nearer 1x; Pirate Mage B/C walk although
their best walk plays just outside the window (x1.50, x0.72). Tiers above the threshold keep their run, so a model can
walk on its slow tiers and run on its fast ones. Hip heights come from the thigh joint in Standing. Needing a brisker
walk clip before they can walk: MM6 PeasantM2, MM7 Zombie A, MM8 Vampire Female Peasant. By the user's choice the MM6
FighterLeath and the MM8/MM7 Gog walk at every speed (x1.4-2.4 when chasing). Flagged bindings with pursuit at 1.75x:
88 MM6, 163 MM7, 94 MM8 (1.5x: 67/151/73; 2x: 99/179/107); 12 chases play below 0.75x (MM6 Guard, MM8 Dark Elf
Warrior and Skeleton Archer the worst, x0.60-0.74), the rest are pre-existing fast runs and Wimps fleeing at 2x.

## 4. Textures

Nothing to run per model: the cook rules (`tools/cook/model_textures.yml`, class `worlds/*/models/*.glb`, see
[ASSET_COOKING_PLAN.md](../../ASSET_COOKING_PLAN.md)) apply to every world. They keep full-size normal maps on desktop,
lift weak normal relief toward a 90th-percentile tilt of 0.25 (at most 3×, never weakening a strong map), and sharpen
colour mips below the first (0.75). Outdoors, creatures also take 40 % of their sky light from a camera-side key light
(`OutdoorRenderer.cpp`), as indoors (60 %).

```sh
python3 level_generation/creatures/claude_shared/postprocess/texture_audit.py --world mm7
```

- `WEAK`: relief still below 0.15 after the lift (MM8: the crossbowwoman, the troll peasant and its club). A
  sidecar `normal_strength` can push one model further; a flat Meshy normal map needs a new bake in its project.
- `flat map`: a normal map with no relief at all (most held weapons); harmless, or remove it in the project.
- `no normal map`, `specular 0`: authored choices (elementals, crystals; the wolf, serpentman and turtle have specular
  off). Revisit only with the project's reasons in its README.
- A model's `<name>.cook.yml` overrides `normal_scale`, `normal_strength`, `colour_mip_sharpening` and sizes. Changing
  the rules re-cooks every model (the `openyamm` build runs `tools/cook_models.py`, about 8 minutes for all 1,642
  models); Android cooks on demand with `tools/cook_android.sh`.

## 5. In-game look

Use the humanoid playbook's fixed cameras (outdoor New Sorpigal `oute3.odm` at (-3718.493, 3245.946, 1), yaw 3.359;
indoor `6d19.blv` at (1672.832, -2938.578, -46.896), yaw 3.132), with `--world mm6` so the merged monster table spawns
any world's monster. A tour opens the console once, spawns each monster with `actor spawn <monster id> 1 x y z`,
closes it and captures; `actor kill <radius>` kills them through the normal damage path, but corpses become loot
satchels within about 1.5 s, so corpse grounding is judged from the audit, not screenshots. Compare against the
project's own `review/ingame/` captures from the same camera.

```sh
./tools/run_game.sh --isolated pp-<name> --world mm6 --map oute3.odm --position -3718.493 3245.946 1 \
  --yaw-radians 3.359 --pitch-degrees -10 --set debug.actor_models=true --set debug.immortal=true \
  --set debug.menu_input_tour_path=/abs/tour.yml --warmup 3 --seconds 22
```

## 6. Head bob of bipeds

```sh
python3 level_generation/creatures/claude_shared/postprocess/bob_audit.py --world mm7
```

The head's peak-to-peak height in each walk and run clip, in per cent of its standing height; it is the pelvis's
travel on almost every model. Walks should sit near 3-5 % and runs near 4-7 % (people: 2.5-3 % and 4-6 %); `uneven`
above about 0.6 means one step rises higher than the other. `bob_fix.py` rescales the pelvis bob, evens the steps or
lays a synthetic leg-timed bob on a gliding clip, and solves the legs again so the feet keep their exact paths
(strides and floor contact unchanged). Judge with the in-game rate from `gait_audit.py`: a big bob played at 2x reads
far worse. Workflow, targets, checks and the before/after viewer: [head_bob_claude](head_bob_claude/README.md).

MM6-MM8 pass (2026-10-22, user-approved in the viewer and installed): 35 clips of 29 models, among them the MM6 Ogre
run (10.3 to 6.5 %), MM8 Ogre Warrior run (13.2 to 6.4 %), MM6 Goblin run (16.4 to 6.4 %) and MM7 Behemoth run
(16.7 to 6.6 %); gliding runs raised (MM6 Barbarian, MM8 Dragon Hunter 2.2 to 4.5 %). Left flagged: the Troglodyte
walk and Ether Knight run (never chosen in game), the Behemoth and Devil walks (their spine nods), the bird and lizard
bipeds, and the MM8 Necromancer (its robe would sink).

## MM6 results (2026-10-21)

- **Scales:** one mismatch fixed: Skeleton B/C copied tier A's 123.6; now 141.26 / 158.91 (SFT 0.7 / 0.8 / 0.9), with
  the `mm6_skeleton_actor_model_tiers_follow_the_native_frame_scales` regression updated to match.
- **Floor:** 22 models fixed (table in [the floor README](claude_shared/floor/README.md#mm6-pass-2026-10-21)), worst a
  Goblin standing 5–6 units in the floor in every clip. All 173 bindings then pass.
- **Gait:** `gait_rate: [0.8, 1.5]` on the free fliers and swimmers (Beholder, Bat, Bloodsucker, Wasp Demon, Robot,
  Gargoyle, Harpy, Genie, DragonFly, Ghost, Cover Dragon, Air, Fire and Water Elementals, Sea Serpent). Clip
  authoring follow-up: Spider (chase slide 3.8), Dwarf (its run is authored slower than its walk), Cobra, Barbarian,
  Medusa, Peasant F3/M3, Cave Dragon and Rat slid under the former cap (their legs now play fast); the Titan's run
  plays at 0.45x.
- **Textures:** weak relief after the lift on the Cockatrice head, the Merchant head and hands and the Peasant M1
  (`mm6_pman_v2`) body; specular is off on many MM6 models (an authored choice of the older pipeline).

## MM7 starting point (2026-10-21, before any MM7 fix)

- Scales: all 76 families' tier scales match their sprite tables.
- Floor: 137 of 228 bindings outside tolerance. Mostly deaths sinking 2.5–10 units, with several larger: Elf Spearman
  −26.5, Harpy −70, Angel −42. Many humanoids stand 1–2 units sunk (Titan −8.4, Wight −3.6). Walks sink (Wight −18,
  Lich −11). Corpses are under the floor for Cleric Sun (−7.5) and Peasant Dwarf Female (−6), and above it for Elf
  Archer (+3.6). Fliers: the Roc carries the uncorrected Thunderbird dip (hover 0.266206), Bat 0.234281, Beholder
  0.036502, Angel, Gargoyle, Harpy and Sea Monster small amounts. Behemoth's attack dips 16.6 and Troglodyte's fidget
  27.
- Gait: 63 of 228 bindings flagged before any `gait_rate` overrides.

## MM7 outcome (2026-10-21)

- Scales: 91 families, no tier mismatch (unchanged).
- Floor: 41 models fixed and reinstalled; 270 of 273 bindings pass. Details and the one open item (Behemoth Attack,
  claw into the ground) are in [the floor README](claude_shared/floor/README.md#mm7-pass-2026-10-21).
- Gait: `animation.gait_rate: [0.8, 1.5]` on the 17 fliers of the monster data (Griffin, Roc, Bat, Dragonfly,
  Beholder, Wyvern, Angel, Gargoyle, Harpy, Genie, Ghost, Sea Monster, Air/Fire/Light Elementals, Ultra Dragon,
  Dragon) and the gliding Water Elemental, as on MM8: 82 flagged bindings down to 42. The rest is clip authoring:
  Titan and Dragon walk in slow motion (authored 1.85 and 1.33 m/s against about 0.5 in game); Rat, Spider, Robot
  (0.33 m per walk cycle on sliding spikes), Earth Elemental, Gog, Troglodyte, the Fighter Chain/Plate B/C,
  Fighter Leather C, Devil C, Troll C and Blaster Guy run or walk faster than their clips (1.3–5×: slid under the former cap, their
  legs now play fast); Dog, Cat and
  Chicken have no run clip; the Treant has no walk clip (it is stationary).
- Textures: weak relief left as on MM8: the Troll body and club (the MM8 troll peasant's maps), the Genie's lamp
  (corpse only) and the Zombie's held forearm. Held weapons carry flat normal maps (harmless).
- In game (`oute3.odm`, hostile launch spawns of Titan, Wight, Troglodyte, Skeleton, Angel, Gargoyle, Roc, Bat, Harpy,
  Behemoth; Lich and Necromancer seen in other runs): feet, claws and hems on the ground, fliers at a sensible height.
