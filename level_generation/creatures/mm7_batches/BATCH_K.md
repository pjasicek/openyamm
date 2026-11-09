# MM7 3D batch K: Peasants: humans and goblin women

Five MM7 creatures for one Claude session, built one after another in the order below. Other sessions work on the
other batches at the same time; each touches only its own projects. The full batch list is in [README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Peasant Human1 Male | `mm7_m352` | `mm7_m352_claude` | 358–366 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m352_reduce_claude`) |
| 2 | Peasant Human1 Female | `mm7_m342` | `mm7_m342_claude` | 349–357 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m342_reduce_claude`) |
| 3 | Peasant Human2 Male | `mm7_m362` | `mm7_m362_claude` | 367–375 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m362_reduce_claude`) |
| 4 | Peasant Human2 Female | `mm7_m372` | `mm7_m372_claude` | 376–384 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m372_reduce_claude`) |
| 5 | Peasant Goblin Female | `mm7_m442` | `mm7_m442_claude` | 430–438 (outfits A, B, C) | installed 2026-10-20 (reduced, `mm7_m442_reduce_claude`) |

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
first body, reuse your own rig and clip set for the others where the proportions allow. Goblin Female was blocked by
image-service refusals during sprite restoration, so build it last. If the image service refuses an HD master or
texture request, do not rephrase it to get around the refusal: mark that model `blocked: refusal` in the table, note
the request under **Open issues** and continue with the next model.

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

## Triangle reduction (user request 2026-10-20: "do tris reduction on all 5")

RETOPOLOGY_PLAYBOOK.md no-retexture route, one `mm7_<id>_reduce_claude/` project per model (templates: batch J's
`mm7_m302/m332/m312/7m452_reduce_claude/`), run in parallel. Source = the current batch export, kept byte for byte as
each project's `work/*_source_pre_reduce.glb` (rollback). Textures, looks, ramps, skins and clips identical to the
source; hands/fingers, eyes, face front and soles kept exactly; no Meshy credits. **Not installed**: install the
reduced export (command in each README) instead of the batch one; REDUCTION_LEDGER rows at install time.

| Model | LOD0 source → reduced | LOD1 / LOD2 / LOD3 reduced | p99 / max mm (limits 5.1 / 25.5) | Project |
|---|---|---|---|---|
| m352 Human1 Male | 9,045 → 7,871 (−13 %) | 3,934 / 1,518 / 431 | 3.35 / 22.3 | `mm7_m352_reduce_claude/` |
| m342 Human1 Female | 9,920 → 8,683 (−12 %) | 4,337 / 1,556 / 512 | 4.14 / 24.2 | `mm7_m342_reduce_claude/` |
| m362 Human2 Male | 9,448 → 8,180 (−13 %) | 4,085 / 1,630 / 532 | 4.80 / 20.8 | `mm7_m362_reduce_claude/` |
| m372 Human2 Female | 10,944 → 8,546 (−22 %) | 4,272 / 1,534 / 504 | 2.56 / 23.3 | `mm7_m372_reduce_claude/` |
| m442 Goblin Female | 9,534 → 7,978 (−16 %) + sickle unchanged | 3,987 / 1,649 / 515 | 4.27 / 24.6 | `mm7_m442_reduce_claude/` |

