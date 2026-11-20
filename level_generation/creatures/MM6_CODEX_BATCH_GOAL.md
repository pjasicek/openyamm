# MM6 Codex batch: 15 humanoid families

Goal: 15 more MM6 monster families as rigged, animated, tiered 3D actors, produced by Codex sessions
(`gpt-6-astra`, reasoning `xhigh`) that each own one creature end to end, with Claude only orchestrating: launching
waves, checking hand-offs, serialized integration (actors.yml, regression, game captures) and relaying user reviews.

Status: **complete 2026-10-13 - all 15 families accepted by the user and installed** (approved 2026-10-12) (budget 100 credits per creature, Codex full access, waves of 5, picks as listed).
Wave 1 launched 2026-10-12. Wave 2 launched 2026-10-12 while wave 1 review rounds ran (101 GB free). Wave 3 launched 2026-10-12 after wave 2 hand-offs.

## Selection

Installed already (29 families): barbarian, bat, beholder, goblin, hydra, bloodsucker, ooze, rat, robot, spider,
thief, titan, cleric, cobra, cockatrice, demon, demon fly, druidess, fighter (leather), guard, necromancer, nobleman,
ogre, peasants F1/M1/M2, sea serpent, skeleton, werewolf.

All 15 picks are two-armed humanoids. This is the mature route: Claude humanoid playbook, source-frame rig, numeric
gates, local animation library. Map counts are MM6 maps whose spawn table lists the family (`map_stats.txt`).

| # | Wave | Family (descriptors) | Sprite | Maps | Kind | Closest reference project |
|---|---|---|---|---|---|---|
| 1 | 1 | FighterChain | `figc` | 4 | chain-mail swordsman | `mm6_bar1_claude` (sword, upright clips), `mm6_fgt_claude` |
| 2 | 1 | Sorcerer | `sor1` | 4 | robed caster | `mm6_dru1_claude` (caster, cloth), `mm6_cle_claude` |
| 3 | 1 | BLich | `lch` | 4 | undead robed caster | `mm6_dru1_claude`, `mm6_ske_claude` |
| 4 | 1 | BMonk | `mnk1` | 3 | unarmed fighter | `mm6_dru1_claude` (unarmed set), `mm6_bar1_claude` |
| 5 | 1 | KnightPlate | `kni` | 2 | plate armour, weapon | `mm6_bar1_claude`, `mm6_gua_claude` |
| 6 | 2 | BMinotaur | `min1` | 3 | monster humanoid, axe | `mm6_gob2_claude` (non-human body), `mm6_ogr_claude` |
| 7 | 2 | BArcher | `arc1` | 2 | bow (ranged) | `mm6_bar1_claude` + a bow prop |
| 8 | 2 | BDwarf | `dwa1` | 2 | short body, axe | `mm6_gob2_claude`, `mm6_bar1_claude` |
| 9 | 2 | LizardArch | `lzd` | 2 | lizard man, bow, tail | `mm6_gob2_claude`, archer from wave 2 |
| 10 | 2 | Jackalman | `jak1` | 1 | beast head, weapon | `mm6_wfigt1_claude` (werewolf) |
| 11 | 3 | PeasantM3 | `mep` | 2 | town NPC | `mm6_pman_claude` (cheapest run) |
| 12 | 3 | PeasantF3 | `mfp` | 2 | town NPC | `mm6_pfem_claude` |
| 13 | 3 | PeasantM4 | `natm` | 2 | town NPC | `mm6_pman_claude` |
| 14 | 3 | PeasantF4 | `natf` | 2 | town NPC | `mm6_pfem_claude` |
| 15 | 3 | Merchant | `mer1` | 0 (houses/NPC) | town NPC | `mm6_nobl_codex`, `mm6_pman_claude` |

Left for later (route not proven, or better with Claude-led R&D): dragons (`drag`, `drg1`, `drr1`; dragoncover is in
4 maps), the four elementals (fire/air are mostly effects), ghost `gst`, genie `djn`, harpy `hrp`, gargoyle `gar`,
medusa `med` (snake body), dragonfly, demon queen `qfi`, cactus `mcac`, reactor `rea`, PeasantF2 `fmp`.

## Per-creature Codex prompt (template)

