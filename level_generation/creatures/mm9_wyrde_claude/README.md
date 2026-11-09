# MM9 Wyrdes Morgan and Verdandi (mm9_wyrde) — 3D actor, 2026-11-02

MM9 `WYRD_YOUNG.abc` and `WYRD_MATURE.abc` are the same mesh (`meshcmp.py wyrd_young:wyrd_mature`: head, torso, arms and legs p90 and max
0.0 cm; 558 faces, MM9's human female skeleton, 73 joints, bind identical to PeasantF1's). One new body on the approved MM9 humanoid route,
two tiers. `wyrd_old.abc` (row 263, Igrid) is a different mesh and not part of this project.

| Item | Value |
|---|---|
| Rows (MONSTERS.txt) | 265 Wyrde of the Unknown (Morgan), `wyrd_young.ABC`, skin `wyrdyoung` -> tier `wy_young`; 264 Wyrde of the Knowing (Verdandi), `wyrd_mature.ABC`, skin `wyrdmature` -> tier `wy_mature`. No other row names these models |
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_wyrde.glb` (`tools/install_model.py --world mm9`), identical to `export/mm9_wyrde.glb` (sha256 f56f8f2407e6..., r16) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_wyrde_claude` (`scripts/bind_actors_wy.py`, under the flock): `MM9 264 Wyrde of the Knowing (Verdandi)` (wy_mature), `MM9 265 Wyrde of the Unknown (Morgan)` (wy_young); scale 100, `yaw_offset` -1.570796327, stride walk 0.95 / run 1.13 (`scripts/stride.py`: walk 0.92-0.97 m, run 0.99-1.27 m), look Neck + Head |
| Descriptors | rows 264, 265 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 380, 384 = the stand-ins of `mm9_npc_legacy_replacements.tsv`), tables regenerated: ids 9264, 9265 |
| Triangles LOD0/1/2/3 | 14,932 / 7,460 / 2,670 / 879 (LOD0: shell split into head set 5,032, gown + sleeves 2,600, mantle 1,700; underskirt 1,028, legs 600, hands 1,470, jewellery 899; linings 1,336 twin + 270 rim faces; 70 hidden underskirt faces removed) |
| Skeleton | 108 joints: MM9's 73 + 30 finger bones (MPFB hands) + 5 half-joint helpers |
| Clips (30 fps) | Standing `stand1`, Walking `Walk`, Running `run`, Fidget `Fidget4`, Hit `Wince1`, Death `Die1`, Dead, Cower `cower` |
| Textures | body colour 2K, normal and ORM 1K, region mask 1K (R mantle, G gown, B Verdandi's damask, A Verdandi's cord); head set (face, hair, circlet, hood) colour 1K per tier (2), head normal and ORM 1K shared |
| Meshy credits | **35 / 60**: Smart Topology 5, body retexture 4K 10, head retextures 4K Morgan 10 and Verdandi 10 (backup account 3085 -> 3060 seen before the last job), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_wyrde_claude/review/viewer/ revision `r16-20261102`, tiers `wy_young`, `wy_mature` (r4 in `review/viewer_before/`) |

## Clips (what the scripts play)

Both rows run `basemelee.scr` (MONSTERS.txt) and the PeasantFemale clip library. DAT objects: Hall of the Gods `WyrdeoftheKnowing0` (class
WyrdeoftheKnowing, row 264) and `WyrdeoftheKnown1` (class WyrdeoftheUnknown, row 265), no ScriptName; `WG_NPC334.scr` only toggles their
visibility, solidity and gravity in the win cutscene; no script plays a clip on them (darkpassageway's `WyrdeoftheUnknown0` is class
WyrdeoftheKnown = Igrid, row 263, `NPC338.scr`, voice and quest only). The ABC's own clips (`wyrdsyoung`, `wyrds_mature`, `statue`) hold the
bind pose. So only MM9's roles are carried (`scripts/roles_wy.json`); the library has no attack: attacks play Fidget. The `Wyrd1stat`,
`Wyrd2stat`, `Wyrd3stat` props in the Hall of the Gods are statues (PropAnim `statue`, the `*sculpt` skins, scale 9), not actors: not in scope.

