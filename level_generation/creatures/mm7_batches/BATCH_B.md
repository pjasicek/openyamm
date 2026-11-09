# MM7 3D batch B: Robed casters

Five MM7 creatures for one Claude session, built one after another in the order below. Four other sessions work on
batches A–E at the same time; each touches only its own projects. The full batch list is in
[README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Cleric of the Moon | `mm7_m170` | `mm7_m170_claude` | 214 Acolyte of the Moon, 215 Cleric of the Moon, 216 Priest of the Moon | installed |
| 2 | Cleric of the Sun | `mm7_m174` | `mm7_m174_claude` | 217 Acolyte of the Sun, 218 Cleric of the Sun, 219 Priest of the Sun | installed |
| 3 | Mage | `mm7_m274` | `mm7_m274_claude` | 292 Sorcerer, 293 Wizard, 294 Archmage | installed |
| 4 | Warlock | `mm7_m426` | `mm7_m426_claude` | 418 Fire Warlock, 419 Water Warlock, 420 Air Warlock | installed |
| 5 | Monk | `mm7_m290` | `mm7_m290_claude` | 304 Monk, 305 Initiate, 306 Master | installed |

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
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_bar1_claude/, mm6_pfem_claude/ (cloth skirt) and mm6_gob2_claude/ (skirt strips).

All five wear long robes: solve the robe or skirt deformation once (mm6_pfem_claude/ cloth skirt, mm6_gob2_claude/ skirt strips) and carry the solution through the batch. Staffs, wands and other held items are separate attachment GLBs. Spell casts need hand sockets (see mm6_gob_claude/ spell sockets).

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

## Accepted and staged (2026-10-20)

Accepted by the user after two review rounds (facing, fidget twist, feet on the floor, Monk sleeves and head, Mage
staff flick, Warlock gown/death/cast/hair/skin; details in each project README) and the triangle reduction
(`mm7_m*_reduce_claude/`). Staged in [BATCH_B_stage/](BATCH_B_stage/README.md) and installed the same day with its
`install.sh` (user request): 7 GLBs in `assets_source/worlds/mm7/models/` with runtime copies in `assets_dev`, 15
bindings appended to `assets_dev/worlds/mm7/models/actors.yml`. Checks:
- the installed sources are byte-identical to the stage;
- 0 inverted closed parts in all seven GLBs;
- an isolated MM7 run on 7out01.odm loads with no errors;
- the actors regression suite has no MM7 cases, and it crashes at `actor_crowding_*` with `--world mm6` too
  (pre-existing).

Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

## Open issues

Batch result (2026-10-20): all five exported, none installed; 155 Meshy credits in total (30 + 30 + 35 + 30 + 30).
Every project README lists the install command, its `export/actors_binding.yml`, gates and known limits. No in-game
check was run (optional for this batch).

For the user's decision:
- **Deaths**: the Warlock, Monk and Moon Cleric use the humanoid set's Relax Lay Down (kneel, lie down) where the
  native falls backwards: the Mixamo backward falls kick the legs up, and the legs Smart Topology modelled under the
  gowns came out of the robes. The Sun Cleric (legs removed) and the Mage keep a closer match.
- **Hands**: all five have rigid hands (open claws, open hands or fists around a prop); no finger motion.
- **Monk**: the folded arms show the hands in front of the sleeves (the native hides them).
- **LOD0** is 8.8–11.9k triangles (Warlock 11.9k: Meshy fused body, gown, cape and hair into one shell).

Playbook / shared-tool notes (not applied, per the batch rules):
- Smart Topology `pose_mode: "a-pose"` re-poses the hands and opened the Mage's staff fist; an empty `pose_mode` kept
  the fist from the HD master (Mage, Warlock, Monk). Worth a line in the humanoid playbook for prop-holding fists.
- Robed casters: Meshy weights long bell sleeves to the pelvis and the torso below the armpit to the arms; the
  connectivity split below the armpit (`weights_robe.py` in each project) fixed the arm stretch every time. The robe
  chain rig of `mm8_m460_claude` needs leg capsules sized by whether real legs exist under the robe.
- `build_rig.py`'s thumb-side guess (the wider side of the hand) flipped the Mage's hands 150°+; forcing the thumb
  forward for an A-pose fixed it.
