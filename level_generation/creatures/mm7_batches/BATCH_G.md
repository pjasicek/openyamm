# MM7 3D batch G: Winged and floating humanoids

Five MM7 creatures for one Claude session, built one after another in the order below. Other sessions work on the
other batches at the same time; each touches only its own projects. The full batch list is in [README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Angel | `mm7_m150` | `mm7_m150_claude` | 199 Angel, 200 Angel Lord, 201 Archangel | installed 2026-10-21 (reduced body `mm7_m150_reduce_claude`, v7 props) |
| 2 | Gargoyle | `mm7_m234` | `mm7_m234_claude` | 262 Stone Gargoyle, 263 Marble Gargoyle, 264 Obsidian Gargoyle | installed 2026-10-21 (reduced, `mm7_m234_reduce_claude`) |
| 3 | Harpy | `mm7_m262` | `mm7_m262_claude` | 283 Harpy, 284 Harpy Hag, 285 Harpy Queen | installed 2026-10-21 (reduced, `mm7_m262_reduce_claude`) |
| 4 | Genie | `mm7_m238` | `mm7_m238_claude` | 265 Djinni, 266 Genie, 267 Efreet | installed 2026-10-21 (reduced, `mm7_m238_reduce_claude`) |
| 5 | Ghost | `mm7_m242` | `mm7_m242_claude` | 268 Shade, 269 Specter, 270 Ghost | installed 2026-10-21 (reduced, `mm7_m242_reduce_claude`) |

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
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_bar1_claude/, mm6_gob2_claude/, and
level_generation/creatures/mm8_m560_claude/ (wyvern) for wing bones and flap clips.

Angel, Gargoyle and Harpy have wings on top of a humanoid body: give the wings their own bone chains and motion
(fold at rest, flap in walk/attack, collapse on death), matched against the native frames. Harpy has bird legs and
wings in place of arms: decide from the native frames whether the humanoid arm gate applies and record why. Genie
and Ghost float with no legs (a smoke tail and a tattered robe): no foot planting, keep a steady hover height, and
treat the tail or robe as a soft chain. Write each anatomy decision into the project README.

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

- **Harpy (m262)**, for review (`mm7_m262_claude/README.md`): built in parallel (user override). Arm gate applies
  (human arms with hands, wings separate on the back). Bird legs on the humanoid leg chain with joints from the mesh;
  she always hovers (flight loop = standing/walking/fidget, legs authored). Death: right hand 3.4 cm into the feathered
  hip while lying. Ramps by palette-index correspondence (rank-matching per tier put grey at tier C's mid). 45 credits.
- Shared-tool notes (m262, not changed): `g6_contacts.py`/`sword_clear.py` sample a fixed 0.85 m blade (a short knife
  needs a length; project copies take `BLADE_TIP`); `foot_level.py` fails on bird feet; the copied viewer page text is
  creature-specific (see batch C note).

- **Angel (m150), for your review** (`mm7_m150_claude/README.md`): exported, 45 Meshy credits. Wings scaled to the
  native 1.2x span (the HD masters drew them 1.55x); Standing keeps the wings spread as the native sa frames do
  (not folded); Walking is an authored flight (no foot contact). LOD0 12.6k with sword (Meshy, 1.0k) and shield (0.7k).
  The Smart Topology crest is an arched loop; the raised blade passes within 1.2 cm of the coverts at the top of the
  wind-up. Not checked in game.
- **Memory (session note):** an unguarded `np.linalg.svd` (default `full_matrices=True`) on 79k image points allocated
  88 GB and exhausted the shared machine; the batch-G scripts now run in a capped `systemd-run --user --scope`
  (`mm7_m150_claude/scripts/cap.sh`) and use `full_matrices=False`. Several shared reference scripts (copied from
  mm6_natm/bar1/m406: `fit_joints.py`, `build_rig.py`, `g5_grip.py`, ...) still call the full SVD; only small inputs
  reach them today, but a shared fix would remove the trap.
- **Ghost (m242)**, for review (`mm7_m242_claude/README.md`): legless — leg bones carry no weight, steady low hover;
  robe on 24 procedural chain bones (no cloth sim); claws rigid on the hand (no finger motion); the native death's
  detached hands stay on the arms; tier A (Shade) reads near-white. No Meshy auto-rig (skeleton rule, joints from the
  bone pieces). 25 credits. The descriptors' TintColor for Ghost B/C is loaded by MonsterTable but unused by any renderer.
  Hood review fixed (2026-10-20): the hood peak was outside the hood weights (stayed on the spine: smeared sheet and the
  plate on the back), two hidden nape fins were rigid on the spine; now hood stretch max 1.9x, no fins, head bend 50 %.
- **Genie (m238):** exported, not installed (`mm7_m238_claude/README.md`; 45 credits). For review: the native cloud burst
  in the death is not modelled (she spins and shrinks into the vortex, then the lamp drops); the vortex is an opaque
  sculpted spiral, not translucent mist; the lamp corpse is its own mesh node hidden by
  `tools/model_hide_collapsed_meshes.py` while she lives. Shared-tool notes (project copies only): `fit_fingers.py` and
  `finger_weights.py` assume separate hand pieces (m406); `g6_contacts.py` needs a held prop; the copied viewer template
  still has fixed focus heights.
- **Gargoyle (m234), for your review** (`mm7_m234_claude/README.md`): the descriptors' TintColor for Marble (0xebce75)
  and Obsidian (0x586280) is not applied (the native sprites change only the membranes); the Falling Back Death kicks
  both legs up for ~0.3 s; a few torn inner-membrane faces by the armpits (Smart Topology); fidget/death hands up to
  5.8 cm into the body. Meshy's auto-rig placed the spine outside the chest (trunk joints composed from the mesh;
  5 credits spent on a rig whose joints were not used, its weights were).
- **Shared-tool note (Gargoyle, not changed):** the reference `shrink_shadow_lods.py` copies hard-code the mesh node
  name ('M406'); project copies take `MESH_NODE`.
- **Angel v2 (after the user review of v1):** bare-head body masters with a polished steel cuirass; the helmet and the
  heater shield are their own Meshy models (attachments); armhole weight rule for the shoulders; steel repaint of
  Meshy's dark metals; AO bake black faces cleaned. 120 Meshy credits (limit raised to 130 by the user). LOD0 13.8k with
  four props. v1 archived in the project (`export/v1/`).
- **Angel v3:** helmet cheek guards fitted to the face, flight sword at the hip pointing forward (native), shield strap and clearance (gate <= 1.9 cm), stray feather card re-weighted to the wing. No credits.
- **Angel v4:** helmet narrowed to hug the head (per-axis fit, ears pushed inside), helmet and shield maps sharpened (unsharp mask, normals x2). No credits.
- **Angel v5:** slumped shoulders fixed (clavicles held near rest, `clavicle_fix.py`), hit head snap halved, armour sharpened at 1K (2K would be ~4x texture memory). No credits.
- **Angel v6:** belt band of the torso shell pinned to the pelvis with the buckle and skirt (two belts sliding apart in the attack). No credits.
- **Angel v7:** skirt and tabs follow the thighs more (65/75 %) and sit >= 2 cm off them; thigh-through-skirt <= 1.4 cm while alive (5 cm in the lying death). No credits.
- **Gargoyle reduction** (`mm7_m234_reduce_claude/`): LOD0 10,812 -> 7,134 (-34 %), LODs 3,565 / 1,840 / 600, no retexture, no credits; flat feet, horns, teeth, wings and tail unchanged (gates as the source). Not installed; install command in its README.
- **Genie reduction** (`mm7_m238_reduce_claude/README.md`): LOD0 10,972 -> 7,786 (71 %, LODs 3,893 / 1,712 / 619), no retexture, no credits; face cut on its own to 85 %, fingers 72 %, lamp unchanged (corpse only); collapsed-mesh keys, bounds, edge stretch and arm contacts as the source. Not installed.
- **Harpy reduction** (`mm7_m262_reduce_claude/`, not installed, no credits): body LOD0 9,590 -> 7,312 (-24 %), LODs 3,652 / 1,603 / 918; knife unchanged (700). Feather cards, face front and bracers kept exactly; gates equal to the source; viewer has source vs reduced for all tiers.
- **Ghost reduction** (`mm7_m242_reduce_claude/README.md`): LOD0 8,168 -> 6,696 (-18 %), LODs 3,292 / 1,214 / 335; no retexture, no credits; shreds, claws and non-rigid bone pieces kept exactly (cutting them lost features); `ghost_gates.py` equal to the source. Not installed.
- **Angel reduction** (`mm7_m150_reduce_claude/README.md`, not installed, no credits): body + wings LOD0 9,916 -> 7,828 (-21 %), LODs 3,894 / 1,686 / 591; skirt, waist, shield and G6 gates equal or better than v7. Helmet (2,000), sword (1,000) and shield (900) kept: MeshLab cuts tore the helmet band and bent the shield outline.
- **Installed 2026-10-21** (user: "install to assets_source assets_dev", overriding the no-install rule above): the five reduced bodies plus the Angel sword/shield/helmet and the Harpy knife via `tools/install_model.py --world mm7` (check_winding 0 inverted on all nine); the staged bindings appended to `assets_dev/worlds/mm7/models/actors.yml` (Angel B/C expanded to full entries). Isolated runs of 7d25, t04, 7d11 and out09 load without actor-model errors. Rollback: each reduce project's `work/*_source_pre_reduce.glb`.
