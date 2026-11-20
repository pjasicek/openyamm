# MM7 3D batch D: Undead and non-human humanoids

Five MM7 creatures for one Claude session, built one after another in the order below. Four other sessions work on
batches A–E at the same time; each touches only its own projects. The full batch list is in
[README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Skeleton Warrior | `mm7_m398` | `mm7_m398_claude` | 397 Skeleton, 398 Skeleton Warrior, 399 Skeleton Lord | installed 2026-10-20 |
| 2 | Wight | `mm7_m430` | `mm7_m430_claude` | 421 Wight, 422 Wraith, 423 Barrow Wight | installed 2026-10-20 |
| 3 | Lich | `mm7_m270` | `mm7_m270_claude` | 289 Lich, 290 Power Lich, 291 Lich King | installed 2026-10-20 |
| 4 | Ghoul | `mm7_m470` | `mm7_m470_claude` | 454 Ghast, 455 Ghoul, 456 Revenant | installed 2026-10-20 |
| 5 | Troglodyte | `mm7_m418` | `mm7_m418_claude` | 412 Troglodyte Drone, 413 Troglodyte Soldier, 414 Troglodyte Queen | installed 2026-10-20 |

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
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_gob2_claude/ (rig-first on a non-human body) and mm6_bar1_claude/.

These are two-armed but not ordinary humans (exposed bones, gaunt or monstrous bodies). Use the mm6_gob2_claude/ rig-first route for non-human proportions. Skeleton and Wight have thin limbs and visible gaps between bones: check that the weights do not bridge across gaps. Held weapons are separate attachment GLBs.

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

Nothing shared was changed; each workaround lives in the project's own script copy.

- **G6 contact gate (reference copies from `mm6_bar1_claude` / `mm6_gob2_claude`):** the cone test reported a flat
  back rib 13 cm away as a 6 cm contact (m398). The m398 copy confirms each hit with a ray-parity inside test; the
  reference scripts could take the same fix. The face index it prints is an index into a filtered face list, so it
  cannot be traced back to the mesh.
- **Blade edge gate (reference copy):** it assumes a long blade; the m430 dagger needed a `BLADE_T` range override.
- **Mixamo retarget world rule (`retarget_mixamo.py`, playbook default):** it copies the source's absolute bone
  directions, so a body whose spine is not upright (the m418 troglodyte) is stood up straight. m418 adds `KEEP_REST`:
  pelvis, spine, neck, head and clavicles keep the mesh's rest frame and take motion relative to Standing frame 0. The
  playbook has no route for hunched or horizontal bodies.
- **Human death clips on horizontal bodies:** a 90-degree backward fall stood m418 on its tail; its death is authored
  (`author_death.py`, a roll onto the back with a floor pass).
- **Meshy auto-rig on non-humanoid bodies:** for m418 it was unusable (a hand on the tail, the knees 0.5 m apart in
  depth). The joints were measured on the mesh (geodesic limb rings and slices); 5 credits were spent on the rig and
  not used. A pre-check of the creature's shape could skip the purchase.
- **`stride.py` (reference copy):** the median planted-foot speed gave −1.56 m for m418's lurching Mutant walk. The
  stride came from the source travel that `:inplace` removed (2.377 m per cycle).
- **Residual contacts in the exported models:** m418's attack follow-through and fidget still reach about 7 cm
  (README gates); m470's death about 6 cm. These need review rather than a tool fix.