```
$creature-to-3d FULL - MM6 <FAMILY> (sprite <code>) - budget <N> credits
Project: level_generation/creatures/mm6_<code>_codex/ . Batch rules: level_generation/creatures/MM6_CODEX_BATCH_GOAL.md
("Batch rules"). Closest reference projects: <from the table>.
```

## Batch rules (every Codex session)

1. **Ownership:** claim `mm6:<code>` with `tools/creature_workspace.py` (owner `codex-batch-<code>`), work only in the
   own project directory, release the lease at hand-off. Never touch another creature's directory.
2. **Playbooks:** read the Claude humanoid playbook fully, including the 2026-10-11 magyar lessons:
   - **Upright clips:** the set's one-handed clips are a low guard, so choose upright clips and render them from the
     side.
   - **Mixamo:** use `retarget_mixamo.py` (rest-delta copy, forearm roll moved to the hand).
   - **Attacks and taunts:** stance plant plus about 20 % of the leg motion, as discrete IK steps.
   - **Blow time:** fastest tip motion while the blade points at the target.
   - **Actual blade motion:** check what the weapon does, not the clip's name.

   Read HD master references and creature textures too.
3. **Shared files are read-only during production:** `assets_dev/worlds/mm6/models/actors.yml`, anything under
   `game/`, `engine/`, `tools/`, the playbooks and AGENTS/CLAUDE files. Instead, write to the project:
   - `integration/actors.yml`: the exact descriptor blocks for its tiers;
   - `integration/regression.md`: the proposed test case (name, map, summoned ids, size bounds);
   - `integration/playbook_notes.md`: lessons for the playbook.
4. **No game launches** (no `openyamm`, `run_game.sh`, `capture_gameplay.sh`, regression suite) and no CMake builds:
   integration does these one creature at a time.
5. **Machine share:** Blender in background only, with `--threads 4`; one Blender process at a time per session
   (five sessions share about 30 GB of free memory). No headless Chrome left running after `check_viewer.mjs`.
6. **Meshy:** through `tools/run_creature_meshy.sh` with the project budget (100 credits); check `anim_library` before paying for
   any animation.
7. **Weapons, shields and metal (user review, 2026-10-12):** held weapons and shields carry the creature's impact, so
   give them real attention: a modelled silhouette (bevelled blade or axe bit, socket, wrapped grip, shield rim, boss
   and emblem matched to the native frames) and a detailed, non-flat texture, with triangles spent on the silhouette
   rather than hidden faces. Steel reads dull grey like the sprites, not bright white, on every tier.
   Weapons are never "a few slabs and solid colours" (user, KnightPlate review). Route: a standalone HD design of each
   weapon/shield from the native frames with Codex image generation (flat light, side + three-quarter view, saved
   under `references_hd/`), then Meshy image-to-3D / Smart Topology + retexture or a careful hand model from it,
   reduced to roughly 1-3k triangles with a detailed texture (wear, edge highlight, wrap). Show the design image and
   a close-up render of each prop in `review/`.
   Props are animated with the body (user, Sorcerer review): Hit and Fidget move the held weapon/staff and both arms,
   with knees and hem reacting; a staff Cast swings the staff head toward the target with a step of the legs; the
   free arm hangs relaxed beside the body in Standing (no flared elbow).
