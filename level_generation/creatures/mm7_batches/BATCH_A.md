# MM7 3D batch A: Human warriors

Five MM7 creatures for one Claude session, built one after another in the order below. Four other sessions work on
batches A–E at the same time; each touches only its own projects. The full batch list is in
[README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Fighter Chain | `mm7_m222` | `mm7_m222_claude` | 253 Conscript, 254 Soldier, 255 Fighter | installed 2026-10-20 (reduced) |
| 2 | Fighter Leather | `mm7_m226` | `mm7_m226_claude` | 256 Robber, 257 Raider, 258 Bandit | installed 2026-10-20 (reduced) |
| 3 | Fighter Plate | `mm7_m230` | `mm7_m230_claude` | 259 Initiate of the Sword, 260 Champion of the Sword, 261 Master of the Sword | installed 2026-10-20 (reduced) |
| 4 | Swordsman | `mm7_m406` | `mm7_m406_claude` | 403 Swordsman, 404 Guard, 405 Adventurer | installed 2026-10-20 (reduced) |
| 5 | Archer | `mm7_m154` | `mm7_m154_claude` | 202 Archer, 203 Bowman, 204 Elite Archer | installed 2026-10-20 (reduced) |

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
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_bar1_claude/ (default humanoid route, solved sword fist) and mm6_gob2_claude/.

The three Fighter families probably share a body under different armour: build the first fully, then reuse your own rig, skeleton and clip set for the next ones where the native frames allow it, with a separate mesh and texture set per family. Bows, swords and other held weapons are separate attachment GLBs.

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

## Open issues

- **The three Fighter families do not share a body** (native frames): Chain (m222) is a woman with a scimitar, Leather
  (m226) a man with a falchion, Plate (m230) an armoured man in full plate. Each gets its own mesh and rig; only
  Plate and Swordsman (m406) look like the same plate-armoured body under different tabards and weapons, so the
  Swordsman may reuse the Plate rig and clip set. (Session decision, 2026-10-20; the user may prefer otherwise.)
- m222: the empty scabbard on her back is not modelled (Meshy turned it into two spikes; removed). Tier A walks at
  ~1.55x the clip's natural speed; tiers B/C (240/260 units/s) exceed the engine's run threshold at scale 96 and run.
- m406 Swordsman did **not** reuse the Plate rig after all: its native body is different (open spiked helmet over a
  mail coif, bearded face, bare upper arms), so it has its own mesh, rig, weights and textures; it shares the clip set.
- Deviations left for review (details in each README): m226 LOD0 about 4 % over the ~10k guideline; m406 right fist
  one web edge 5.69x (hidden in the fist) and the blade 5.7 cm into the lying body in Death; m154 G4 p99 2.17 at full
  draw (sleeve hem), the drawing hand close to the coif just after the release, the bow tip brushing the boot in the
  fidget.
- m154 Archer: the native holds the bow in the RIGHT hand and draws with the LEFT; the Mixamo archery clips are
  mirrored (`retarget_mixamo.py` `:mirror`, project-local) and joined (`concat_actions.py`). Bow/string/arrow follow
  mm7_m214_claude's rules; arrow release 1.167 s on `Socket_Arrow_Release`. The HD masters gave the tunic a white
  **tree** emblem where the native manifest names a white bird.
- Shared-tool candidates (not changed, per the batch rules): the `:mirror` flag in the project copies of
  `retarget_mixamo.py` and `concat_actions.py` would serve every archer whose handedness differs from Mixamo's.
- **User review 2026-10-20** (viewers): (1) the archer did not aim ahead: the planted retarget kept his torso
  forward, so at full draw the arrow and head pointed 86 deg to his right. Draw/Recoil are now unplanted and he turns
  side-on (`bow_stance.py`, m214's narrowed stance plus a pelvis trim): arrow -0.9 deg, head +0.8 deg at the release.
  (2) On all five the feet stood slightly on the boot edge: every clip rolled the soles 4-11 deg (rest flat), and
  `foot_level.py` only levelled pitch. The project copies now also level the roll on grounded frames, keeping floor
  contact; all five rebuilt, re-gated (gates unchanged within noise) and re-exported, viewers 24/24.
- Shared-tool candidate: the same roll fix belongs in every `foot_level.py` copy (the other MM7 projects share the
  pitch-only version) and in the playbook's "Feet and locomotion" section.
- **Triangle reduction (user, 2026-10-20: "reduce tris on all 5")**: RETOPOLOGY_PLAYBOOK.md no-retexture route, one
  `mm7_<id>_reduce_claude/` project per model (source = this batch's export, kept as `work/*_source_pre_reduce.glb`),
  face, hands/fingers (fitted grips), soles, small pieces and the bowstring kept exactly; no credits; not installed.
  Body LOD0: m222 9,666 -> 8,020; m226 10,455 -> 8,233; m230 8,898 -> 7,492; m406 10,294 -> 8,072; m154 10,253 -> 8,383
  (bow 988 -> 524, arrow 342 -> 210). Swords unchanged. Each stops where the next step fails the ladder limits or
  visibly changes a feature. LOD ratios deviate from 50 % per level where the stock ratios broke the face/helmet at
  LOD3 (see each README). Installed from the reduce projects and listed in REDUCTION_LEDGER.md.
- **User review 2026-10-20, walk/run ankle twitch** (after the foot flattening): the per-frame roll, weighted by how
  close each foot was to the floor, switched on and off at every landing and lift-off (foot turns up to 55 deg per
  frame, source 25). Walk and run now take one constant roll per foot and one constant pelvis shift; foot motion per
  frame matches the source again and grounded roll stays within about 2.7 deg. All five rebuilt and re-exported; the
  fixed clips were transplanted into the reduced exports (`transplant_clips.py`). Viewers 24/24 and 48/48.
- **User review 2026-10-20, uneven head bob in the walk**: the retarget's floor rule set the pelvis height from the
  lowest foot point per frame, so it zigzagged (frame jumps up to 3.7 cm, head acceleration up to 5.8 cm/frame^2)
  and the two steps bobbed differently. New project step `walk_bob.py` (after clip_timing.py; the chain version of
  the MM8 reductions' `smooth_walk_bob.py`): periodic smoothing, both steps alike, reach cap, legs re-solved to the
  same ankle paths (0.01 mm). Head acceleration now <= 0.9 cm/frame^2 on all five; transplanted into the reductions.
  Shared-tool candidate together with the foot roll fix.
- **Accepted by the user 2026-10-20 and staged**: [BATCH_A_stage/](BATCH_A_stage/README.md) holds the reduced exports
  (5 bodies, 4 swords, bow, arrow), the 15 bindings and `install.sh`.
- **Installed 2026-10-20 (user: "install to assets_source and assets_dev")** with `BATCH_A_stage/install.sh`: 11 GLBs
  through `tools/install_model.py --world mm7` (0 inverted closed parts each), the 15 bindings appended to
  `assets_dev/worlds/mm7/models/actors.yml` after Batches E and D (45 bindings, no duplicate descriptors). Added to
  REDUCTION_LEDGER.md.
- **Install fix, missing cast clip (found by the first in-game run)**: the game refused the whole MM7 `actors.yml`
  ("spellcasting actor model requires a cast clip: Archer A"), so for a few minutes no MM7 3D actor loaded. Archer A-C
  (Shield, Lightning Bolt) and Fighter Plate A-C (Bless, Heroism) cast spells in the monster table; their bindings now
  name `cast: Attack` (archer bolts leave `Socket_Arrow_Release`), the installed Batch A section was replaced from the
  rebuilt stage, and `build_stage.py` now fails on a spellcaster without `animation.cast`. Checked in game on 7out01
  (`debug.actor_spawn_id` 202 and 259): the file loads, archers draw and cast Shield, Fighter Plates draw with swords.
  Shared-tool candidate: the viewers and stage checks never load bindings through the game; a binding check that
  runs `WorldFxSystem`'s validation would catch this before an install.
- **Hit/Death foot snap (peer report from batch D, 2026-10-20)**: the per-frame roll weighted by groundedness alone
  snapped a stepping or lifting foot (m230 Hit 22 deg, m154 Death 65 deg per frame; source 9.5 / 37). Non-walk clips now
  use batch C's flatness-weighted, 20 deg-capped, smoothed roll (mm7_m218_claude); walk/run keep the constant roll.
  Every clip's foot turn per frame is within 2 deg of the source on all five; planted roll within 2.7 deg (Hit's
  stepping foot up to 5.6). Rebuilt, transplanted into the reductions, stage rebuilt (`build_stage.py`).
