# MM7 3D batch E: Beasts

Five MM7 creatures for one Claude session, built one after another in the order below. Four other sessions work on
batches A–E at the same time; each touches only its own projects. The full batch list is in
[README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Behemoth | `mm7_m162` | `mm7_m162_claude` | 208 Young Behemoth, 209 Behemoth, 210 Ancient Behemoth | exported |
| 2 | Griffin | `mm7_m258` | `mm7_m258_claude` | 280 Griffin, 281 Hunting Griffin, 282 Royal Griffin | exported |
| 3 | Manticore | `mm7_m278` | `mm7_m278_claude` | 295 Minicore, 296 Manticore, 297 Scorpicore | exported |
| 4 | Spider | `mm7_m402` | `mm7_m402_claude` | 400 Giant Spider, 401 Venomous Spider, 402 Widowmaker | exported |
| 5 | Rat | `mm7_m382` | `mm7_m382_claude` | 385 Giant Rat, 386 Lightning Rat, 387 Fire Rat | exported |

All projects live under `level_generation/creatures/`. The native projects hold the original frames and the
validated sprite restorations; read from them, do not change them.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## How to build each model

Run the creature-to-3d workflow (`.agents/skills/creature-to-3d/SKILL.md`, `CREATURE_TO_3D`) for each creature, one
at a time, and follow the **Claude quadruped playbook (or the humanoid playbook where noted)** fully (read it before the first model; humanoid: `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md`, quadruped: `level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md`). Also follow
`level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (five HD masters from the native bitmaps before any
Meshy job), `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set, region mask and
per-tier colour ramps from the MM7 palettes, separate 1K head set) and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_rat_claude/ (quadruped), plus level_generation/creatures/mm8_m560_claude/ (wyvern) and mm8_m552_claude/ (thunderbird) for wing bones, flap clips and air/floor rules.

Behemoth is a hunched, clawed, horned beast, not MM8's Juggernaut: do not reuse mm8_m608. Study its native walk and attack frames and choose the route the creature-to-3d skill prescribes (humanoid playbook with the mm6_gob2_claude/ non-human-body route if it walks upright with two working arms, otherwise the quadruped playbook). Griffin flies: match the native flight posture. Manticore has a scorpion tail; Spider has eight legs (give each leg its own chain and keep the feet planted). Write each anatomy decision into that model's project README.

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

- **Behemoth** (`mm7_m162_claude/README.md`, "For the user to review"): hide paler than the native sprite (follows the
  HD masters; a compose-only change if wanted); Death 1.9–2.4 s, right claws pass ≤ 14 cm through the kneeling calf
  for ~0.4 s; LOD0 kept at Smart Topology's 14,752 triangles. The batch note's "horned" does not match the native
  frames (tusks only), so no horns were modelled.
- **Griffin** (`mm7_m258_claude/README.md`): procedural flight interpretation; raised wings reach ~172 units above
  the origin (native collision height 140), so low ceilings can clip them, as with the other flyers.
- **Manticore** (`mm7_m278_claude/README.md`): the pale tier-A body reads lighter than the dark-shaded sprite in the
  viewer; ramp gain is one number in `compose_m278.py` if it needs to go darker.
- **Spider** (`mm7_m402_claude/README.md`): Meshy added a ninth leg and a stub under the abdomen; both were deleted.
  The red leg fringes keep Meshy's brighter red (not a tier region).
- **Rat** (`mm7_m382_claude/README.md`): edge stretch up to 11.8x on a small inner-hock patch of the left hind leg in
  Running (the coarse weight proxy fused the thin hind legs); not visible at game distance, a finer weight solve or a
  retopology would remove it.
- **All five:** clips are procedural (Griffin, Manticore, Spider, Rat) or retargeted Mixamo (Behemoth); none was
  checked in game (optional for this batch). Install commands and `actors.yml` bindings are in each README.
- **Tool note (no shared tool changed):** Blender's heat-weight solver fails on voxel proxies finer than ~2 cm for
  these meshes ("failed to find solution"); 2.2 cm worked for all four that use it.

## Triangle reduction (2026-10-20, after the user accepted the five models)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) (texture-aware ladder, no retexture, 0 credits),
one `mm7_mXXX_reduce_claude/` project per model. Each keeps the batch export as its rollback source
(`work/mm7_mXXX_source_pre_reduce.glb`); install the reduced export, not the batch one. **Installed 2026-10-20** (smooth exports) through
[BATCH_E_stage/](BATCH_E_stage/README.md); rows added to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

| Model | LOD0 before | LOD0 after | LODs 1/2/3 | Pick | Project |
|---|---:|---:|---|---|---|
| Behemoth | 14,752 | 11,063 | 5,461 / 2,207 / 645 | 75 %, ~240 mane shingles and other small pieces kept | `mm7_m162_reduce_claude/` |
| Griffin | 16,126 | 9,188 | 4,593 / 2,297 / 917 | 57 % per region (wings 70 %) | `mm7_m258_reduce_claude/` |
| Manticore | 16,048 | 10,588 | 5,286 / 2,585 / 933 | 66 %, 167 small pieces kept | `mm7_m278_reduce_claude/` |
| Spider | 13,808 | 6,903 | 3,446 / 1,719 / 821 | 50 % uniform + locks | `mm7_m402_reduce_claude/` |
| Rat | 14,751 | 8,613 | 4,304 / 2,117 / 813 | 58 % per region | `mm7_m382_reduce_claude/` |

Open for the user:
- **Smooth or flat shading.** The batch exports are flat-shaded (per-face normals); the reduced exports are smooth
  (about half the file size) with a flat build beside each (`REA_FLAT=1`, `*_flat.glb`); compare in each project's
  `review/glbclose/`.
- **Spider fringe cards:** in the batch export seven red fringe cards (legs R1, R2, L1, L4) are rigged to the fangs or
  the abdomen (the fang detection in `mm7_m402_claude/scripts/rig_spider.py` caught them) and stay behind in motion.
  Fixed in the reduced export only; two cards there dip 3-6 cm under the floor in Death/Dead.
- Behemoth: the Death claw-into-thigh moment is unchanged (14.6 cm); Rat: the Running inner-hock stretch is unchanged.
