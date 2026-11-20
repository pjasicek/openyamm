# Gait rollout: sprints and locomotion fixes for every MM6–MM8 3D monster (2026-10-31)

The user's request (2026-10-31): fix every installed MM6–MM8 3D monster whose walk, run or (new) sprint plays outside
the gait window, after the sprint pilot (MM6 Ogre and KnightPlate in `../mm6_sprint_humanoids_claude/`, the MM6, MM7 and
MM8 rats). Work runs as packages, four agents at a time; the coordinating session writes `actors.yml`.

## Why

The engine plays a locomotion clip one loop per stride of travel (`game/gameplay/ActorModelPresentation.h`), so a body
moving far faster than its clip was authored for pedals in tiny rapid steps. Monsters chase at twice their speed, and
under the MAW ruleset a hostile melee monster faster than 150 moves at Spd / 2 + 300, so it chases at up to twice
Standard's speed. Running faster is mostly a longer stride, not quicker steps, so such bodies get a third clip:
`animation.sprint` with `sprint_stride_length`. The engine picks walk, run or sprint by misfit (`actorModelGait`) and
caps playback at 2x (`ActorModelDefaultMaxGaitRate`; feet slide above it). See
[the post-process, step 3](../CREATURE_POSTPROCESS.md#3-strides-walkrunsprint-choice-and-playback-rate).

## Scope

`ledger.py` lists every model whose gate fails (`ledger.json`: problems per tier, body type, projects). 129 at the
start: 13 footless bodies (snakes, medusas, nagas, oozes, Couatl, Salamander, Efreeti, Juggernaut) were bound by the
coordinator with `gait_rate` ([0.8, 1.5]; the rolling Juggernaut [0, 0]) and need no clips. The other 116 are in the
packages below.

## Package brief (every agent reads this)

Read the repository's `AGENTS.md` and `CLAUDE.md` first: no `git add`/commit/stash/reset/restore, no Vulkan builds, no
paid Meshy or other spending, keep diagnostics out of committed scripts.

**Target.** For each model of your package, `gait_gate.py` passes:

```sh
python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world <w> --model <glb>      # targets
python3 level_generation/creatures/claude_shared/postprocess/gait_gate.py --world <w> --model <glb> \
    --candidate <export.glb> [--set walking=Walk2] [--set run=Jog] [--set sprint=Sprint] [--set *_stride_length=..]
```

It checks the stride (what planted feet cover), the window 0.75–1.5x on Standard's wandering and chasing and MAW's
chasing, and the floor rules (including the sprint clip). A model bound in two worlds (MM8's Earth Elemental and Gog
are also MM7's) must pass in both. Usually that means some of:

- a `Sprint` for MAW's chase (when MAW changes the speed: melee monsters faster than 150);
- a better run (`Jog`, or a slower run) when Standard's chase plays the run outside the window;
- a better walk (`Walk2`) when Standard's wandering plays outside it.

Add new clips under new names, appended to the **currently installed** source
`assets_source/worlds/<world>/models/<glb>` (it carries the far-LOD repair and head-bob fixes; project exports may
predate them). Existing clips, meshes, skins and materials stay byte-identical. Keep a copy of the pre-change source in
your package's `work/` for rollback.

**Humanoids and other two-legged bodies.** Use the composer of `../mm6_sprint_humanoids_claude/` (read its README:
library loops for legs/pelvis/trunk, arms and props from the model's own run, two-bone IK, planted soles, floor,
`align: Walking`, `stance_foot: Standing` with `foot_toe_out_deg: 5`, `bend_toes`, `foot_smooth`, arm clearance) and
its lineage `../mm8_pirates_gait_claude/`. Package h16 extended the composer (`h16/scripts/`, see `h16/README.md`):
Meshy joint names, arms from the library run for models without a run, an even pelvis drop on both steps (no limping
head bob: `uneven` under about 0.3), a rigid guard lift for two-handed weapons, loincloth rule, lower swing foot,
per-side arm clearance, probes for candidates (`bob_probe.py`, `foot_heading_probe.py`, `prefix_check.py`); start from
that copy. Package h02 (`h02/scripts/`, `h02/README.md`) adds a swing-foot lift, a rigid both-arms raise for
two-handed weapons, arm abduction and a forward elbow bend, a Mixamo-name rename round trip, and found that the
pilot's `clear_arms` (push along the body-skin normal) turns arms inward on tunics and kilts and `elbow_flex_deg` swings
the hand across the body when the forearm's swing is mostly twist: check both, or use h02's options. Many installed
walks and runs are half a loop apart from each other (align new clips to the walk) and plant splayed feet (new clips
still plant at about 5°). Package h08 (`h08/scripts/`) has a numpy port of the robed projects' cloth simulation (coat skirts, capes, robes;
with a final collision pass so knees stay inside at run speeds) and a dagger-follows-sheath option. The walk-as-run
rule only holds while the chase is a walking pace (Froude ≤ 0.65): a chase at a run pace gets a run (h08's Monk and
Vampire). Package h04 (`h04/scripts/`) adds skirt follow and push-out (knees through skirts), a staff lift, and fixed a
fall-through in h02's `raise_arms` when `elbow_forward_deg` is set (use h04's copy of that function). Peasants flee at a
run pace (2.5–2.7 units/s), so they jog in both rulesets. Package h07 (`h07/scripts/`) adds `arm_raise_deg` with `arm_raise_window`: a weapon arm lifted forward only while the
knee on its side comes through (a carried sword the faster run's thigh would hit). `gait_gate.py` does floor-check the sprint (`floor_audit.py` reads `sprint`). Do not edit those projects: copy what you need into your package's
`scripts/` (or import it unchanged). Library loops are in the git-ignored `anim_library/` (README: humanoid set,
Mixamo; sprint, fast run, jog, walk variants). Fit the body: heavy bodies take shorter, heavier steps and a powerful
low sprint, casters in robes keep a robe-safe gait, peasants a plain civilian run.

**Four-legged and other multi-legged bodies.** Procedural gaits per the
[quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md). Precedents: the rat sprints
(`../mm6_rat_claude/scripts/sprint_rat.py`, `../mm7_m382_claude/scripts/sprint_rat7.py`,
`../mm8_m452_claude/scripts/anim_sprint.py`) and each model's own gait script in its project; graft with
`../claude_shared/graft_clips.py`. Start from package q3's `scripts/quad_gait.py` (q2's moved paw contacts to an averaged position, which sinks
claws on a skewed rest pose) and `quad_probe.py`. Check a stride the gate suggests against the authored one: swing
paws skimming the floor lower its measurement. A sprint is a gallop or bound with lower duty, longer flights and spine flexion, the
extra stride coming from the body's travel in flight.