8. **Done criteria** (hand-off; technical completion, not artistic acceptance):
   - **Elbow gate (Sorcerer review):** on every clip at 48 Hz, both elbows flex only forward in the arm's anatomical
     plane (no hyperextension beyond 5 degrees, forearm roll within limits); re-posed arms are where it breaks.
   - **Rest pose (Archer review):** Standing and Fidget match the native standing frame (upright, relaxed arms,
     weapon held loosely), not a combat-ready idle; soles flat on the floor (heel and toe within 1 cm) in both.
   - **Locomotion (Dwarf review):** Walking swing feet clear the floor visibly (peak lift ~8-12 cm at human size,
     knee ~40-60 degrees at mid-swing; no shuffle); Running has a real flight phase but no floating:
     each foot planted (no slide) during its own stance (~30-40 % of the cycle), with double-float phases (both
     feet up) and flight height as in the source run clip (do not flatten it to a fixed cap), and
     the pelvis stays high (min >= ~92 % of the Standing pelvis height; corrected 2026-10-13 after the Magyar's
     crouched run - forcing high contact drops the hips). Report pelvis height %, contact and flight per clip.
   - **Library clips first (Jackalman review):** Attack, Cast and Death come from anim_library (Mixamo or the humanoid
     set), retargeted and planted; hand-authored/procedural action clips lack sway and momentum. Weapon attacks use
     the matching grip (two-handed staff/polearm swings for staff wielders). Procedural only to fill a gap, said so.
   - **Hands:** palm direction gate on every clip (free hand palm toward the thigh at rest; weapon hand closed around
     the grip from the correct side); no candy-wrapper upper-arm twist.
   - **Skin tone:** skin ramps match native skin luminance numerically (mean and highlight percentiles), not darker.
   - **Cloth penetration (Monk review):** hands exit sleeves only through the openings; legs/feet never poke through
     robes or skirts above the hem. Signed-distance gate per clip at 48 Hz, worst penetration reported in mm.
   - **Triangle minimisation (user, 2026-10-12; method revised after the KnightPlate round got only -13 %):** the 15k
     Meshy return is a ceiling, not a target. Reduce geometry for the silhouette only (planar dissolve + collapse with
     protected groups: face, hands/fingers, deformation loops at shoulders/elbows/knees/hips, silhouette edges, prop
     contact), then REBAKE the textures from the unreduced mesh onto the reduced one (base colour, region mask, ORM,
     and a tangent-space normal map that keeps the lost surface detail; the engine loads glTF normal textures) instead
     of carrying distorted UVs. Judge at the largest in-game size (actor height about 700 px, melee range at 1080p)
     with the actual tier materials: silhouette IoU >= 0.99 from 8 views, and textured SSIM >= 0.95 or a perceptual
     difference you would not notice side by side; every rig gate (G4-G6, elbow, palms, contact, cloth penetration)
     still passes on all clips. Stop at the last step that passes. Expect roughly 5-8k for clothed humanoids, 3-5k for
     simple rigid bodies; props 1-3k. LOD1-3 are fitted at their switch sizes (550/220/88 px; pooled IoU >= 0.97), not fixed
     50 % ratios, and the chain must strictly decrease (about LOD1 <= 55 %, LOD2 <= 25 %, LOD3 <= 10 % of LOD0) and
     never exceed the previously installed counts.
     Report the reduction curve (triangles vs. IoU/SSIM/gates) and side-by-side renders in `review/` and HANDOFF.md.
   - **Two-handed grips (Minotaur review):** the weapon follows the dominant hand; the off hand is solved onto the
     haft with a fixed grip frame; wrist/forearm roll stays anatomical with no flips between samples (roll spread over
     twist bones); palm-to-grip distance <= 3 mm for both hands. Heavy swings show wind-up (step, torso turn, weapon
     back), release with weight transfer, follow-through.
   - **Gait:** feet point within ~10 degrees of the travel direction (no toe-out splay); free arm swings beside the
     body, palm toward the thigh; carried bows hang vertically, string toward the body.
   - **Smoothness:** no frame-to-frame jitter or snaps: angular-acceleration gate on upper arms, forearms and wrists
     for every clip (IK pole flips are the usual cause).
   - **Texture sets (Sorcerer streaks):** one shared texture set for all LODs; rebakes keep the accepted resolution
     and texel density, pack islands with >= 16 px dilated margins; no per-LOD map sets.
   - **Running clip (user, Merchant review):** never use `RelaxRunForward`; pick a normal running/jog clip with arm swing.
   - **Closed body (Minotaur/Merchant reviews):** no open holes in the body under clothing or at sleeves (count open
     boundary edges below the belt and at shoulders; only intended ones); never delete "hidden" faces that show
     between kilt strips, sleeve gaps or in motion.
   - **Head in action clips (user, male Cannibal review):** the target is straight ahead (runtime look adds the turn
     to the party), so the face stays pointed forward at the victim through Attack/Cast: torso coils in the wind-up while
     the head counter-rotates to stay on target; head steady and level at the release, tilts only with the spine
     (<= ~15 deg); no sideways/down glances. Neck length constant (no translation/scale keys on neck/head). Casting
     hand ends palm-forward. Gate: head forward within ~20 deg of character forward from wind-up to recovery.
   - **Head and hands in reduction (Merchant review):** protect head and hand geometry from the body reduction and
     give them their own texture sets (1K head set, small hand set); never re-project the face through a body rebake.
   - **Running clip (user, 2026-10-13):** a real run, not a jog: default `anim_library/mixamo/Standard Run.fbx` (the
     accepted female Cannibal's run); Jogging was rejected for every creature.
   - **Costume bones in library clips (male Cannibal review):** retargeted clips must not drive cloth/feather/
     costume bones from a different rest; frame 0 of every clip matches the Standing costume within ~1 cm.
   - **Silhouette:** male robes and armour keep the shoulders as the widest upper point (no pear/hip bulge).
   - **Rig gates:** G4/G5/G6 pass on every clip; blade-edge and blow-time gates pass for weapons; posture check
     (pelvis height, trunk lean) for every clip.
   - **Exports:** runtime GLB with LODs and 3 tiers in `export/`; review viewer passes `check_viewer.mjs`.
   - **Bindings:** `animation.cast` is required by the engine even without spells (alias `Attack`); a descriptor
     whose `monster_data.txt` row has a spell needs a distinct Cast clip (not the attack clips), or the registry fails.
   - **Skin weights:** every skinned primitive of the final runtime GLB (all LODs and shadows) has weight sums
     within 1e-4 of one, and no material uses an extension the loader rejects (`KHR_materials_specular`, `_ior`,
     clearcoat, sheen, transmission...; Blender writes specular when Specular IOR Level/Tint/IOR leave their
     defaults), colour-region extras are absent or a mask plus 1-4 ramps of 16 colours, and every *_Shadow
     mesh uses an OPAQUE material.
     `python3 output/codex_batch/check_bindings.py integration/actors.yml` (bindings + all referenced GLBs) must print
     no BAD line: it mirrors the engine's actors.yml rules (cast clip, distinct cast for spellcasters, clip/socket
     names, impacts inside clips) and `check_weights.py`. One bad model
     disables the whole MM6 actor registry (dwarf weights, lizard/gargoyle specular, 2026-10-12).
   - **Sheets:** clip sheets (front, side, three-quarter) in `review/`.
   - **Records:** `README.md` and `creature_3d_progress.json` updated; `HANDOFF.md` lists the files, gate numbers,
     open faults and the integration snippets.

