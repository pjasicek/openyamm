# MM9 PeasantF8, the elf townswoman (mm9_peasantf8) — 3D actor, 2026-11-01

MM9 `PEASANTF8.abc` (75 nodes, 486 triangles) with skins `PEASANTF8B` and `PEASANTF8A`. `MONSTERS.txt` rows on this model:
15 Commoner "Peasant Elf FemaleA A" (F8b), 16 Commoner "Peasant Elf FemaleA B" (F8a), 21 Prisoner "Peasant Elf FemaleD A" (F8b,
Transparent 1 = the skin's alpha; F8b has none, so opaque). DAT classes `CommonerElfFemaleA` (row 15, 19 placements) and
`CommonerElfFemaleB` (row 16, 12) in Drangheim, Drangheim City, Sturmford City, Thronheim City, Thjorgard City, Yorwick, Arslegard City,
Lindisfarne (`scripts/dat_objects.py`; 31 objects in the rebuilt maps). Row 21 has no placement.
First female townsfolk body: MM9's human female skeleton (73 joints, `FHP *`, the same as Yrsa's and the `PEASANTFEMALE` library's) and
the `peasantfemale` clip library (20 clips). Built on the approved MM9 humanoid route: MM9 skeleton and clips, never Mixamo.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantf8.glb` (`tools/install_model.py --world mm9`), identical to `export/mm9_peasantf8.glb`; variants `pf8_b`, `pf8_a` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantf8_claude`: `MM9 15 Commoner` (pf8_b), `MM9 16 Commoner` (pf8_a), `MM9 21 Prisoner` (pf8_b); scale 100, `yaw_offset` -1.570796327, stride walk 1.0 / run 1.6 (`scripts/stride.py`: walk 0.95-1.11 m, run 1.2-2.0 m), look Neck + Head |
| Descriptors | rows 15, 16, 21 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 331, 332, 331 = the elf woman stand-ins), tables regenerated: ids 9015, 9016, 9021 |
| Triangles LOD0/1/2/3 | 12,406 / 6,200 / 2,231 / 743. LOD0: head 3,204, bodice and sleeves 1,798, hands 1,470, skirt 1,398, skirt lining 1,586, scarf 948, legs 638, ears 588, cuffs 518, band 258 |
| Skeleton | 108 joints: MM9's 73 + 30 finger bones (15 per side, MPFB hands) + 5 half-joint helpers (`XhalfUpperArm`, `XhalfForearm`, `XhalfHead`) |
| Clips (30 fps, `source/mm9_lib/pfemale.glb`) | Standing `stand1`, Walking `Walk`, Running `run`, Fidget `Fidget4`, Talk `Conv2`, Conv1, Conv3, Hit `Wince1`, Death `Die1`, Dead, Cower `cower` |
| Textures | body colour 2K, normal and ORM 1K, region mask 1K (R bodice, G skirt + lining, B scarf/sleeves/cuffs); head colour 1K per tier (2), head normal and ORM 1K shared. 9 images |
| Meshy credits | **35 / 60**: Smart Topology 5, body retexture 4K 10, head retexture 4K B 10, head retexture 4K A 10 (backup account, balance 3730 -> 3635 seen before the last job), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf8_claude/review/viewer/ revision `r13-20261101`, tiers `pf8_b`, `pf8_a` |

## Clips: what MM9 plays on this body (user decision for townsfolk: only the library clips the scripts use)

The MM9 roles plus the clips the body's scripts play. NPCbase.scr (the rows' default) -> NPCBase.inc `Converse -1` (a random `conv*`) and
BaseRun.inc `LoopAnim Cower`; Retainer.scr and shopkeeper.scr add nothing; Beathag.scr loops its parameter `stand`, which the library does
not have (Standing plays `stand1`); NPC96/NPC241.scr play nothing. No wander marker near these objects names an animation.
Bound: standing, walking, run, fidget, hit, dying, dead; attack_melee and attack_ranged play Fidget (the library has no attack: peasants
flee); script clips `talk` and `conv2` Talk, `conv1`, `conv3`, `cower`, `stand` (Standing).
Left out (not played by these NPCs): `Fidget3`, `Yawn`, `Wash`, `Washfidget`, `wipe`, `wipefidget`, `Wince2`, `Die2`, `cowerstart`, `cowerend`.