**Phase.** The engine keeps one gait phase (0–1) and switches walk, run and sprint at it. A new clip strikes with the
same foot at the same phase as the model's walk; if the installed walk and run disagree (the MM6 Ogre's were half a
loop apart), align new clips to the walk and say so.

**Feet.** Planted feet point along travel (about 5° toe-out at most, like an accepted walk), flat, never splayed; the
swing foot does not flare. Paws of four-legged bodies keep their rest pose's toe-out (the engine switches clips
instantly, so a new clip must match the accepted ones); their head bob is judged against the model's accepted gaits,
not the bipeds' 4–7 %. On rigs whose toe joint is off the foot's long axis (h06's LizardArch, ElemEarth) the joint-based heading misreads:
measure from the foot mesh with `h06/scripts/foot_mesh_heading_probe.py` (h06 also has a per-side
`foot_toe_out_deg`). Measure with `../mm6_sprint_humanoids_claude/scripts/foot_heading_probe.py` (or the
coordinator's `foot_yaw.py` idea: foot-to-toe joint on the ground plane) and look at front-view filmstrips.

**Standing decisions of the user.**
- Walk-as-run (CREATURE_POSTPROCESS.md): slow human-sized bipeds whose hurried speed is a walking pace walk when they
  chase in Standard (pirates, peasants, casters). Keep that for Standard; MAW's faster chase gets a sprint (or a run
  bound as `sprint`). The MM6 FighterLeath and the MM7/MM8 Gog walk at every Standard speed by the user's choice; keep
  their Standard walk, give MAW's chase a sprint, and report it.
- Bodies that flee (Wimps: peasants) are judged at the flight speed (2x) in both rulesets.

**Gates before install** (all on your export): `gait_gate.py` PASSED in every world the model is bound in (a tier no
clip can cover: explain why, with numbers, as `../mm8_pirates_gait_claude/` did for the Pirate Mage);
`level_generation/decorations/mm8_3d/animated/scripts/check_winding.py` 0 inverted; head bob
(`claude_shared/postprocess/bob_audit.py`, walks about 3–5 %, runs and sprints 4–7 %); for humanoids the "Arm and hand
gate" of `../CLAUDE_HUMANOID_NPC_PLAYBOOK.md` plus contact probes (no hand, forearm or prop inside legs or trunk); the
foot heading; playback review with the authorized wrapper `python3 tools/run_creature_review.py`
(`tools/CREATURE_REVIEW.md`) that you look at yourself.

**Install and hand-off.** Install with `tools/install_model.py <export.glb> --world <w> --name <glb>` (serialised
installs; never copy into `assets_dev`). Do not edit any `actors.yml`: write `<package>/bindings.yml` (format below)
for the coordinator. Write `<package>/README.md` (dated; per model: clips, sources, numbers, gate window sections,
doubts, rebuild commands) and a dated "Gait rollout" section in each model's latest project README (rebuild commands,
and that a far-LOD repair rerun must re-graft these clips). Do not edit shared tools under `claude_shared/`, the
pilot projects or engine code; report problems with them instead. If something blocks a model, finish the others and
report the blocked one with the reason.

`bindings.yml`:

```yaml
- world: mm7
  descriptors: [Fighter Chain A, Fighter Chain B, Fighter Chain C]
  walking: Walk2               # clips.walking; omit when unchanged
  animation:                   # keys under animation; omit unchanged ones
    run: Jog
    run_stride_length: 3.21
    sprint: Sprint
    sprint_stride_length: 4.4
```