## Orchestration (Claude)

- **Waves:** 5 sessions at a time.
  - **Launch:** `output/codex_batch/launch.sh <code> "<family>" "<references>"` runs
    `codex exec -m gpt-6-astra -c model_reasoning_effort=xhigh --dangerously-bypass-approvals-and-sandbox -C <repo>`
    in the background, logging to `output/codex_batch/<code>.log` (session id in the log header) and the final message
    to `output/codex_batch/<code>.last.md`.
- **Monitoring:** cheap only. Process alive, `creature_3d_progress.json` stage, `HANDOFF.md` present. No reading of
  full logs unless a session stops early.
- **Hand-off check:** gate numbers present, `check_bindings.py` on the staged actors.yml (no BAD line) before merging, one look at the clip sheets
  and prop close-ups.
- **Integration (one creature at a time, Claude or one integrator Codex session):**
  1. Merge `integration/actors.yml` and the regression case.
  2. Build `openyamm` and run the MM6 actor suite.
  3. Install the GLB.
  4. Run an in-game tour capture against the sprites.
- **User review:** one viewer link per creature. Feedback goes back to the owning session with
  `codex exec resume <session id> "<feedback>"`, then re-integration.
- Next wave starts when the previous wave is integrated (lessons from wave 1 go into the prompt of wave 2).

## Speed-up (user, 2026-10-12)

Measured: ~70-80 % of a two-hour round is model time (each session writing and debugging its own gate and reduction
scripts at `xhigh`); Blender is ~20-35 %, renders ~5 %. The user approved:
- **A. Shared gate runner:** one tested script, `level_generation/creatures/claude_shared/gates/run_gates.py`, runs every
  batch gate on the runtime GLB in one Blender pass. Bone gates run at 48 Hz; mesh gates run at 24 Hz and are refined
  near thresholds. It writes `gates.json` and `gates.md`. Built and validated 2026-10-12 (see its README and
  VALIDATION.md); sessions call it instead of writing their own gate code.
