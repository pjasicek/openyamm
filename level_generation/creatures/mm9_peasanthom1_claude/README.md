# MM9 half-orc townsman PeasantHOM1 (mm9_phom1) — 3D actor, 2026-11-01

MM9 `PEASANTHOM1.abc` (35 joints: the half-orc male skeleton, `Bip01 Pelvis` root, no Spine3, four helper bones on the
pelvis) with MM9's half-orc male clip library `PEASANTHOMALE.abc` (11 clips; same rest pose as the body, checked joint by
joint). No other project had retargeted this skeleton (the Dook militia half-orc is a monster rig on `fighterbase.abc`).
`MONSTERS.txt` rows naming `PeasantHOM1.ABC`: **57 Commoner** "Peasant Half-Orc Male A" (skin PeasantHOM1a: chestnut bowl
hair, dark plum vest over a cream linen shirt, red-brown trousers; DAT class `CommonerHalfOrcMaleA`, 16 objects in the
rebuilt maps' raw objects: Guberland City 10, Arslegard City 2, Sturmford City 2, Guberland 2), **58 Town** "Male B" (skin
PeasantHOM1b: blond-grey hair, older moustached face, green/ochre patterned jacket with brown wool sleeves, charcoal
trousers; no DAT placement found) and **60 Prisoner** "Male D" (skin PeasantHOM1a; no DAT placement found). Row 59 uses
PeasantHOM2 (not this body). Townsfolk batch `devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`, on the approved MM9
humanoid route (MM9 skeleton and clips, never Mixamo; grafted five-finger hands; separate head set) with PeasantM1d's,
Annud's and the Honk male's v2 scripts. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_phom1.glb` (`tools/install_model.py --world mm9`), identical to `v2/export/mm9_phom1.glb`, sha256 `0692f374972b17f5...` (sideburn outline fix 2026-11-02; before it `3ec43eb07b106d8b...` (wrist fix), rollback `work/installed_preear.glb`; first install `927bd9f2...` in `work/rollback_v1/`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `scripts/binding.yml` (`scripts/bind_under_lock.sh` under the flock): `MM9 57 Commoner` and `MM9 60 Prisoner` skin `phom1_a`, `MM9 58 Town` skin `phom1_b`; scale 100, `yaw_offset -1.570796327`, stride 1.7 / 4.0 (`scripts/stride.py`: walk 1.66-1.95, run 3.8-4.4 model units; the half-orc is 2.27 units tall in MM9's own scale, 27 % taller than the human peasants), look Neck/Head, melee impact 0.5 s (hattack1 `Rattack`) |
| Descriptors | rows 57, 58, 60 added to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 439 / 442 / 447, the stand-ins the maps use), tables regenerated: 9057 / 9058 / 9060 |
| Triangles LOD0/1/2/3 | 7,853 / 3,924 / 1,411 / 471 (Smart Topology 15,040; head 3,028 kept at 0.75 incl. horns and ears, hands 2 x 700 MPFB) |
| Clips (30 fps, `source/mm9_lib/phomale.glb`) | Standing `stand`, Walking `walk`, Running `run`, Fidget `Fidget1`, Talk `conv1` (NPCBASE.inc `Converse`), AttackMelee `hattack1`, Hit `wince1`, Death `die1`, Dead; script clips Cower `cower` (NPCbase via BaseRun.inc `LoopAnim Cower`; ArmWrestle.scr), CowerStart `cowerstart`, CowerStop `cowerstop` (ArmWrestle.scr). Retainer.scr plays none. All 11 library clips are used |
| Textures | body 2K colour + 1K normal + 1K ORM + 1K region mask (4 regions); head + hands set 2K colour + 1K normal + 1K ORM + 1K mask (2 regions); one set for all tiers |
| Meshy credits | **25** (Smart Topology 5, 4K body retexture 10, 4K head retexture 10; backup account, 3585 before the first job, 3430 at the end, other agents spending too), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthom1_claude/review/viewer/ revision `v16-20261102`, tiers `phom1_a`, `phom1_b` |

## Sideburn outline (2026-11-02, ear sweep) - current

Ear sweep (`claude_shared/mm9_overview/ear_sweep_20261102.png`, rows 11-12): an outline drawn round the hair patch on each cheek,
dark on phom1_a, lighter on phom1_b. MM9's PeasantHOM1 has that patch (the hair bowl comes down in front of each ear to the jaw:
`references_hd/mm9_head_views_{a,b}.png`, and the Codex head turnaround), so the sideburn stays and only the outline goes.
**Cause**: not the Meshy paint (`v2/work/phom1_head_basecolor_composed.png` has a soft sideburn edge) but `hairline_fix.py`: it
darkens every hair-mask texel within 8 texels of the hair border to 1.1 x the hair median; at the fringe that removed the pale
strand tips, round the sideburns, temples and nape it darkened the soft hair/skin border into a line. **Fix**
(`scripts/fix_sideburn_phom1.py`, 0 credits): `colour` (after `hand_clean.py`, before `tier_ramps_phom1.py`; reads
`v2/textures/phom1_head_basecolor_preear.png`): head texels outside the fringe window (front y < -0.075, |x| < 0.10, faded over
2 cm) take the composed paint back, i.e. hairline_fix acts on the fringe only (64,010 texels; hands and fringe untouched).
`mask` (after `tier_ramps_phom1.py`; reads `v2/textures/phom1_head_region_mask_preear.png`): row 58 then still showed a brown
frame round each blond sideburn (the border's chestnut texels outside the hair mask or under its brightness fade keep tier A's
colour); in the sideburn box (z < 1.0, -0.09 < y < 0.04, |x| > 0.06, brows and ears out) texels within 6 texels of the hair
mask take a hair weight from their luminance (0 at the cheek's, 1 from 35 % of the way to the hair's), blurred 0.7 texel, max
with the old weight (5,369 texels). Tried: a gentler weight (full at 80 %, blur 1.5) brought a faint brown rim back. The tier
script was not re-run (the ramps and the rest of the mask stay as installed; note that `hairline_fix.py` -> `hand_clean.py` on
the current mask does not reproduce the installed colour: the mask was refitted after the last hairline run). Only
`phom1_head_basecolor` and `phom1_head_region_mask` changed (`glb_diff.py` vs the previous install: 0.000 mm in every clip, every
other image the same). Left: row 58's lower sideburn is a flat pale blond (Meshy's soft gradient there maps to the capped top of
the blond ramp) and ends in a soft step to the skin, no line. Sheet `review/sheet_ear_before_after.png` (both tiers, before v15 /
after v16: ear-side close-ups, both profiles, both 3/4 backs, both under-jaw views, party view from 22 deg, front). Viewer
v16-20261102 check 24 switches, 0 failed.
Regression after the last ear-sweep install (2026-11-02, `review/regression_actors_earsweep.log`): `--world mm9 actors` passed 192,
failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data");
`mm9_actor_models_build_every_binding` **PASS**.

## Wrist and sleeve fix (2026-11-02, orchestrator follow-up after the PeasantM7 review "hands sticking through the sleeves")

Asked: remove the salmon skin flare at the cuffs and the two dark triangles on the sleeve; route and scripts from
`../mm9_peasantm7_claude/` (README, "Wrist and hand fix"). Meshy: 0 credits. Rollback of the first install: `work/rollback_v1/`
(source and export GLB, viewer GLBs, master `fix_v1.blend`, body/head colour, masks, ramps).

- **Cuff rim** (geometry): `scripts/cuff_fix.py` (on `v2/work/head_uv.blend`, fourth argument TRIM 0.025) now also deletes the
  outer 2.5 cm of each cuff's crumpled rim and every inward-facing (turned-in lining) old face from 5 cm before the cuff,
  then relaxes the new open rim along itself (8 passes) -> `v2/work/fix_v1.blend`.
- **Stub inside the sleeve**: `scripts/sleeve_tuck.py` (M7's, frac 0.75, gap 3 mm) -> `v2/work/fix_v2.blend`: 21 vertices per
  hand moved in up to 23 mm, 34 / 33 stub vertices take the sleeve weights.
- **The "dark triangles" were holes**: Meshy's Smart Topology left four see-through holes in the forearm sleeves (boundary
  loops of 4, 5, 18 and 19 edges, about 15 cm before the cuffs). `scripts/sleeve_holes.py` -> `v2/work/fix_v3.blend` (the
  master) fills them with cloth faces that continue the surrounding UVs (a flat texel across a UV seam).
- **Skin paint on the cuff cloth**: `scripts/sleeve_paint_fix.py v2/export/mm9_phom1.glb` (M7's, from
  `textures/phom1_basecolor_graded_collar.png`): skin-coloured texels within 12 cm of a hand (r/g > 1.28, saturation > 0.35:
  the cream linen is r/g ~1.17) and the pale peach on the cuff lining within 8 cm (r/g > 1.22, saturation > 0.25; 211/145/104)
  take the nearest cloth texel (4,067 texels) -> `textures/phom1_basecolor_graded.png`; mask `review/sleeve_paint_fix_mask.png`.
- **Hands** were blotchy with dark nails too (the same per-channel grade as M7): `scripts/hand_clean.py` (run from `v2/`,
  after `hairline_fix.py`): one clean face-skin colour 167/104/73 times the bake's luminance detail.
- New gate `scripts/sleeve_poke_gate.py`: before (first install) 0 mm in every clip (it measures skin outside the sleeve
  tube; the flare was the cuff's own rim cloth and paint, which the gate does not see); after: 0 frames over the 0.5 mm
  tolerance in all 12 clips, both arms; worst Death L 0.2 mm (sub-tolerance; 4.2 mm, 17 frames with the 1.5 cm trim, the
  bent hand's back against the cuff side). `v2/review/gates_v2/sleeve_poke.txt`.

Sheets read: `review/sheet_wrist_before_after_L.png`, `review/sheet_wrist_before_after_R.png` (same cameras, first install
left, fixed right: bind, Talk 200, Fidget 70, AttackMelee 20, Death 30; side, other side, front, back, below),
`review/wrist_parts_{L,R}_before.png` and `_after.png` (hand material red), `review/sleeve_marks_before_after.png` (the
sleeve holes front, then the fixed sleeves front and back), `review/cuff_fix.png` (clay cuffs), `v2/review/death_L.png`,
`v2/review/death_L_parts.png`.

Gates after (`v2/review/gates_v2/`): arm and hand 0 frames over 1 cm in all 12 clips (Fidget L 0.8 cm, unchanged); jitter
0 fails; floor all three OK; winding 0; bones 0 stretching; detached 0; flat 0.00; body atlas 60.1 %, spread 1.07,
fragments 0.5 %; head set 46.8 %, spread 3.09, fragments 2.9 %; viewer 24 switches, 0 errors. Installed sha256
`3ec43eb07b106d8b...`; LOD0 7,853 triangles (the trimmed rim and the hole patches cancel out), LOD1-3 3,926 / 1,412 / 470. Full `actors --world mm9` suite on this install
(`v2/review/gates_v2/regression_actors_full.txt`): 192 pass, 1 known fail (out05); `mm9_actor_models_build_every_binding` PASS
(181 descriptors on 74 models).

Left: the cream inner lining of the cuff shows inside the opening in some poses (cloth colour, not skin).

## Route (all from this project; commands in the scripts' headers)

0. **Sources** (`convert_abc_model.py`, both skins, `--scale 0.0256`; library `PEASANTHOMALE.abc`). **HD masters** from
   renders of the MM9 model with skin A (`scripts/ref_renders.py` -> `references_hd/mm9_views_a.png`,
   `mm9_head_views_a.png`, `mm9_skin_x4_a.png`), Codex (`scripts/codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`),
   1536x1024; Codex's alpha halo removed into `references_hd/clean/` (`scripts/clean_alpha.py`), which the retexture uses.
   Head turnaround `v2/references_head/` (`scripts/codex_head.sh`, mouth closed with the tusk tips, clean hairline asked
   for), halo-free copies in `v2/references_head/clean/`.
1. Smart Topology 15k from `00_three_quarter.png`; `scripts/fit_rig.py` with `scripts/fit_config.json` (centre chain
   Pelvis..Head; **Spine and Spine2 by `centre_interp`**: the 3 cm torso band read the pot belly's front and pushed them
   23 / 19 cm forward; X-ray `review/xray_v1_sheet.png`) -> `work/fit_v1.blend`; `scripts/reduce_uv.py` ->
   `work/uv_v1.blend`; `scripts/prelabel.py` (`prelabel.json`: the head shell is its own part from z 0.70; two loose shirt
   lace strips floating in front of the chest deleted) -> `work/label_v1.blend`.
2. Body UVs `v2/scripts/texpass_uv.py` -> `work/uv_tp.blend`, upload `texturing/phom1_body_upload.glb`; 4K retexture
   `requests/retexture_body.json`; `bake_ao_texpass.py`, `compose_texpass.py`, gentle `grade_basecolor.py` ->
   `textures/phom1_basecolor_graded_pre.png`; `scripts/collar_fix.py` (the collar's top rim was painted skin pink: rust
   leather with its own brightness detail) -> `textures/phom1_basecolor_graded.png`.
3. Hands `v2/scripts/graft_hands.py` (`graft_phom1.json`: stocky MPFB macro, one hand scale 1.72, cuff percentile 97 for the
   noisy class map, `poke` 0.03; **new opt-in `old_hand_attr`**: every face prelabel.py marked as old hand goes too, as
   old fingertip and thumb shards stayed beside the graft) -> `v2/work/hands_v1.blend`; `head_split.py`
   (`head_phom1.json`) -> `head_v1.blend`; head UVs `texpass_head_uv.py` -> `v2/work/head_uv.blend`, upload
   `v2/texturing/phom1_head_upload.glb`; 4K head retexture `v2/requests/retexture_head.json`; `bake_hands.py`
   (middle-aged caucasian male skin), `compose_headhand.py --ref-head --hand-gain 1.3` (the reference median included hair
   and came out dark) -> `v2/work/phom1_head_basecolor_composed.png`; `scripts/hairline_fix.py` (below) ->
   `v2/textures/phom1_head_basecolor.png`.
4. **Clean-up** (2026-11-02 chain: `cuff_fix.py ... 0.025` -> `sleeve_tuck.py 0.75 0.003` -> `sleeve_holes.py` -> master `v2/work/fix_v3.blend`, see the wrist section) `scripts/cuff_fix.py` on `v2/work/head_uv.blend` -> `v2/work/fix_v1.blend`: the turned-in
   cuff lining and rim faces past each cuff deleted, then sliver tips (cream and salmon flaps round both wrists in the
   Fidget close-ups). The graft was not re-run (the head UV layout is paid for).
5. **Tiers** `scripts/tier_ramps_phom1.py` (texel positions `scripts/make_texels.py` from `v2/scripts/uv_xyz.py` dumps;
   MM9 skin pairs `scripts/mm9_skin_samples.py`): body R vest (above the vest hem, found per 10-degree sector from the
   rust border), G sleeves (by position along each arm to the embroidered cuff band; by colour they were blotchy), B
   trousers, A vest border; head R hair (closed and hole-filled so the dark strands are included, brows out, eroded one
   texel against hair only, brightness fade within 5 texels of its edge, blond ramp capped at stop 6), G collar. Tier A
   ramps fitted to our own paint; tier B quantile-matched to the PeasantHOM1b texels paired with PeasantHOM1a texels of the
   same region (sleeve pairs without the hands; vest gain 1). Report `textures/phom1_ramps.json`.
6. **Runtime** `TOKEN=<lease> scripts/rebuild.sh <viewer revision> [--install]` -> `v2/scripts/build_runtime_v2.sh`:
   export, `clips_mm9.py` (`v2/scripts/roles_phom1.json`, `soft_offsets`, root `Bip01 Pelvis`), `arm_clear.py` on Fidget
   only (`arm_clear_phom1.txt`) re-applied smoothly by **new `v2/scripts/smooth_correction.py`**
   (`smooth_correction_phom1.txt`: hold 0.15 s, Gaussian 0.08 s), prepare, LODs, shadow LODs, `region_variants.py`, floor
   pass (`scripts/floor_ops.txt`: walk offsets `--smooth-loop Walking 0.06 --smooth-hold 0.25`, death 0.08 s), `mirror_glb.py`,
   `fix_winding.py`, winding check; viewer GLBs `viewer_tiers.py`, manifest `make_viewer_tiers.py`.
   **Never re-run `texpass_uv.py`, `texpass_head_uv.py` or the graft**: the paid paints belong to `work/uv_tp.blend` and
   `v2/work/head_uv.blend`.

Texture chain when the paint changes: `grade_basecolor.py` -> `collar_fix.py` -> `compose_headhand.py` ->
`hairline_fix.py` -> `hand_clean.py` (from v2/) -> `fix_sideburn_phom1.py colour` -> `tier_ramps_phom1.py` ->
`fix_sideburn_phom1.py mask` -> `rebuild.sh` (delete the `*_preear.png` backups after a new compose / tier run) (hairline_fix reads the current head mask, so run the tier
script once before it on a fresh compose).

Shared-script copies changed in this project only: `v2/scripts/glb_frames.py` and `head_closeups.py` write their tiles
next to the output (the snap Blender's private `/tmp` hid them; `head_closeups.py` also gained `face`, `faceq`, `faceL`,
`fringe*` views for this big horned head); `build_runtime_v2.sh` reads optional `arm_clear_<prefix>.txt` and
`smooth_correction_<prefix>.txt`; `graft_hands.py` has the opt-in `old_hand_attr`.

## Checks (final GLB, 2026-11-01)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps, `v2/review/gates/arm_final.txt`) | hands 0 frames over 1 cm in all 12 clips; worst Fidget L 0.8 cm (the scratching hand at the other sleeve); forearms <= 2.1 cm (Fidget, cloth on cloth); 19 chains per hand; finger stretch p99 <= 1.71, max 3.47 (Fidget R, single knuckle-web edge at the closed curl; read in `review/close_hands.png`). Raw MM9 Fidget before the fix: L hand 6.0 cm, 67 frames |
| Jitter (`jitter_gate.py` vs MM9's untouched clips, `jitter_final.txt`) | 0 fails. Before: Fidget (arm_clear per key: upper arm 1.5 deg/f, shoulder skin 11.5 mm/f2 over MM9), Walking and Death (per-key floor offsets: shoulder skin 10 and 31 mm/f2) |
| Floor (`floor_audit.py --world mm9`) | all three OK: stand 0, walk -1.6..+1.5, living -1.6, dead 0 (a 0.08 s walk smoothing had lifted every foot 4.0 units) |
| Winding | 0 inverted closed parts |
| Bones (`bone_length_audit.py`) | 12 checked, 0 stretching |
| Detached (`detached_parts_audit.py`) | 0 detached (15 components); root-lift notes only (head shell 2.4 cm off Spine2 at Hit 57: no gap visible in `v2/review/neck_hit.png`) |
| Flat shading | 0.00 on both materials |
| `texture_quality.py` body | atlas 60.2 %, density p10/p50/p90 1313/1364/1406, spread 1.07, fragments 0.1 %, stretch p90 1.11 |
| `texture_quality.py` head + hands | atlas 46.8 % (66.9 % on the head upload; the hands' squares), spread 3.11 (head 4201 vs hands ~1400 texels/size: by design), fragments 3.1 %, stretch p90 1.34 |
| Tier A ramp fit (8-bit mean / p95) | vest 2.2 / 6.4, sleeves 2.5 / 7.9, trousers 2.3 / 7.0, border 3.9 / 12.4, hair 1.5 / 4.5, collar 2.5 / 7.4 |
| Viewer `run_creature_review.py check` | 24 switches, 0 failed, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | PASS, 181 descriptors on 74 models, 0 failed (`v2/review/gates/regression_binding.txt`) |
| Full `actors` suite (`--world mm9`, on the install before the walk-floor and cuff changes) | 192 pass, 1 known fail (`out05_event_clearance_completes_from_monster_killed_hook - could not load gameplay data`), `v2/review/gates/regression_actors_full.txt` |

Sheets (viewer shots and EEVEE renders, read): `review/sheet_ear_before_after.png` (2026-11-02), `review/sheet_mm9_vs_ours.png`, `review/sheet_tiers.png`,
`review/sheet_face.png` (shoulders/collar framing: the viewer's head focus aims below this tall head),
`review/face_closeup.png` (both tiers, bind and Talk: face, three-quarter, profile, fringe edge front/three-quarter/side),
`review/strips_1.png`, `review/strips_2.png` (every clip at four times, tier A), `review/close_hands.png`,
`v2/review/fidget_frames.png`, `v2/review/neck_hit.png`, `review/hands_clay.png`, `review/cuff_fix.png`.

## Deviations and open points

- **Row 58 is a colour tier, not its own face.** MM9's PeasantHOM1b face is an older man with a moustache and no visible
  tusks; ours keeps the young tusked face of skin A with blond-grey hair. A per-tier face would need a second head
  retexture (10 credits) and per-tier head images (the creature texture rules say no per-tier base colours). The jacket is
  a flat olive-brown from the luminance-matched ramp (MM9: green with an ochre pattern and a blue/red key border).
- **Fringe edge, row 58:** the pale jagged band of wave 1 was there at first (blond ramp on the fringe's light strand
  tips and the transition texels). Fixed by the head paint (`hairline_fix.py`) and the hair mask (above); at the fringe
  close-up (16 cm frame) a faint lighter rim stays at row 58's hairline, not visible at the face framing. Row 57's fringe
  edge is clean.
- Wrists and the sleeve marks: fixed 2026-11-02 (section above).
- Small marks: a 17 cm rust band at the vest's back hem
  (Meshy painted the back hem as border; it takes the border ramp in row 58).
- Hands: MM9's mitten curl drives the five MPFB fingers (`finger_alias`, Annud's values). Hand skin graded to the face.
- `attack_ranged` maps to AttackMelee (the engine requires the key; civilians).
- Ears: Meshy and the masters made them point up and out (MM9: flat, straight out sideways).

## Binding plan for the map placements (not done: shared import code)

As in `../mm9_peasantm1d_claude/README.md`: the rebuilt maps place these NPCs with the legacy stand-ins 439 / 442 / 447
from `tools/mm9_import_discovery/mm9_npc_legacy_replacements.tsv` through `transcode_mm9_dat_to_odm.py`
(`build_mm9_npc_actor_lines`); nothing places 9057 / 9058 / 9060 yet. The orchestrator's one switch for every townsfolk
row in `mm9_npc_actor_rows.tsv` (then `regenerate_mm9_maps.sh` and the review root) shows them in game.

## Not checked

Normal-speed playback was not watched (motion judged from strips, frame renders and the jitter gate); no in-game run;
LOD1-3 and shadow meshes not looked at; foot sliding against the 1.7 / 4.0 strides; tier B clips (Standing shots only:
same clips and mesh); the cower clips' intent (MM9's half-orc "cower" holds both arms out forward, kept as authored).

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasanthom_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasanthom_reduce_claude/before/`.