The coordinator applies them with `apply_bindings.py <package>/bindings.yml` and reruns `ledger.py`.

## Packages

Directory `gait_rollout_20261031/<id>/`. Status lives in `STATUS.md`.

| id | models (world/glb: descriptor family) |
|---|---|
| q1 | mm6_ckt Cockatrice, mm6_spi1 Spider, mm7_m402 Spider, mm6_wyrm DragonLand |
| q2 | mm8_wolf Dire Wolf, mm7_m509 zdog, mm7_7m500 zcat, mm7_m382 zrat (Standard walk only; Rat A-C done) |
| q3 | mm8_m516 Thunder Lizard, mm8_m564 Gorgon, mm7_m266 Hydra, mm7_m278 Manticore |
| q4 | mm8_centaur Centaur, mm8_m544 Unicorn, mm8_m548 Crystal Dragon, mm7_7m504 zchicken |
| h01 | mm6_bar1 Barbarian, mm6_fgt FighterLeath, mm6_figc FighterChain, mm6_thf BThief |
| h02 | mm6_dwa1 BDwarf, mm6_min1 BMinotaur, mm6_wwf Werewolf, mm6_jak1 Jackalman |
| h03 | mm6_arc1 BArcher, mm6_cle Cleric, mm6_sor1 Sorcerer, mm6_dru1 Druidess, mm6_lch BLich |
| h04 | mm6_pfem PeasantF1, mm6_pman_v2 PeasantM1, mm6_pmn2 PeasantM2, mm6_fmp PeasantF2, mm6_mep PeasantM3 |
| h05 | mm6_mfp PeasantF3, mm6_natf PeasantF4, mm6_natm PeasantM4, mm6_nobl Nobleman, mm6_mer1 Merchant |
| h06 | mm6_demon Demon, mm6_ert ElemEarth, mm6_ske Skeleton, mm6_gob2 BGoblin, mm6_gua Guard, mm6_lzd LizardArch |
| h07 | mm7_m222 Fighter Chain, mm7_m226 Fighter Leather, mm7_m230 Fighter Plate, mm7_m406 Swordsman |
| h08 | mm7_m290 Monk, mm7_m410 Thief, mm7_m418 Troglodyte, mm7_m422 Vampire |
| h09 | mm7_m438 Zombie, mm7_m470 Ghoul, mm7_m430 Wight, mm7_m398 Skeleton Warrior, mm7_m270 Lich |
| h10 | mm7_m254 Golem, mm7_m162 Behemoth, mm7_m286 AMinotaur, mm7_m461 ATroll, mm7_m190 Dwarf |
| h11 | mm7_m170 Cleric Moon, mm7_m174 Cleric Sun, mm7_m274 Mage, mm7_m294 Necromancer, mm7_m426 Warlock |
| h12 | mm7_m178 Devil, mm7_m214 Elf Archer, mm7_m218 Elf Spearman, mm7_m246 Goblin, mm7_m475 zBlasterGuy |
| h13 | mm7_m302, mm7_m312, mm7_m322, mm7_m332 (dwarf and elf peasants) |
| h14 | mm7_m342, mm7_m352, mm7_m362, mm7_m372 (human peasants) |
| h15 | mm7_7m452, mm7_m442 (goblin peasants), mm8_m504 Earth Elemental (MM7 and MM8), mm8_m612 Gog (MM7 and MM8) |
| h16 | mm8_lizardman_peasant, mm8_m404 Lizardmen Warrior, mm8_m576 Triton, mm8_m456 Dragon Hunter |
| h17 | mm8_m412, mm8_m416, mm8_m420 pirates, mm8_m656 Human Mercenary, mm8_m620 Bedraggled Human |
| h18 | mm8_m424, mm8_m428, mm8_m432 dark elves, mm8_m604 Ether Knight, mm8_m460 Cleric |
| h19 | mm8_m436 Ogre Peasant, mm8_m440 Ogre Warrior, mm8_m540 Ogre Mage, mm8_m520 Cyclops |
| h20 | mm8_m476 Troll, mm8_m480 Troll Peasant, mm8_m484 Minotaur, mm8_m488 Minotaur Peasant |
| h21 | mm8_m444 Wererat Human Form, mm8_ratman Ratman Form, mm8_m468 Vampire, mm8_m632 Dark Dwarf, mm8_m628 Skeleton Archer |
| h22 | mm8_m592 Plane Guardian, mm8_m596 Crystal Walker |

## Composite viewer

`viewer/index.html` shows every changed model (132: the pilot, the 26 packages, the footless and rolling bindings):
its old and new walk, run and sprint side by side, each on a treadmill moving at the clip's bound stride (planted feet
stand still when the stride is right), with a shared-phase mode (as the engine switches clips), views, attachments,
and per tier the in-game playback rates before and after under Standard and MAW. Open it through the repository
server: `http://127.0.0.1:8912/level_generation/creatures/gait_rollout_20261031/viewer/index.html` (`#<model id>`
selects a model). After binding or clip changes, rebuild the manifest with `python3 viewer/build_manifest.py`
(old bindings and clip sets are read from git HEAD of the repository and of `assets_source`).