- **B. Reasoning level:** review/fix rounds (`resume.sh`) run at `high`, first production stays at `xhigh`.

## Cost controls (user, 2026-10-12, after ~2 Pro-200 sessions of usage for 5 accepted families)

1. No new launches until the 14 running sessions finish; nothing running is stopped (finishing keeps the spent work).
2. At most 4 Codex sessions at once from now on.
3. Triangle reduction: ONE rebake pass per creature to a fixed target (body ~7k, each prop ~1.5k; LOD1/2/3 about
   55/25/10 %), accepted if the eight-view side-by-side shows no visible change. No trial searches or curves.
4. No retroactive rules: new rules apply only to sessions that have not started.
5. At most two review rounds per creature; after that the orchestrator brings it to the user before spending more.
6. The shared gate runner is ready (2026-10-12; 12 tests, matches handoff numbers, ~1-7 min per creature) and is
   mandatory for every round: keep a `gates.json` config beside the project (start from
   `claude_shared/gates/example.gates.json`), run
   `level_generation/creatures/claude_shared/gates/run_gates.sh export/<name>.glb --config gates.json --out review/gates`
   and put its `gates.md` verdict in HANDOFF.md. Do not write per-creature gate code; report runner bugs instead.

## Decisions (user, 2026-10-12)

- **Meshy budget per creature:** 100 credits (1500 maximum for the batch).
- **Codex sandbox:** full access (`--dangerously-bypass-approvals-and-sandbox`) for the background sessions.
- **Wave size:** 5.
- **Selection:** as listed.

## Wave log

