# MM7 3D batch J: Peasants: dwarves, elves and goblin men

Five MM7 creatures for one Claude session, built one after another in the order below. Other sessions work on the
other batches at the same time; each touches only its own projects. The full batch list is in [README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Peasant Dwarf Male | `mm7_m302` | `mm7_m302_claude` | 322–330 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m302_reduce_claude`) |
| 2 | Peasant Dwarf Female | `mm7_m312` | `mm7_m312_claude` | 313–321 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m312_reduce_claude`) |
| 3 | Peasant Elf Male | `mm7_m332` | `mm7_m332_claude` | 340–348 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m332_reduce_claude`) |
| 4 | Peasant Elf Female | `mm7_m322` | `mm7_m322_claude` | 331–339 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m322_reduce_claude`) |
| 5 | Peasant Goblin Male | `mm7_7m452` | `mm7_7m452_claude` | 439–447 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_7m452_reduce_claude`) |

All projects live under `level_generation/creatures/`. The native projects hold the original frames and the
validated sprite restorations; read from them, do not change them.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## How to build each model

Run the creature-to-3d workflow (`.agents/skills/creature-to-3d/SKILL.md`, `CREATURE_TO_3D`) for each creature, one
at a time, and follow the **Claude humanoid NPC playbook** fully (read it before the first model; humanoid:
`level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md`, quadruped:
`level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md`). Also follow
`level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (five HD masters from the native bitmaps before any
Meshy job), `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set, region mask and
per-tier colour ramps from the MM7 palettes, separate 1K head set) and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_pman_claude/ (cheapest run),
mm6_pfem_claude/ (cloth skirt, braid), mm6_bar1_claude/ and mm6_gob2_claude/ (non-human body, for the goblin).

One model per body: each body has three outfits (A, B, C) with three tiers each, and all nine share the same native
frames and differ only in palette (see the native project's `variants.json`). So build one mesh, rig and clip set
per body and cover all nine looks with colour tiers from the MM7 palettes (region mask plus per-tier ramps); a
separate outfit mesh is only justified if the native frames really differ in shape, and must be recorded in the
project README. Peasants flee rather than fight: check the native attack/fidget frames and match them. After the
first body, reuse your own rig and clip set for the others where the proportions allow.

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

- **Goblin fixes after install (2026-10-20):** Standing soles lifted onto the floor and the death replaced (Armed Death 1:
  the billhook went through the left thigh); reinstalled (`mm7_7m452_claude` and `mm7_7m452_reduce_claude` READMEs).
- **Goblin billhook hold (7m452, user decision):** the model carries the billhook in one hand, level at the hip with the
  blade forward (as the native walk). The native stands holding it in both hands and raises it upright with both
  hands in the fidget; that is not reproduced. Keep the one-handed carry, or author a two-handed Standing and Fidget?
- **Peasant deaths in long dresses (m312):** the floor-length dress cannot cover a wide backward stride, so the dwarf
  woman uses a crouch-and-fall with damped legs; her legs are painted as dress cloth in the corpse. Review in the viewer.
- **Shared stride tool:** `stride.py` (copied into each project) returned a negative stride for m322's walk; the README
  value there is estimated from the planted-foot travel. No shared tool was changed.
- **Installed 2026-10-20** at the user's request ("accept all"): the five reduced models and their props in
  `assets_source`/`assets_dev`, 45 `actors.yml` bindings; boot check on Harmondale (`output/batchJ_boot/`).
- Process note: the user overrode the one-after-another rule mid-batch; models 3–5 were built in parallel by agents.
  Each model's README lists its own limits for review; none is installed or checked in game.
