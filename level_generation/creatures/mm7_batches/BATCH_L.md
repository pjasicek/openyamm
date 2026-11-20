# MM7 3D batch L: the last new models

The last six MM7 creatures that need a new 3D model, for one Claude session, built one after another in the order
below. Other sessions work on the other batches at the same time; each touches only its own projects. The full batch
list is in [README.md](README.md).

## The six models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Earth Elemental | `mm7_m198` (MM7), `mm8_m504` (MM8) | `mm8_m504_claude` | MM7 235 Clay, 236 Stone, 237 Earth Elemental; MM8 79 Lesser, 80, 81 Greater Earth Elemental | installed |
| 2 | Sea Monster | `mm7_m394` | `mm7_m394_claude` | 394 Giant Shark, 395 Piranha Shark, 396 Dragon Shark | installed |
| 3 | Blaster Guy | `mm7_m475` | `mm7_m475_claude` | 457 Tolberti, 458 Robert the Wise, 459 Blaster Guy C | installed |
| 4 | Dog | `mm7_m509` | `mm7_m509_claude` | 469 Dog A, 470 Dog B, 471 Dog C | installed |
| 5 | Cat | `mm7_7m500` | `mm7_7m500_claude` | 463 Cat A, 464 Cat B, 465 Cat C | installed |
| 6 | Chicken | `mm7_7m504` | `mm7_7m504_claude` | 466 Chicken A, 467 Chicken B, 468 Chicken C | installed |

All projects live under `level_generation/creatures/`. The native projects hold the original frames and the
validated sprite restorations; read from them, do not change them.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## How to build each model

Run the creature-to-3d workflow (`.agents/skills/creature-to-3d/SKILL.md`, `CREATURE_TO_3D`) for each creature, one
at a time, and follow the matching playbook fully (read it before the first model of its kind): humanoid
`level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md` for Blaster Guy and Earth Elemental, quadruped
`level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md` for the animals and the Sea Monster. Also follow
`level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (five HD masters from the native bitmaps before any
Meshy job), `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set, region mask and
per-tier colour ramps from the native palettes, separate 1K head set where there is a face) and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_bar1_claude/ and mm6_gob2_claude/
(humanoids), mm6_rat_claude/ (small quadruped), mm8_m512_claude/ (MM8 Dire Wolf, for the dog's gait only; the art
differs).

**Earth Elemental** is the same art in MM7 and MM8 and neither world has a model yet: build it once, in
`mm8_m504_claude`, with variants for both worlds' tiers (MM8 palettes for 79–81, MM7 palettes for 235–237; check
whether they are the same palettes first). Export `mm8_m504.glb`; the README gives the MM8 install and binding, and
the MM7 binding that points to the same model, so one copy serves both. It is a heavy stone humanoid: stiff, heavy
motion.

**Sea Monster** is a shark that lives in water: no legs or floor contact. Keep it at the water surface or below it
as the native frames show (check how the engine places it: water-only movement), give the body and tail a swimming
chain, and write the decision into the README.

**Blaster Guy** is a humanoid with a gun: the blaster is a separate attachment GLB, the ranged attack fires from a
muzzle socket. Tiers A and B are the named NPCs Tolberti and Robert the Wise, so check each tier's look against its
own frames; if they differ in more than colour, record it.

**Dog, Cat and Chicken** are small ambient animals with low-resolution native frames: keep the triangle budget low
for their size, and do not invent detail the frames do not show beyond what the HD masters need. The chicken walks
on two legs with wings folded: use the quadruped playbook's own-rig route with two legs. Match their native fidget
and walk timing.

Finish one model completely (all clips, gates, textures, LODs, exports, viewer check) before starting the next. Before
any paid Meshy animation, check the animation library first (`anim_library/README.md`) and ingest every paid result.

## Do not install: keep everything in the projects

The user will decide later when these go into the game. Until then:

- Do not run `tools/install_model.py`, and do not write anything under `assets_dev/` or `assets_source/`.
- Do not edit `actors.yml`, model manifests, monster tables or any other runtime binding or table.
- Do not change shared tools, playbooks or skills, or another project (including the installed MM8 models and their
  projects). If one needs a fix, note it under **Open issues** below.
- Each model stops at accepted project exports in the project's export folder. The project README lists the exact
  `tools/install_model.py ...` command(s) and the `actors.yml` binding you would add, ready to apply later.
- Check visually with `python3 tools/run_creature_review.py --project level_generation/creatures/<project>` (the
  project viewer), including the playbook's gates on every clip.
- An in-game check is optional and only in a private asset root under `output/`, launched with
  `./tools/run_game.sh --isolated <name> --world mm7 ... --assets <that root>`. If that root uses hard links, delete
  the link and write a new file before changing anything, so the real `assets_dev/` is never modified. Note in the
  project README how it was checked.

## When the batch is done

Report per model: export paths, gate results, Meshy spend, and anything left for the user to review. Collect
problems that need the user's decision here:

## Open issues

- **LOD builder rounding at the atlas edge.** After the LOD0 halving, `tools/build_actor_lods.py` left one LOD2/LOD3
  vertex of the Blaster Guy at u = -0.00001 (its source UVs touch 0 exactly), and `tools/merge_head_material.py`
  rejects any coordinate outside [0, 1]. `mm7_m475_claude/scripts/clamp_uv.py` clamps it before the merge; a small
  tolerance in either shared tool would make that step unnecessary.
- **Earth Elemental, one model for two worlds** (resolved 2026-10-21). Every world package is mounted together, so the
  MM7 binding resolves the MM8 path. MM8's Earth Elemental A–C had an interim binding to the MM6 model in MM6's
  `actors.yml` (2026-10-19), which collided with the new MM8 binding (a descriptor may be bound once across worlds);
  the user chose `mm8_m504.glb` and the interim entries were removed.
- **Single-look creatures and the shared build tools.** Blaster Guy, Dog, Cat and Chicken have one look (all three
  descriptors draw the same group and palette), but the shared region-variant step expects colour variants. Each
  project uses a local `scripts/set_extras.py` for the material extras only. A no-variant mode in the shared tool would
  remove these copies.
- **Quadruped playbook and two-legged birds.** The batch asks for the chicken on the quadruped own-rig route, but its leg
  measurement (`measure_quad.py`) and rig (`rig_rat.py`) assume four legs. The chicken uses a new `rig_chicken.py`
  (joints read off slices, folded-wing bones) and `anim_chicken.py` in its project. The playbook could add a bird
  section that points to them.
- **Fused geometry from Smart Topology.** The chicken's toe tips were fused across both feet (14 bridge faces, deleted in
  `rig_chicken.py`). The playbook's mesh checks do not look for limbs joined to each other; a check would have caught it
  before rigging.
- **Small-animal speeds.** At the binding scales, MM7's speed 140 is 0.98 m/s for the 45 cm chicken, so one native walk
  loop would need 0.85 m strides. Its walk runs two step cycles per native loop. Dog and Cat play at 1.05× and 1.0×.