**For F1 and F5 (same skeleton and library):** `scripts/pf_roles.py` writes `roles_pf.json` (the used set) and with `ALL=1`
`roles_pf_all.json` (all 20 clips, role names in the file). The retarget is a copy of MM9's local rotations onto MM9's joints at their
MM9 bind (only arms, hands, fingers, head pivot and the scarf's Ponytail chain move onto the mesh); translations: our rest plus the
source's pelvis/calf/Spine1 offset times our/MM9 leg length, every other joint on the soft line
`np.sign(off) * np.maximum(np.abs(off) - 0.004, 0.0) * k` (`scripts/clips_pf.py`). MM9's sparse keys are thinned and resampled as monotone
cubics; loops spread their seam, one-shots ease from and to Standing (0.15 / 0.2 s, Death in only), Dead = Death's last pose. The
library's root lift: the bind is centred on the pelvis, `lift_to_floor` moves the scene root so y = 0 is the floor. `work/mm9_ref_b.glb`
is MM9's own mesh with the same roles (the reference for `strips_mm9.png`).

## Route (`scripts/`)

0. **Sources**: `convert_abc_model.py --scale 0.0256` (`source/mm9/pf8a|pf8b`, `source/mm9_lib/pfemale`, raw ABC space: `L` at -x).
   `mm9_dump.py`, `mm9_regions.py` (MM9's skin texels by body region, from MM9's own triangles).
1. **HD masters** (`references_hd/`, Codex, brief `CODEX_BRIEF.md`, two runs): renders of the MM9 model with skin B (most placed row) in its
   own bind pose; `clean_alpha.py` removes Codex's halo (`*_clean.png`). Head turnarounds for both faces (`references_head/`, one run,
   face A made on face B's views).
2. **Meshy Smart Topology** 15k from `00_three_quarter_clean.png`: one clean figure, apron merged into a one-sided skirt, 1 cm human ears
   under the scarf.
3. `step1_clean.py` -> **`assemble_pf.py`**: every shell bisected at x = 0 and its +x half mirrored in numpy (Meshy's -x half had an open
   eye socket and a lip notch; `bmesh.ops.mirror` had left the seam inconsistent). Sleeve axis from sections; the sleeve beyond the
   shoulder cap is pulled to MM9's arm length (x 0.873) and turned 8.9 deg onto MM9's arm direction, so MM9's arm poses reproduce.
   Female MPFB hands (`hand_mpfb.py`, 175 mm) at MM9's wrist, the forearm stub cut 6 cm in. The human ears pressed into the skull and
   procedural elf ears (cupped leaf, rim) placed there, out, up and back through the scarf like MM9's. Legs: the +x leg and shoe on
   MM9's foot, cut below the knee. Holes filled (cuff gap, shoe soles). Symmetric collapse outside the head. Skirt lining: an inner copy
   4 mm in with a rim along the hem and the apron's lower edge.
4. **`uv_pf.py`** (never re-run: the paid paints belong to `work/uv.npz`): `uv_atlas.py`, body one 2K square at 4K paint (hands 1.5x,
   legs 0.5x, lining 0.3x), head + ears their own square (face 1.6x). `make_upload_pf.py` (true-handed uploads).
5. **Paint**: one Meshy body retexture at 4K from the four body masters; two head retextures at 4K (faces B and A) on the head upload.
   `compose_pf.py` (4K -> 2K/1K once), AO `texpass_bake_ao.py` (reach 6 cm body, 3 cm head) with **gutters padded** (`pad_ao.py`: the
   black gutters, multiplied in by the grade, drew dark lines on every UV seam), gentle grade (`finish_pf.py`), **`sym_paint.py`** (each
   head texel on the -x side takes its mirror partner's paint, so both halves of the face are one paint), `tiers_pf.py` (ramps, mask,
   darkened lining and cuff interiors, Meshy's chunky knit on scarf and sleeves softened 55 %).
6. **`tweak_pf.py`** (after the paint, UVs unchanged): midline slivers (bisect vertices 0.2-2 mm off the plane) snapped onto it (they
   shaded as a dark line down the chin), the hand stubs' zig-zag rim set on one ring, the cuff's top rim snapped onto the sleeve.
7. **`rig.sh <uv_tex2.npz>`**: `fit_rig_pf.py` -> `weights_pf.py` -> `build_glb_pf.py` -> `clips_pf.py` -> `finger_rest.py` -> `arm_out.py`
   (0 deg) -> `half_keys.py`. **`build_runtime.sh [--install]`**: prepare -> LODs -> shadow fix -> `region_variants.py` -> `tier_images.py`
   (head colour per tier) -> winding -> floor (two passes, `floor_lift.txt` then `floor_ops.txt` + ground death) -> `mirror_glb.py` ->
   winding check -> install. `viewer_update.sh <rev>`, `gates.sh`.

Rebuild from the paid inputs: `python3 scripts/finish_pf.py && ../claude_shared/gltf_venv/bin/python scripts/tiers_pf.py &&
python3 scripts/finish_pf.py && python3 scripts/tweak_pf.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz 0.010 0 &&
scripts/rig.sh work/uv_tex2.npz && scripts/build_runtime.sh --install` (project folder; heads: `sym_paint.py work/uv.npz 1
textures/pf_head_<t>_final.png textures/pf_head_<t>_sym.png +x` after their grade).

## Rig and weights

- MM9's joints stay where MM9 has them (spine, clavicles, skirt chains, legs, xpony), except the arms (on the turned sleeve axis, MM9's
  lengths), fingers (MPFB), the scarf's `Ponytail11/12` (moved onto our scarf's back), and **the head pivot**: MM9's `Head` joint sits at
  jaw height (1.49 m over the soles); with it a bow drove the chin into the bodice (Fidget, Hit). Moved to the skull base (1.535 m),
  rotations unchanged.
