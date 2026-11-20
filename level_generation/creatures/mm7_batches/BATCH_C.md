# MM7 3D batch C: Elves, dwarves and giants

Five MM7 creatures for one Claude session, built one after another in the order below. Four other sessions work on
batches A–E at the same time; each touches only its own projects. The full batch list is in
[README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Elf Archer | `mm7_m214` | `mm7_m214_claude` | 247 Elven Archer, 248 Elven Scout, 249 Elven Ranger | installed 2026-10-20 |
| 2 | Elf Spearman | `mm7_m218` | `mm7_m218_claude` | 250 Elven Warrior, 251 Elven Defender, 252 Elven Lancer | installed 2026-10-20 |
| 3 | Dwarf | `mm7_m190` | `mm7_m190_claude` | 229 Dwarven Soldier, 230 Dwarven Lieutenant, 231 Dwarven Commander | installed 2026-10-20 |
| 4 | Thief | `mm7_m410` | `mm7_m410_claude` | 406 Thief, 407 Rogue, 408 Master Thief | installed 2026-10-20 |
| 5 | Titan | `mm7_m414` | `mm7_m414_claude` | 409 Titan, 410 Storm Titan, 411 Blood Titan | installed 2026-10-20 |

All projects live under `level_generation/creatures/`. The native projects hold the original frames and the
validated sprite restorations; read from them, do not change them.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## How to build each model

Run the creature-to-3d workflow (`.agents/skills/creature-to-3d/SKILL.md`, `CREATURE_TO_3D`) for each creature, one
at a time, and follow the **Claude humanoid NPC playbook** fully (read it before the first model; humanoid: `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md`, quadruped: `level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md`). Also follow
`level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (five HD masters from the native bitmaps before any
Meshy job), `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set, region mask and
per-tier colour ramps from the MM7 palettes, separate 1K head set) and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_bar1_claude/ and mm6_gob2_claude/.

Body proportions vary a lot in this batch (slim elves, short dwarf, giant Titan): fit every rig to its own native frames, not to the previous model. The Titan is large in game: check its in-game height against the monster descriptor height and record it. Spears, bows and axes are separate attachment GLBs.

Finish one model completely (all clips, gates, textures, LODs, exports, viewer check) before starting the next. Before
any paid Meshy animation, check the animation library first (`anim_library/README.md`) and ingest every paid result.

## Do not install: keep everything in the projects

The user will decide later when these go into the game. Until then:

- Do not run `tools/install_model.py`, and do not write anything under `assets_dev/` or `assets_source/`.
- Do not edit `actors.yml`, model manifests, monster tables or any other runtime binding or table.
- Do not change shared tools, playbooks or skills. If one needs a fix, note it under **Open issues** below.
- Each model stops at accepted project exports: the final GLB, any attachment GLBs, LODs and textures in the project's
  export folder. The project README lists the exact `tools/install_model.py --world mm7 ...` command(s) and the
  `actors.yml` binding you would add, ready to apply later.
- Check visually with `python3 tools/run_creature_review.py --project level_generation/creatures/<project>` (the
  project viewer), including the playbook's gates on every clip.
- An in-game check is optional and only in a private asset root under `output/`, launched with
  `./tools/run_game.sh --isolated <name> --world mm7 ... --assets <that root>`. If that root uses hard links, delete
  the link and write a new file before changing anything, so the real `assets_dev/` is never modified. Note in the
  project README how it was checked.

## When the batch is done

Report per model: export paths, gate results, Meshy spend, and anything left for the user to review. Collect
problems that need the user's decision here:

## User review 2026-10-20 (fixed, re-exported, not installed)

- All five: the planted feet stood 5-10° on their outer edges; `foot_level.py` now also levels the sole roll (batch A's
  rule), idle/attack/fidget feet within 4° of flat (`foot_flat.py` in each project).
- Elf Archer and Elf Spearman: the walk tucked the weapon arm against the body; it now holds the idle's arm beside the
  body with a small swing (`arm_hold.py`).
- Elf Spearman: the thrust put the right arm 10-12 cm into the chest; the shaft line moved down and out of the chest and
  both elbows are cleared on the final weights (`elbow_clear.py`, `arm_torso_probe.py`). The archer's quiver reach got
  the same elbow pass (forearm 11.5 cm into the neck at one frame).
- Dwarf: the hip skin poked through the mail skirt in the walk (3.5 cm); the skirts take the skin's weights where they
  lie on it (walk ≤ 0.2 cm).
- Titan: the walk kept the empty-hand swing (palm up, blade across the thighs); it now carries the sword palm to the
  hip, blade forward.

## Second review 2026-10-20 (fixed, re-exported, not installed)