## Route (`scripts/`, from PF1 `mm9_peasantf1_claude` and PF8 `mm9_peasantf8_claude`)

0. **Sources**: `convert_abc_model.py --scale 0.0256` for both models (`source/mm9/`), the PeasantFemale library copied from PF1
   (`source/mm9_lib`). Reference renders of MM9's model with both skins (`ref_renders.py`) -> `references_hd/mm9_*_{y,m}.png`.
1. **HD masters** (`references_hd/`, brief `CODEX_BRIEF.md`, `codex_masters.sh` 1 and 2 through `codex_slot.sh`): Morgan's clothes,
   1536x1024, `clean_alpha.py`; sheet `review/masters_vs_mm9.png`. Head turnarounds for both women (`references_head/`, `codex_heads.sh`).
2. **Smart Topology** 15k from `00_three_quarter_clean.png`: one fused shell (head, hair, hood, cowl, mantle, gown, sleeves with closed
   cuff caps) + underskirt, legs, hands, eyes, pendant, belt stone, panel ornaments, 21 choker beads.
3. **`seg_wy.py`** (seeds `seg_seeds.json`): the shell split by multi-seed Dijkstra with a crease cost into head, hair, hood, mantle, gown.
   **`assemble_wy.py`**: mirrored at the midline (X0 0.008, +x half), a straight hood/cowl cut behind the face at 1.465 m (bisected, so the
   head-set/body seam is a line in the fold), face labels by vertex majority; head set = face, hair, circlet, hood; Meshy's lumpy eyeballs
   replaced by fitted spheres, socket rims relaxed (2.5 mm cap), the small human ears pressed in (membrane over face-skin vertices only);
   sleeves turned and scaled onto MM9's arm, MPFB female hands (172 mm) with a 6 cm forearm stub through the closed cuff caps (no hollow
   cuff); legs on MM9's feet cut below the knee; reduction outside the head with part borders held.
4. **`uv_wy.py`** (never re-run: the paid paints belong to `work/uv.npz`): body one 2K square (hands 1.4x, legs 0.5x), head set its own
   (face 1.7x).
5. **Paint**: `compose_wy.py`, AO `texpass_bake_ao.py` + `pad_ao.py`, `finish_wy.py` (gentle grade); heads `sym_paint.py`,
   **`head_tiers_wy.py`** (hood quantile-matched to MM9's mantle texels per tier; Morgan's dark under-hood hair to her blonde),
   **`face_fix_wy.py`** (below); **`tiers_wy.py`** (below).
6. **After the paint, UVs unchanged**: `tweak_wy.py` (mantle back midline relaxed: the mirror V and a deep fold shaded a line down the
   back), **`linings_wy.py`** (below), `trim_hidden_wy.py` (underskirt faces hidden inside the gown above -0.30 m).
7. `rig_wy.sh` (`fit_rig_wy.py`: MM9's joints, arms on the sleeve axis, head pivot at the skull base; `weights_wy.py`: PF1's analytic
   weights, the mantle on spine/clavicles above the waist and the skirt chains below like MM9 hangs it, smoothing only above the waist (it
   spread the chains past four influences and drew a seam down the back in Walking), head rigid above a jaw-line plane at 1.495 m, face,
   lips, chin and jaw on Head; `clips_pf.py` with the soft offset line) -> `build_runtime_wy.sh [--install]` -> `viewer_update.sh <rev>`.