- Skirt and apron: analytic over MM9's eight skirt chains (`rig_bones.SKIRT_CHAINS`, XCOM_skirt prepended): azimuth between two
  neighbouring chains, height between two neighbouring links; exactly four influences, no smoothing after.
- Bodice: spine heights, clavicles at the shoulders, sleeves and cuffs by position along the arm (elbow band +/- 6 cm). The cuff's top
  ring copies the sleeve ring it meets. Head rigid above a slanted jaw-line plane, a 4 cm band to Neck, the inner neck on Spine3. Scarf on
  the head, its hanging back on Ponytail11 -> 12. Ears rigid on the head (MM9 hangs only the ear tip on `xpony`; a whole ear on it
  swung 7 cm). Hands: MPFB weights onto the finger bones. Legs: Calf, Foot, Toe0. Half-joint helpers at shoulder, elbow, neck.
  Weights mirror-symmetric.

## Tiers

The two MM9 skins differ in the bodice (B red, A brown), the skirt (B red-brown, A olive) **and the face** (B a young blonde woman, A an
older smiling woman with grey-white hair). One body paint with ramps fitted to MM9's own texels of each region and tier: R bodice
(embroidery left out by hue), G skirt (apron left out; mostly-apron charts are all apron; the lining at the bottom of the ramp), B scarf,
sleeves and cuffs (one ochre ramp from MM9's texels for both tiers: it tames Meshy's bright orange and hides fringe hair Meshy painted on
the scarf's inner flaps). **Heads**: one 1K colour per tier (the only per-tier image, 1K each), from two head retextures; bound per tier
on every LOD by `KHR_materials_variants`.

## Checks (final GLB, `review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` (48 fps) | **0 frames over 1 cm in every clip, both hands**; hand depth at most 0.2 cm (the wrist inside its own cuff); forearm 0.2 cm; finger stretch max 2.36 (Fidget R) |
| `robe_gate.py` (legs through the skirt) | **0 frames in all 11 clips** (Death and Dead after the two-pass floor fix; a tighter skirt lift had put the shins through the skirt, Death 13/45 at 7.8 cm) |
| `jitter_gate.py` against the same clips without corrections | 0 fails (no arm corrections were needed: MM9's own arms clear this body) |
| `collapse_gate.py` (30 fps, worst frame per region) | see table below |
| `detached_parts_audit.py` | 2 flagged: the two legs (shoe + shin), by design: MM9 has no thighs, the legs hang free inside the skirt (bind gap 7.9 cm), as on the Monk and the Honk female |
| `bone_length_audit.py` | 14 checked, 0 stretching |
| `flat_shading_check.py` | 0.00 body, 0.00 head |
| `check_winding.py` | 0 inverted closed parts |
| `floor_audit.py --world mm9` | 3 bindings ok: stand -0.1, walk -0.1..+1.4, living -0.8, dead 0.0 |
| `texture_quality.py` | body atlas 65.9 %, fragments 0.8 %, stretch p90 1.08, spread 3.39 (hands 1.5x, legs 0.5x, lining 0.3x by design; p50 1,655 px/m); head atlas 59.0 %, spread 1.65 (face 1.6x), stretch p90 1.13, fragments 0.0 % |
| Regression `--world mm9 --headless-run-regression-suite actors` | `mm9_actor_models_build_every_binding` PASS, 168 descriptors on 69 models (final run, siblings added theirs), 0 failed; suite 192 passed, 1 failed: `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data" (known) |
| Viewer `run_creature_review.py check` | 22 switches, 0 failed, 0 console errors |
| In game (`bootcamp.odm`, review root, isolated, spawned 9015/9016/9021) | `review/sheet_ingame.png`: both tiers bound per variant; standing, walking, running seen |

### Collapse (`scripts/collapse_gate.py`, all LOD0 primitives)

| Clip | face-frames | elbow L/R | armpit L/R | wrist L/R | waist | torso | neck | head | scarf | skirt | ankle L/R | finger | exposed at worst |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 1910 | 1/1 | 0/0 | 0/1 | 0 | 6 | 2 | 8 | 8 | 0 | 0/0 | 0 | 21 |
| Walking | 619 | 1/0 | 0/0 | 0/0 | 1 | 2 | 0 | 8 | 9 | 4 | 2/2 | 1 | 21 |
| Running | 497 | 2/3 | 1/2 | 0/0 | 4 | 0 | 0 | 6 | 9 | 4 | 0/1 | 0 | 19 |
| Fidget | 3462 | 1/2 | 0/21 | 0/3 | 14 | 2 | 33 | 21 | 12 | 2 | 2/0 | 1 | 72 |
| Talk | 2420 | 2/4 | 0/2 | 0/4 | 4 | 2 | 0 | 9 | 10 | 0 | 0/0 | 0 | 23 |
| Conv1 | 2611 | 2/4 | 11/8 | 0/2 | 4 | 5 | 4 | 9 | 11 | 0 | 0/0 | 0 | 26 |
| Conv3 | 6030 | 3/2 | 0/1 | 1/2 | 2 | 6 | 28 | 12 | 11 | 0 | 0/0 | 1 | 46 |
| Hit | 4663 | 4/1 | 4/41 | 0/2 | 36 | 8 | 35 | 24 | 12 | 8 | 2/1 | 2 | 110 |
| Death | 1939 | 1/2 | 13/10 | 0/1 | 28 | 10 | 2 | 8 | 10 | 11 | 1/1 | 1 | 40 |
| Cower | 2843 | 7/3 | 0/20 | 2/1 | 0 | 8 | 20 | 19 | 12 | 0 | 4/1 | 10 | 68 |
| Dead | 961 | 0/0 | 0/1 | 0/0 | 2 | 8 | 0 | 8 | 8 | 2 | 1/0 | 1 | 18 |

Worst: Hit armpit R 41 and waist 36 (MM9's wince bends the trunk over, an arm over the face), neck 33-35 in Fidget and Hit and 28 in Conv3
(under the chin, mostly hidden in a bow), Death waist 28. Skirt at most 11 (Death), 2 in Dead. Looked at in `review/sheet_joints_b.png` and `review/sheet_collapse3.png`:
sleeve creases and the collar under a bowed chin, no tear or flap. First rig (MM9 head pivot): neck 55 / 69.

## Sheets (viewer shots, read by me)

`review/sheet_mm9_vs_ours.png` (MM9 renders vs ours, both tiers, body front/quarter, head front, head side), `review/sheet_tiers.png`,
`review/strips_b.png`, `review/strips_a.png` (every clip, six frames, each tier) against `review/strips_mm9.png` (MM9's mesh with the same
clips, untextured silhouettes), `review/sheet_joints_b.png` (armpits in Conv1 and Hit, hem in Running, neck in Fidget, face in Cower, hands
in Standing, Dead, waist in Death, Talk), `review/sheet_collapse3.png`, `review/sheet_cuff3.png` (wrist in the cuff), `review/sheet_dead.png`
(corpse, from the feet, the fall), face close-ups `review/shots/f9b_hf.png`, `f9a_hf.png`, `r7_chinB.png`, `review/sheet_ingame.png`.

## Deviations and open points

- **Handedness:** `mirror_glb.py` last (raw ABC `L` at -x), as every MM9 humanoid; inferred from names and coordinates.
- **Proportions:** arms pulled to MM9's length (x 0.873 of Meshy's) and direction; head pivot moved up 4.4 cm (above).
- **Ears:** procedural, not Meshy's; MM9's elf ear is a flat card on the head with its tip on `xpony`. Ours are rigid on the head. From
  behind they read as a pink flap at the scarf edge; the ear's base sits partly inside the scarf.
- **Face A** is older and thinner than MM9's chubby, broadly smiling woman (same head mesh as B; the smile is paint). Face B's lips are
  Meshy's slightly pursed shape. A faint light strip remains on the nose bridge (geometry ridge on the midline).
- **Scarf**: Meshy painted a chunky knit; softened 55 %, still coarser than MM9's smooth cloth up close. Flat ochre panels (the scarf's
  inner flaps) frame the face at the temples.
- **Legs** hang free inside the skirt (2 detached parts, as MM9). The corpse lies 4 cm up on its folded hem.
- **Map placement not switched** (orchestrator's step, TOWNSFOLK_BRIEF "Lessons from wave 1"): the rebuilt maps still place 331/332
  (legacy elf women) through `transcode_mm9_dat_to_odm.py`; the descriptors 9015/9016/9021 are ready for the batch switch
  (`mm9_npc_legacy_replacements.tsv` rows 15/16/21 -> the MM9 ids, or the transcoder emitting the MM9 descriptor when one exists).
- `Transparent 1` on row 21: skin F8b has no alpha, so nothing to cut out.

## What was not checked

- Motion at normal speed by eye (judged from strips and numbers; no playback capture made).
- Tier A joint close-ups (tier B only; the meshes and clips are the same, only paint differs); LOD1-3 and shadow meshes by eye.
- In game: hit, death, cower, talk and the corpse were not seen; placed NPCs on their real maps (not switched yet).
- Wince/fidget selection by MM9's engine: one fidget and one hit per the townsfolk decision; the left-out clips are not in the GLB.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantf8_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf8_reduce_claude/before/`.