Cuts are modest: every source had already been reduced once in its build (head and hands protected), and deeper
steps failed the gates or showed in the textured close-ups (m352: tunic flecks where large faces' UVs crossed into the
belt/stud texels; found by a project-local `sliver_check.py`, not by the playbook's `texture_drift.py`). Viewer checks
pass on all five. For review: m372 LOD3 has one face over 20x stretch in the Death; m342 LOD3 is 2 cm taller (a hair
vertex); m442 LOD3 dips up to 1 cm lower in Death/Walking. Tool note: the reduce ladders use a pymeshlab venv from
another session's scratchpad (each README says how to recreate it).

## Installed 2026-10-20

At the user's request: the five reduced models and the sickle in `assets_source/worlds/mm7/models/` (runtime copies
cooked into `assets_dev`), 45 bindings appended to `assets_dev/worlds/mm7/models/actors.yml` (from each project's
`integration/actors.yml`), ledger rows in `../REDUCTION_LEDGER.md`. Bindings use one explicit scale per model and no
`scale_reference`: the first install used it and the engine rejected the whole MM7 actors.yml ("actor model scale
requires a valid standing sprite: Peasant Human2 MaleA A", sprite `m363s` not found), so for a few minutes no MM7 actor
models loaded. Boot check on Harmondale (`7out02.odm`, two looks of each model spawned): no load errors, 185 actors
textured, 0 missing (`output/batchK_boot/`).

## Open issues

Batch result (2026-10-20): all five exported, none installed; 150 Meshy credits in total (30 each). The user asked
mid-batch to build models 2–5 in parallel instead of one after another. Every project README lists the install
command, its `integration/actors.yml`, gates and known limits. No in-game check was run (optional for this batch).

For the user's decision:
- **No attack clips**: the native peasant attack reuses the walk frames, so every binding plays Walking for
  `attack_melee`/`attack_ranged` (MM6's male peasant v2 used Standing instead). Run → Walking (speed 140 is below the
  run threshold); cast → Standing.
- **Skirts (m342, m372)** use the batch-B robe chains with batch J m312's legs under the skirt (see the floor/walk fix). m372's death leaves sleeve-cuff and robe stretch above the gates while she falls (arm p99 4.6,
  robe 4.25); the bell sleeves are simulated only in the death.
- **m372 has six palettes, not nine**: outfits B and C share palettes 376–378 (`m372_ba/bb/bc`).
- **m442**: the sickle stays in her hand in the death (the native throws it); scale assumes sprite scale 1.0 (no scale
  in its sprite-frame file); the HD master shows more cleavage than the sprite.
- **Deaths**: m352, m362 and m442 use Falling Back Death and end with one knee raised (native corpses lie flat).
- Smaller limits per README: m362 left-arm fidget stretch 2.25 and a straight-hanging scabbard; m342 hands sink up to
  6 cm into the wide skirt; m372 skin uses 132 joints (above batch B's 128 ceiling, the renderer packs 128 per row).

Walk fix (user review 2026-10-20, "foot/ankle/zig-zag"): batch A/J's `foot_level.py` (constant roll per foot for the
walk) and `walk_bob.py` (even pelvis bob, legs re-solved) applied to all five and replayed. Head height second
difference 2.9–6.3 → 0.53–0.84 cm; m352/m362 switched to Mixamo Standard Walk (Walk's own feet changed 17° per frame;
now 10.3–11.7°), upper arms out 6° in the walk. Measured with each project's `scripts/walk_probe.py`.

Floor/walk fix for the two human women (user review 2026-10-20, "in the air", "walks very funny"): m342 and m372 now use
batch J m312's dress route: legs and shoes on the leg bones under the skirt (the shoes had ridden the hem chains, so
the figure floated with the hem and the feet slid and splayed), the set's short Relax Walk Forward with flattened feet
and an even bob, and the set's Unarmed Death 1 with legs damped to 40 %. Soles on the floor in every standing clip.

Playbook / shared-tool notes (not applied, per the batch rules):
- Meshy weights sleeves that hang beside a bodice or gown (puffed blouse sleeves m342, bell sleeves m372, goblin
  sleeves m442) partly to the pelvis; each project now moves that weight back to the arm (project-local rules).
- `finger_weights.py`: the non-adjacent-finger cleanup also needs to run on unlabelled palm vertices (m352 right hand
  5.1x → 3.7x).
- Region ramps: rank-matching the full native luminance range brings the sprite's baked deep shadows onto smooth Meshy
  cloth as dark patches; a native quantile window (35–97 %) for cloth keeps tier A matching Meshy's colour.
- Meshy's auto-rig can tilt the head ~40° when a veil/hood covers the neck (m372 `axial_fix.py`).