- All five: the roll levelling of the first review turned the ankles up to 44° per 1/48 s at heel strike and toe-off
  (the spearman's "dislocated" ankle in walk frame 17). The roll is now weighted to the flat-planted frames, capped and
  smoothed over the clip; foot turn in every walk and run is back to the source clips' ≤ 17.5° per 1/48 s, idle feet
  stay within 2.6° of flat.
- Elf Archer: the tooled bracer of the left forearm is copied onto the bare right forearm (`bracer_map.py`,
  `bracer_apply.py`; mirrored rest geometry, normals turned through the mirror).
- Elf Spearman: the return to the idle after the thrust starts at full reach (16 frames instead of 10), the right arm
  follows an IK arc out of the chest and is smoothed (`smooth_arm.py`); blow 0.862 s (binding impact updated in the
  README).

## Third review 2026-10-20 (fixed, re-exported, not installed)

- All five: the walk's head went down, up, down around each heel strike: a 1-3 cm pelvis hitch in the source Mixamo Walk
  / Dwarf Walk. `bob_smooth.py` low-passes the walk's pelvis height over the cycle and re-solves the legs to the same
  feet; one smooth dip per step now (the runs were already smooth).
- Thief: a 23 cm sliver from the mask across the chest to the right upper arm (seen as a skin triangle fused to the
  vest) and shards off the mask; `despike.py` puts the spike tips back on the surface (rest positions only).

## Triangle reduction (user request 2026-10-20: "do the tris reduction playbook on these 5")

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) (texture-aware ladder, no retexture), one project
per model (`mm7_<id>_reduce_claude/`, scripts from batch A's `mm7_m406_reduce_claude/`), sources = the accepted
exports above. Installed 2026-10-20 with `BATCH_C_stage/install.sh` (user acceptance). No Meshy credits; weapons left byte-identical (fitted grips, thin blades); not installed. Rollback
sources in each project's `work/*_source_pre_reduce.glb`; details, checks and install commands in each README.

| Model | Body LOD0 | LOD1 / LOD2 / LOD3 | Pick | p99 / max mm (limit) |
|---|---|---|---|---|
| Elf Archer | 8,037 -> 6,931 (-14 %) | 3,456 / 1,405 / 476 | f2 r86 | 4.56 / 22.66 (5.19 / 25.95) |
| Elf Spearman | 9,586 -> 8,616 (-10 %) | 4,285 / 1,654 / 504 | h r89 | 2.74 / 7.61 (5.41 / 27.04) |
| Dwarf | 10,027 -> 8,995 (-10 %) | 4,497 / 1,799 / 590 | j r89 | 3.83 / 18.92 (4.2 / 21) |
| Thief | 11,282 -> 9,077 (-20 %) | 4,537 / 1,995 / 671 | t r80 | 3.95 / 18.89 (5.4 / 27) |
| Titan | 10,320 -> 8,946 (-13 %) | 4,473 / 1,788 / 669 | l r85 | 5.26 / 23.13 (5.79 / 28.95) |

Every reduced body keeps its hands/fingers exactly (grip checks: positions within 0.0007 mm, weights equal), the
model's top in every LOD, clips/materials/variants identical (compare_glb), 0 inverted parts, and passes its viewer
check (source vs reduced). The cuts are modest: each source body was already reduced once in its build and the
features kept exactly are 50-60 % of the mesh. Review points: Spearman's slung back shaft goes ~26 cm into the floor
while lying in Death (source issue, unchanged); Dwarf's darker patch above the mail-skirt front hem; Titan's skirt
strips slightly simpler in clay (fallback k86 at 9,042); Thief's vest kept whole (its studded pattern tears under a
cut; further reduction would need a retexture).

## Thief textures (user review 2026-10-20, fixed)

Angular light/dark patches on the Thief's bare arms and trousers: arm texels misclassified as gold/metal (raw Meshy
paint and shine), per-triangle AO steps and UV-space blurs across unrelated islands. Fixed in `compose_m410.py`
(arm skin by bone, flat body skin, 3D-averaged AO, 3D patch evening) plus a smoothed arm normal field; source and
reduced exports carry the new textures (README of each project).

## Open issues

- **Arm-into-torso probe (project-local, `arm_torso_probe.py`):** the G6 gate samples only forearms and hands, so an
  upper arm inside the chest (the Spearman's thrust) passed it. A shared upper-arm check would catch this earlier.
  The probe flags thin shells as false hits (the Thief's sheath, the Dwarf's mail over the bare upper arm).

- **Review viewer template (shared, not changed):** the per-project `review/viewer/review.js` copied between projects
  has fixed camera focus heights for a ~1.8 m figure (head at 1.78 m: the head shot of the 1.43 m Dwarf showed only a
  horn tip) and its feedback text was labelled "MM6 Sea Serpent". Fixed locally in `mm7_m214_claude`, `mm7_m218_claude`
  and `mm7_m190_claude`; a template that reads the model height would avoid it.
- **Dwarf (m190), for your review:** Smart Topology modelled six digits per hand (thumb + five fingers). The extra,
  shortest finger was removed by script (`remove_finger.py`); a small flat facet remains on the outer knuckle. The
  thumb's fist wrap is capped at 30° (the thumb leaves the palm far up this hand). If you prefer, a new Smart Topology
  run (5 credits) could be tried instead.
- **Dwarf (m190) binding:** the native tiers draw the sprite at scale 1.0 / 1.05 / 1.10, so the three `actors.yml`
  entries need different `scale` values (104.69 / 109.92 / 115.16; README).
- **Thief (m410), for your review:** the authored attack draws the dagger from the left-hip sheath and sheathes it again
  (as the native does); for about two frames at each end the right hand and forearm press up to 5 cm into the belt,
  because the hilt sits within a fist's thickness of the body. The sheathed dagger also touches the left thigh in the
  run (2.3 cm) and the lying death (3.9 cm). Its sprite frames draw at scale 1.1 (binding scale 112.30), so tiers A and
  B walk and tier C runs.
- **Titan (m414), for your decision:** at the binding scale 374.06 (helmet top 655 units vs the descriptor's 650) the
  MM7 speed 200 plays the walk at 0.29x its natural speed — a slow, heavy stride; a shorter-stride walk would play
  faster but shuffle. The native's crumbling death and rubble corpse are not modelled (the corpse is the lying body).