| Wave | Creature | Launched | Session id | Hand-off | Integrated | User review |
|---|---|---|---|---|---|---|
| 1 | `figc` | 2026-10-12 | `01a12e87-48d9-7c70-a336-282109a98b1c` | yes (30 credits) | 2026-10-12: 3 GLBs, actors.yml, regression case, oute3 capture | accepted 2026-10-12; rebake reduction installed (body 11,511 to 6,797; axe 2,440 to 2,122; shield 1,476 to 1,328); round 4 installed: axe 2,122 to 796, body textures 16 to 4 images (18.7 to 11.7 MB); round 6 installed 2026-10-13 (steel OK); running removed by user - run binds to Walking (2026-10-13) |
| 1 | `sor1` | 2026-10-12 | `01a12e87-4cee-7fe3-ae78-8d2039d066eb` | yes (40 credits) | 2026-10-12: 2 GLBs, actors.yml, regression case, oute3 capture | accepted 2026-10-12 (round 3); round 4 texture fix installed (44 to 7 images, 19.3 to 10.0 MB, no mip streaks) |
| 1 | `lch` | 2026-10-12 | `01a12e87-50fa-7bc1-a7ec-5eef18931235` | yes (30 credits) | 2026-10-12: GLB, actors.yml, regression case, oute3 capture | accepted 2026-10-12; rebake reduction installed (16,274/8,135/2,907/897 to 6,290/3,466/2,907/897) |
| 1 | `mnk1` | 2026-10-12 | `01a12e87-5590-7713-93a2-c9a8b1eee961` | yes (20 credits) | 2026-10-12: GLB, actors.yml, regression case, oute3 capture | accepted 2026-10-12 (round 3); round 4 rebake reduction installed (12,427/6,212/2,235/744 to 7,047/3,804/1,690/701) |
| 1 | `kni` | 2026-10-12 | `01a12e87-596e-7080-bbf8-a91c9f194282` | yes (20 credits) | 2026-10-12: 2 GLBs, actors.yml, regression case, oute3 capture | accepted 2026-10-12; rebake reduction installed (body 12,815/6,467/2,314/754 to 8,403/5,172/2,110/697; sword 2,292 to 1,985) |
| 2 | `min1` | 2026-10-12 | `01a12f07-6eb7-7723-89b6-375795bf7a00` | yes (30 credits) | 2026-10-12: 2 GLBs, actors.yml (attack_ranged Attack, axe_head socket dropped), regression case | accepted 2026-10-12 (round 3) |
| 2 | `arc1` | 2026-10-12 | `01a12f07-83e8-7ca3-8993-82140ffc89b6` | yes (40 credits) | 2026-10-12: 3 GLBs (body, bow, arrow), actors.yml, regression case, oute3 capture | accepted 2026-10-13 (round 6) |
| 2 | `dwa1` | 2026-10-12 | `01a12f07-8995-7351-a1c3-f833cbe2bf25` | yes (40 credits) | 2026-10-12: weights fixed (round 1), 2 GLBs, actors.yml (cast: Attack alias added), regression case, oute3 capture | accepted 2026-10-12 (round 3 look and motion); round 4 reduction installed (body 11,563, axe 2,119); round 5 stopped by user (looping), lease released; round 8 upright Standard Run installed 2026-10-13 (pelvis min 92.5 %, walk stride 0.89, new run_stride_length 0.706); accepted 2026-10-13 |
| 2 | `lzd` | 2026-10-12 | `01a12f07-8fa2-71a3-a510-659547844119` | yes (60 credits) | 2026-10-12: round 2 (distinct Cast), 2 GLBs, actors.yml, regression case | accepted 2026-10-13 (round 6) |
| 2 | `jak1` | 2026-10-12 | `01a12f07-9485-7d32-aae7-39ebb003d7ed` | yes (40 credits) | 2026-10-12: round 1 fixes (staff extras removed, attack_ranged Attack), 2 GLBs, actors.yml, regression case, oute3 capture | accepted 2026-10-12 (final: round 3 skin, dark +30% lift); staff reduced 2,018 to 866 (installed 2026-10-13) |
| 3 | `mep` | 2026-10-12 | `01a12fc3-2017-70e2-af49-edb129bc0221` | yes (40 credits) | 2026-10-12: 2 GLBs, actors.yml, regression case (LOD chain 10,066/4,494/3,594/3,494, above target) | accepted 2026-10-13 (round 2); death 2x timing installed |
| 3 | `mfp` | 2026-10-12 | `01a12fc3-2595-7c10-877e-7df93042fc6f` | yes (55 credits) | 2026-10-12: 2 GLBs, actors.yml, regression case (LOD 10,180/5,511/2,277/1,234) | accepted 2026-10-13 (round 2); death timing installed (2.98 to 2.14 s) |
| 3 | `natm` | 2026-10-12 | `01a12fc3-2bde-7521-89db-e373a4bffa40` | yes (50 credits) | round 1 fix (opaque shadows, shared textures, feather floor contact) installed 2026-10-12 | accepted 2026-10-13 (round 4); attack timing installed (hold removed, arms recover together, jerk smoothed; 2.25 to 1.15 s); final, accepted 2026-10-13; body maps halved 4096 to 2048 by the orchestrator |
| 3 | `natf` | 2026-10-12 | `01a12fc3-318d-77c3-852c-58799b31f856` | yes (30 credits, modest costume adaptation) | 2026-10-12: 3 GLBs, actors.yml, regression case (LOD chain 11,641/4,699/3,077/2,707, above target) | accepted 2026-10-12 (round 3); slim skirt OK; round 5 installed (attack arm/shoulder fixed, wind-up and recovery 30 % faster): pending user check |
| 3 | `mer1` | 2026-10-12 | `01a12fc3-366b-7fc3-8b55-df451ab1fc1e` | yes (30 credits; self-reported QA hold: 302 shared-gate FAIL rows - wrist, grip, cloth) | 2026-10-12: 2 GLBs, actors.yml, regression case | accepted 2026-10-13 (round 3; hands noted as odd, left as is; run swap cancelled - merchants do not run) |

Outside the batch: the Magyar (`mm6_bar1_claude`) running clip (RelaxRunForward) is being replaced by a fresh Codex
session (`output/codex_batch/bar1_runswap.log`); Jogging rejected; Standard Run with raised pelvis installed 2026-10-13 (pelvis min 92.1 %, stride 1.6 m, stride_length 1.032); accepted by the user 2026-10-13.

## Texture minimisation (2026-10-14)

The texture reductions found in the MM6 inventory (far-LOD caps, prop caps, flat maps, lossless roughness halving,
mostly empty colour maps, creature cap 2048) are cook decisions in `tools/cook/model_textures.yml` (`reductions`),
applied by `tools/cook_models.py` from the untouched sources in `assets_source`; see ASSET_COOKING_PLAN.md section 13.
