# MM7 3D batch H: Flying creatures

Five MM7 creatures for one Claude session, built one after another in the order below. Other sessions work on the
other batches at the same time; each touches only its own projects. The full batch list is in [README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Roc | `mm7_m390` | `mm7_m390_claude` | 391 Roc, 392 Greater Roc, 393 Thunderbird | **installed** 2026-10-21 (reduced 6,237, `mm7_m390_reduce_claude`) |
| 2 | Bat | `mm7_m158` | `mm7_m158_claude` | 205 Giant Bat, 206 Vampire Bat, 207 Inferno Bat | **installed** 2026-10-21 (reduced 6,084, `mm7_m158_reduce_claude`) |
| 3 | Dragonfly | `mm7_m186` | `mm7_m186_claude` | 226 Dragonfly, 227 Fire Dragonfly, 228 Queen Dragonfly | **installed** 2026-10-21 (reduced 7,893, `mm7_m186_reduce_claude`) |
| 4 | Beholder | `mm7_m166` | `mm7_m166_claude` | 211 Floating Eye, 212 Gazer, 213 Evil Eye | **installed** 2026-10-21 (reduced 6,814, `mm7_m166_reduce_claude`) |
| 5 | Robot | `mm7_m386` | `mm7_m386_claude` | 388 Seeker Droid, 389 Sentinel Droid, 390 Assassin Droid | **installed** 2026-10-21 (v2 all-metal, retextured, `mm7_m386_v2_claude`, LOD0 5,223; 40 credits incl. v1) |

All projects live under `level_generation/creatures/`. The native projects hold the original frames and the
validated sprite restorations; read from them, do not change them.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## How to build each model

Run the creature-to-3d workflow (`.agents/skills/creature-to-3d/SKILL.md`, `CREATURE_TO_3D`) for each creature, one
at a time, and follow the **Claude quadruped playbook (own rig, automatic weights, procedural clips; air rules from
the MM8 flyers)** fully (read it before the first model; humanoid:
`level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md`, quadruped:
`level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md`). Also follow
`level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (five HD masters from the native bitmaps before any
Meshy job), `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set, region mask and
per-tier colour ramps from the MM7 palettes, separate 1K head set) and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_rat_claude/ (non-humanoid route),
plus level_generation/creatures/mm8_m560_claude/ (wyvern) and mm8_m552_claude/ (thunderbird) for wing bones, flap
clips and air/floor rules.

All five fly and none is humanoid. Roc and Bat are wing-driven; Dragonfly has four wings that need a fast flap;
Beholder is a floating eye with tentacles (soft chains, no wings); Robot is a hovering droid with gun arms (mostly
rigid parts, so prefer rigid binding over skin weights). Match each native flight posture and attack, keep a steady
hover or flight height, and write the flying decision into each project README.

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

- **Roc reuses the MM8 Thunderbird body.** The MM7 Roc frames are the same render as MM8 `m552` with the same
  palettes 553–555 and the same tier-A frame scale; only the feather palette indices differ (MM7 tiers have
  grey-olive, red-brown and black flight feathers). `mm7_m390_claude/` therefore exports the installed MM8 model with
  MM7 ramps (0 credits) instead of a new Meshy build. To be decided at install: ship that separate GLB, or add the
  three MM7 variants to the shared `mm8_m552.glb` (saves about 8 MB when both worlds are mounted).

- **Robot walks, it does not hover.** The batch text says "hovering droid with gun arms"; the native data says
  otherwise (Fly = N for all tiers, separate standing/walking/fidget sprites, spike tips on the ground line, spikes
  sliding in their sleeves in the walk). `mm7_m386_claude/` is a four-spike walker; its README records the evidence. User agreed it walks (2026-10-21).
- **Robot redesign (user, 2026-10-21):** v1 read as a dinosaur skeleton fused with robot parts; it must be a fully
  metallic robot, and its attack is the gun shot. Rebuilt from new HD masters in `mm7_m386_v2_claude/`.
- **Monster tint column is ignored by the engine.** Robot B/C share palette 386 and differ only by the descriptor
  TintColor (`0x93c4ba`, `0xd8c462`), which OpenYAMM reads but never applies, so the sprite tiers look identical in
  game. The 3D Robot reproduces the original tints in its ramps. This affects every tinted monster's sprites.
- **Beholder reduction misses the geometric gates** (p99 3.79 mm vs 2.78, IoU 0.970 vs 0.98): picked from close-ups
  (brain folds flatten 3–6 mm but read the same with the normal map; IoU loss is tentacle outline jitter). The only
  fully passing step keeps 9,088 triangles. User to judge in the viewer.
- **Beholder and Robot LOD0 were cut with Blender edit-mode decimate**, like the first Bat/Dragonfly exports; the
  reduction playbook prefers the texture-aware MeshLab ladder (redone for Bat, Dragonfly and Roc in their
  `*_reduce_claude` projects). Done for the Beholder (`mm7_m166_reduce_claude`); the Robot v2 uses the ladder from the
  start.
- **Installed 2026-10-21 at the user's request** (Roc, Bat, Dragonfly, Beholder: reduced exports, `tools/install_model.py
  --world mm7`, bindings appended to `assets_dev/worlds/mm7/models/actors.yml`). The Roc ships as its own GLB
  (`mm7_m390.glb`); merging its variants into `mm8_m552.glb` is still possible later. In game (7out01 / 7d12 with
  `debug.actor_spawn_id`): all four render as 3D; Dragonfly wings translucent.
- **Engine: `scale_reference` fails for monsters whose sprite family the map has not loaded.** A debug-spawned Bat B or
  Beholder C on Emerald Island logs "actor model scale requires a valid standing sprite" and is invisible (no model,
  no sprite); the same tiers load on their own maps (Dragonfly B on 7out01, Beholder B/C on 7d12). The binding reads
  the frame scale from the current map's sprite frame table (`WorldFxSystem.cpp`). Affects every B/C binding with
  `scale_reference` when such a monster is summoned or spawned onto a foreign map.
- **Robot v2 reduction misses the numeric gates** (p99 6.1 mm vs 2.9, IoU 0.957 vs 0.98; no ladder step passes, the
  error is spread over many small plates); LOD0 5,223 picked from close-ups.
- **Robot v2 texture quality (user, 2026-10-21: "texture quality is terrible").** Two causes on our side: Smart UV at
  the default angle shattered the 305-piece hard-surface mesh into 3,340 UV islands (median about 5×5 texels at 2K),
  and the export dropped Meshy's metallic/roughness maps and forced `metallicFactor` 0 (the organic-creature rule),
  so steel and brass rendered as speckled paint. Fixed 2026-10-21: hard-surface unwrap (844 islands, 2x texel density), new retexture, Meshy metal maps kept with
  metallic capped at 0.3 (uncapped renders blue-black in game: the engine's metal reflects only a blurred sky).
  Lesson for later hard-surface models (playbook change left to the user): unwrap per piece on sharp edges, and keep
  real metal for metal materials.
- **Robot v2 installed 2026-10-21** (user accepted 5,223 triangles). In game with the real assets: Robot A on 7out01
  and A/B/C on 7d23 (The Lincoln) render as 3D with their tints; The Lincoln's own robots now draw as 3D as well.