### Tiers (`tiers_wy.py`, `head_tiers_wy.py`)
MM9's skins are one design: Morgan a plum gown and plain royal-blue mantle, Verdandi a brown gown with a braided cord down the front panel and
a moss-green damask mantle; gold trims, spirals, jewellery, underskirt, hands and shoes are shared. One body paint (Morgan's clothes):
R mantle (every mantle texel except gold, plus blue texels Meshy put on the gown at the neckline), G gown (plum texels), B damask (MM9's own
mature mantle pattern from its skin's back strip, mapped by arc length round the body and height at MM9's 9 x 5 mm per texel; Morgan's B
ramp = her R), A cord (a braid at |x| < 1.2 cm from the belt to 0.80 m; Morgan's A = her G). Ramps by luminance quantiles onto MM9's
projected texels (`project_mm9_skin.py`) per tier. Hands one clean skin (212,148,108). Cuff caps a dark lining colour. Faces: one 1K head
colour per tier from each woman's own head retexture; the hood part of each is quantile-matched to MM9's mantle texels of that tier, so it
meets the ramped mantle at the cut. Not carried: Verdandi's spirals are dark plum in MM9, ours stay gold on both.

### Face fixes (`face_fix_wy.py`, per tier; face pre-screen against MM9)
Nose underside (irregular dark smudge) -> nose-side skin with two soft nostrils at the geometry's recesses; throat between the hood's sides
-> neck skin (Verdandi had a green wedge and a red band there); a white pearl drop painted on the forehead where the mesh has none -> skin;
eyelids painted on the rigid eyeball spheres (upper from 0.42 r above the centre for Morgan, 0.30 r for Verdandi, lower from -0.62 / -0.42 r,
lash line): the Meshy eyes stared; chart gutters re-padded (thin grey seam lines across the cheeks).

### Linings (`visible_backfaces.py`, `posed_backfaces.py`, `linings_wy.py`)
Cloth is one-sided. Faces whose back side is the first hit of a view ray (8 azimuths x 0/+-20/50 deg at rest; 8 x 0/20 deg on the export
posed at Death 0.6-1.8 s, Dead, Hit, Fidget, Cower) are duplicated 2 mm behind themselves, flipped (same UVs and weights), one ring of
neighbours at rest (two on the head, none on the hand stubs), with rim strips at open edges. Mainly the inner sides of the hair strands
beside the jaw, the cowl's inner edge, the gown's lower hem.

## Review pass r5-r9 (orchestrator, 2026-11-02; 0 Meshy credits)
Review of r4 (`sheet_faces_vs_mm9`, `sheet_r4_face`, `sheet_r3_body`). Rollback: `work/rollback_r4/` (GLB, both head colours, body tone,
mask, ramps); r4 viewer in `review/viewer_before/`.
1. **Forehead pearl** (Verdandi): a painted pearl drop under the tiara where the mesh has none; the r4 shots were taken before the second
   pass of `face_fix_wy.py` (threshold sat < 0.34, z 0.708-0.732, filled from the forehead just below); checked in the head colour (gone),
   the head normal (flat there), the body texture (the forehead is not in it) and the ramps (the head has none).
2. **Noses**: the underside zone now reaches the tip (Morgan's dark dot), plain nose-side skin with two light small nostrils at the
   geometry's recesses, no inherited detail; head normal map flat over nose and lips (`flatten_head_normal.py`); the nose underside and
   philtrum top geometry relaxed (`tweak_wy.py`, at most 2 mm: the remaining dark notch from below was shading).
3. **Eyes**: geometry (`tweak_wy.py`): the lid skin rotated about each eye's horizontal axis like a closing lid, upper 9 deg down, lower
   5 deg up, fading out by 9 mm and toward the corners, 0.6 mm outside the ball (184 vertices); paint lids on the eyeballs per tier
   (Morgan from 0.40 r / -0.62 r, Verdandi's squint from 0.24 r / -0.30 r).
4. **Morgan's scalp** under the tiara (a flat tan cap left by the r2 recolour): her front strands' blonde with strands combed back over
   the side and top hair zone (forehead and circlet band protected) and the flat tan wherever it remained.
5. **Lips**: one closed shape (an ellipse round the mouth, 2.4 x 0.8 cm half axes) in one colour per tier, Morgan soft rose (192,92,88),
   Verdandi natural (178,98,86), a mild luminance variation and a thin line at the slit; the old lipstick's edge outside it recoloured too.
6. **Verdandi's mantle back** (a mirrored Rorschach blotch): the damask strip made seamless and repeated by wrap with a brick offset per
   column at 6.5 x 4 mm per skin texel, no mirror at the back centre.
7. **Profiles**: true profile and a low 3/4 from below the chin for both women, against MM9's profile: chins and jaws read as MM9's, no
   receding chin or under-chin slab; no geometry change there.
Sheet (read): `review/sheet_faces_before_after_r5.png` (rows: Morgan r4, Morgan r9, Verdandi r4, Verdandi r9; MM9's front and profile
on the left; front, 3/4, true profile, low 3/4, from below, back).

## Mouth pass r10-r14 (orchestrator, 2026-11-02; 0 Meshy credits)
Review of r9: both lips a swollen pursed pout (Verdandi a mauve two-tone pucker), a dark V under the noses from below. Rollback:
`work/rollback_r9/` (GLB, head colours and normal, `tweak_wy.py`, `face_fix_wy.py`).
- **Geometry checked**: the lips are not proud of the face (upper lip and philtrum on one line at y -0.12; the lower lip ~1 cm before the
  chin) and the mouth is one connected piece (no loose lip shells). The pout was paint: Meshy's lips 1.9 cm tall. Meshy modelled the mouth
  slightly open: relaxing the mouth area (r11) pulled the cavity forward and opened it, so that was dropped.
- **Paint** (`face_fix_wy.py`): the old lip area becomes skin (interpolated per column between philtrum and chin); thin lips on a slit curve
  5.2 cm wide (upper 3.5 mm, lower 4.2 mm at the centre, tapering), one colour (Morgan soft rose 186,104,94; Verdandi natural 176,110,94),
  soft edges and slit line; Morgan's corners lifted 0.8 mm (calm), Verdandi's 3.5 mm (smile) with soft nasolabial smile lines; the mouth
  cavity's inner faces (texels > 3 mm behind the lip surface) a muted rose so the mouth reads closed.
- **Shading** (`build_glb_wy.py`, NRELAX 30): normals of the mouth area and the nose underside relaxed toward the surrounding surface (the
  pale zig-zag fold under the slit and the dark V under the nose were Meshy's folds catching the light); nose underside geometry relaxed a
  little more (`tweak_wy.py`, at most 4 mm) and its paint lightened.
- The head mesh is shared by both women, so the smile is paint, not geometry (a geometric smile would make Morgan smile too).
Sheet (read): `review/sheet_faces_before_after_r14.png` (rows Morgan r9 / r14, Verdandi r9 / r14; MM9's front and profile; front, 3/4, true
profile, low 3/4, from below, mouth close-up).

## Face form pass r15-r16 (user notes on r14, 2026-11-02; 0 Meshy credits)
User: Morgan "mouth + nose needs work?" (`review/user_notes/morgan_mouth_nose_front.png`), Verdandi "this also strange"
(`review/user_notes/verdandi_nose_mouth_front.png`): the nose a smoothed wedge with no nostrils or wings (Verdandi's wings two blobs on a
flat nose, a smear beside the bridge), the mouth a pale painted line on a flat lower face. Rollback: `work/rollback_r14/`.
- **Cause**: my r9-r14 steps, not Meshy's mesh. Clay of the untouched Smart Topology head (`work/refs/clay_asm_frozen_*`) has a proper nose
  (tip, wings with a crease to the cheeks, nostrils) and modelled closed lips; the nose-underside relax (`tweak_wy.py`, up to 4 mm), the
  normal relax over nose and mouth (`build_glb_wy.py` NRELAX), the flattened head normal map there and my repaint (the nose base painted as
  flat skin with two dots, the mouth as a thin line, a muted cavity) flattened them.
- **Fix**: those four steps undone (nose geometry as Meshy made it, NRELAX 0, Meshy's head normal map, Meshy's own nose and mouth paint,
  which was painted onto this geometry); kept: eyelid rotation, pearl, throat, scalp, lids on the eyeballs. Paint now only tones: the
  darkest nostril texels lifted halfway to a soft shadow; Meshy's lip texels (hue 335-12, sat > 0.4) take one colour per tier by
  luminance ratio (Morgan rose 196,96,92; Verdandi warm rose 184,102,90). No new sculpt and no Codex repaint were needed: the geometry
  carries the forms and the paint fits it (the earlier "pout" was the r5 lipstick over these lips, not the lips).
Sheet (read): `review/sheet_faces_r14_vs_r16.png` (viewer lighting; rows Morgan r14 / r16, Verdandi r14 / r16; MM9's front and profile;
front close-up, 3/4, true profile, low 3/4, party view).

## Checks (final GLB, `review/gates/`)

| Gate | Result |
|---|---|
| See-through (`see_through_gate.py`, every 3rd 30 fps frame of all 8 clips + Running 12, 8 azimuths x 0/20 deg, 3 mm pixels) | r1 (no linings) head 177 px Standing, torso 272 px Death, collar 63 px; **r5, r9, r14 and r16 (`see_through_r8/`): every zone <= 7 px in every clip except Death torso 26 px** (frame 33, az000 el20: the gown hem from the feet mid-fall) |
| `arm_hand_gate.py --outer-only --exact` (48 fps) | 0 frames over 1 cm in every clip, both hands; finger stretch max 2.36 (Fidget R) |
| `jitter_gate.py` | 0 fails (no arm corrections) |
| `robe_gate.py` (legs through the skirt) | 0 in 7 clips; Death 1/45 frames at 0.8 cm |
| `detached_parts_audit.py` | the two legs (feet), by design (MM9 has no thighs; legs hang free inside the skirt, as PF1/PF8); small lining pieces 1.5-2 mm behind their cloth |
| `bone_length_audit.py` / `flat_shading_check.py` / `check_winding.py` | 0 stretching / 0.01 body, 0.00 head / 0 inverted closed parts |
| `floor_audit.py --world mm9` | rows 264 and 265 ok: stand -0.2, walk -0.1..+1.5, living -1.4, dead 0.0 |
| `texture_quality.py` | body atlas 61.0 %, spread 1.11, fragments 1.1 %, stretch p90 1.14; head atlas 55.2 %, spread 1.77 (face 1.7x), fragments 0.9 %, stretch p90 1.15 |
| Regression `--world mm9 --headless-run-regression-suite actors` | r16: `mm9_actor_models_build_every_binding` PASS (214 descriptors on 92 models, 0 failed). r4: `mm9_actor_models_build_every_binding` PASS (204 descriptors on 90 models, 0 failed); suite passed 190, failed 3: the known `out05_event_clearance...`, plus `actor_3_runtime_preview...` and `jeric_whistlebone...` (could not load out05 / map assets): `worlds/mm9/modifiers.yml` was rewritten by another session at 13:44 during the run with `taunt_seconds`, which the current build rejects ("failed to load common gameplay data"); not this binding (`review/gates/regression_actors.log`) |
| Viewer `run_creature_review.py check` | 16 switches, 0 failed, 0 console errors |

## Sheets (read)
`review/masters_vs_mm9.png`, `review/sheet_r3_body.png` (both tiers front/3-4/back), `review/sheet_faces_vs_mm9.png` (r3) and
`review/sheet_r4_face.png` (MM9's face, front, 3/4, from below, under the jaw, hand; both tiers), `review/sheet_r3_ears_hands.png` (both
ears, under the jaw, both hands, both tiers), `review/strips_mature.png` (every clip, five frames), `work/clay/c1_sheet.png` (clay clips).

## Open points
- **Eyes** (r9): lids lowered in geometry and paint; Verdandi's squint is paint on a shared lid shape, milder than MM9's smile.
- **Verdandi's mantle**: MM9's own low-res damask, now an even non-mirrored repeat; a little more yellow than MM9 in bright light.
- **Mantle in Running**: faint facets where the mantle bends on the skirt chains; Death torso 26 px see-through at one view.
- **Map placement not switched** (orchestrator's step): the rebuilt maps place the stand-ins 380 / 384; descriptors 9264 / 9265 are ready.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_wyrde_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_wyrde_reduce_claude/before/`.
