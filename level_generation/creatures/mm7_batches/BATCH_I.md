# MM7 3D batch I: Large and unusual bodies

Five MM7 creatures for one Claude session, built one after another in the order below. Other sessions work on the
other batches at the same time; each touches only its own projects. The full batch list is in [README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Hydra | `mm7_m266` | `mm7_m266_claude` | 286 Fire Hydra, 287 Air Hydra, 288 Chaos Hydra | installed (reduced) |
| 2 | Medusa | `mm7_m282` | `mm7_m282_claude` | 298 Medusa, 299 Queen Medusa, 300 Empress Medusa | installed (reduced) |
| 3 | Ooze | `mm7_m298` | `mm7_m298_claude` | 310 Emerald Ooze, 311 Sapphire Ooze, 312 Bloodstone Ooze | installed (reduced) |
| 4 | Treant | `mm7_m479` | `mm7_m479_claude` | 451, 452, 453 Tree | installed (reduced) |
| 5 | Golem | `mm7_m254` | `mm7_m254_claude` | 277 Bronze Golem, 278 Brass Golem, 279 Gold Golem | installed (reduced) |

All projects live under `level_generation/creatures/`. The native projects hold the original frames and the
validated sprite restorations; read from them, do not change them.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## How to build each model

Run the creature-to-3d workflow (`.agents/skills/creature-to-3d/SKILL.md`, `CREATURE_TO_3D`) for each creature, one
at a time, and follow the **Claude quadruped playbook for non-humanoids, humanoid playbook for Golem** fully (read
it before the first model; humanoid: `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md`, quadruped:
`level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md`). Also follow
`level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (five HD masters from the native bitmaps before any
Meshy job), `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set, region mask and
per-tier colour ramps from the MM7 palettes, separate 1K head set) and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_rat_claude/ (non-humanoid route) and
mm6_gob2_claude/ (rig-first, for Golem).

Hydra has several heads and necks on one body: give each neck its own chain and keep the heads from intersecting.
Medusa has a human upper body on a snake tail: humanoid arms with the arm gate, a spline chain for the tail that
stays on the floor. Ooze is a blob: a minimal rig or shape-driven squash and stretch is enough. Treant has only 33
native frames (mostly a standing tree): keep it light, with sway and a few branch chains, and do not invent clips
the native set lacks. Golem is a rigid, heavy humanoid: use the humanoid playbook with stiff, heavy motion. Write
each anatomy decision into the project README.

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

Batch built in parallel (user override, 2026-10-20: the lead built the Hydra, one agent each the other four). Nothing is
installed; each README has the install command(s) and the `actors.yml` binding.

- **Hydra** (`mm7_m266_claude/README.md`): 100 of 100 credits (five separate head models + a second body retexture
  after neck 1 had been deleted by the graft's crumb rule). LOD0 17.9k triangles (five heads 12.3k), over the 15k
  ceiling like the accepted MM6 hydra. Attack frame 13: a horn tip of head 4 grazes head 5 (6 triangle pairs); a hind
  paw dips 3.9 cm under the floor mid-Death. Backs of the heads show rounded napes where the lofts meet the crests.
  Tiers lighter than the dark sprites (`RAMP_GAIN`).
- **Medusa** (`mm7_m282_claude/README.md`): 25 credits. Body plus bow and arrow attachments. Meshy fused the inner
  upper arms to the ribs: raised arms pull a web of side skin (a clean fix needs a mesh split and a new unwrap); string
  hand up to 3.1 cm into the jaw at full draw; release flick very fast for one frame; corpse torso floats ~6 cm in
  places; LOD0 16.5k. Face projected from the Codex head turnaround (Meshy's head retexture painted scales on it).
- **Ooze** (`mm7_m298_claude/README.md`): 15 credits. Opaque glossy blob with a pseudopod and death globules.
  `m299a/m300a/m301a` have no contact frame in `engine/rendering/sprite_attack_timing.yml`, so the blow lands at the end
  of the 1.25 s animation (suggest `contact_frame: 5`, a runtime table, not changed). Lumpier than the sprite's fine
  ridges; slightly light in the viewer.
- **Treant** (`mm7_m479_claude/README.md`): 25 credits (second retexture after a 13 %-coverage unwrap blurred the bark).
  Only the native clips (Standing serves walk/fidget). All tiers share palette 530: one material, no ramps. Attack lash
  goes forward rather than sideways as in the natives; death has no particle effect; in game the tree is 1,155 units
  tall against a collision height of 199; UV island padding 4 texels at 2K (8 cost too much coverage).
- **Golem** (`mm7_m254_claude/README.md`): 30 credits. Skinned humanoid (Meshy returned one closed metal skin), authored
  double-fist smash over a library chop (blow 0.967 s; MM7 has no contact frame for its attack sprite either). Attack:
  fists clasp 2.1 cm into each other overhead, left upper arm 2.9 cm against the neck, left thumb web 4.35x; gold reads
  bronze in the specular-less viewer (`GOLD_GAIN`).
- **Shared-tool notes** (none changed): `arm_torso_probe.py` and `g6_skirt_poke.py` count open shells (collars,
  loincloths) as "inside"; `merge_head_material.py` needs equal body/head map sizes; `run_creature_blender.sh` holds the
  project lock for the whole run, so Meshy polls of the same project fail during long bakes.
- **Installed 2026-10-20** at the user's request: the five reduced exports (`mm7_*_reduce_claude/export/`, Medusa with
  its bow and arrow) through `tools/install_model.py --world mm7`, and 15 bindings appended to
  `assets_dev/worlds/mm7/models/actors.yml` (all clips, skins, sockets, look nodes and attachments checked against the
  GLBs). In-game check on Emerald Island (`7out01.odm`, `debug.actor_models=true`): all 15 descriptors spawn as 3D
  models with their tier colours and no actor-model errors.
- **`scale_reference` fails for monsters a map does not spawn natively:** the binding looks up both standing sprites in
  the current map's sprite frames, so console-spawned (or map-absent) tiers fail with "actor model scale requires a
  valid standing sprite" and fall back to sprites. Batch I uses explicit per-tier scales instead (Hydra B 234.6, C
  255.9). The batch E entries Behemoth B/C and Manticore B/C still use `scale_reference` (seen failing for Manticore B
  in the same check); an engine fix (the descriptor's sprite scale from the global table) or explicit scales would
  cover them.
