# MM9 Tryggva Ravenlocks, Jarl of Frosgard (mm9_tryggva) — 3D actor, 2026-11-02

Townsfolk batch wave 3 (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`). MM9 `MONSTERS.txt` row **250** "Tryggva Ravenlocks"
(`Tryggva.abc`, skin `tryggva.dtx`, NPCbase.scr, Scale 1, BaseName PeasantMale) is the only row naming the model. Built on the
PeasantM7 / Bjarni route: Meshy body fitted to TRYGGVA.abc's own skeleton (= the 45-joint PeasantMale biped), MM9 clips only
(PeasantMale library + TRYGGVA.abc's own), MPFB five-finger hands, separate head + hands set, Codex eye-area repaint.
Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_tryggva.glb` (installed with `tools/install_model.py --world mm9 --name mm9_tryggva.glb` from `export/mm9_try.glb`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_tryggva_claude`: `MM9 250 Tryggva Ravenlocks`, scale 100, `yaw_offset -1.570796327`, stride walk 1.1 / run 2.8, look `Bip01 Neck, Bip01 Head`, impact 0.533 s (hattack2), one skin (no tiers) |
| Descriptor | row 250 (legacy stand-in 607) appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated (`generate_mm9_monster_tables.py`: 9250 `MM9 250 Tryggva Ravenlocks`) |
| Triangles LOD0/1/2/3 | 8,405 / 4,205 / 1,506 / 495 (Smart Topology 13,903; body 2,270, head + hair + braids + fur lapels + hands 6,135) |
| Skeleton | TRYGGVA.abc = PeasantMale, 45 joints (incl. `Bip01 Ponytail1` for the long hair), rest rotations unchanged, joints translated onto the HD body (`fit_rig.py` with Bjarni's `centre_span`); + 15 finger bones per side from MM9's mitten curl (`finger_alias`); mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps) | Standing stand1, Walking walk3, Running run, Fidget fidget4, Talk conv2, AttackMelee hattack2, Hit wince1, Death die1, Dead, Cower cower (PeasantMale library `source/mm9_lib/pmale.glb`); Sit sit, Agree Agree, Applause Applause, DeadStatic static_die1 (TRYGGVA.abc). TRYGGVA.abc's bind-pose clip `Tyrggva` is not used |
| Textures | body 2K colour + 1K normal + 1K ORM; head + hands 2K colour + 1K normal/ORM; `openyamm_specular 0`, metallic 0 |
| Meshy credits | **25** (Smart Topology 5, body retexture 4K 10, head retexture 4K 10; backup account 3405 -> 3295 shared balance over the session, floor 2740) |

## Clips the MM9 scripts play

DAT objects naming `Tryggva.abc` (`scripts/dat_objects.py`-style scan of `assets_dev/worlds/mm9/maps/*.raw_objects.yml`):

| Map | Object | Script | Clips |
|---|---|---|---|
| Frosgard City | `TryggvaRavenlocks0` (class TryggvaRavenlocks) | NPC180.scr | `loopanim Sit` (vanishes on keys 104/40) |
| Thronheim City | `Tryygva` (class TryggvaRavenlocks; its stale `Filename` property says Kira.abc) | ARG_Tryygva.scr | `loopanim Sit`; `PlayAnim Agree` / `Applause` on the Argument scene's Agree / Clap triggers |
| Thronheim City | `TryygvaProp` (RUDEProp, hidden until ARG_Unhide) | PropAnim.scr | `Sit` |
| Afterworld | `TryggvaRavenlocks0` (hidden until Six Fires) | none -> NPCbase.scr | BaseRun.inc `LoopAnim Cower` |
| Afterworld, Yorwick | `Tryygva` (Prop) | PropAnim.scr | `Static_die1` (corpse prop) |

Sturmford's `tryggvaspeech.scr` runs on a PeasantMS2 prop, not this body. Script-clip keys bound: talk, conv2, cower, stand, sit,
agree, applause, static_die1 and dead_static (DeadStatic).

## Route (scripts/, from mm9_peasantm7_claude and mm9_bjarni_claude)

0. **Sources** `convert_abc_model.py` (TRYGGVA.abc + TRYGGVA.dtx -> `source/mm9/`), MM9 renders `ref_renders.py` ->
   `references_hd/mm9_views.png`, `mm9_head_views.png`, `mm9_skin_x4.png`; own clips at a glance `review/mm9_clips/sheet.png`.
1. **HD masters** (Codex via `codex_slot.sh`; `scripts/codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`), halo removed by
   `clean_alpha.py` (threshold 128; raw in `references_hd/raw_codex/`); head turnaround `scripts/codex_head.sh` -> `references_head/`.
   The three-quarter master was frozen before Smart Topology; 01-04 arrived during it (gated on a contact sheet afterwards).
2. **Meshy** Smart Topology 15k (`requests/smart_topology_v1.json`).
3. **Fit + weights** `fit_rig.py` + `fit_config.json` (Bjarni's copy, `centre_span` for the back hair/mantle) -> `work/fit_v1.blend`,
   X-ray `review/xray_v1_{front,left}.png`; **reduce** `reduce_uv.py` -> `work/rig_v1.blend`; **hands** `graft_hands.py graft_try.json`
   (MPFB age 0.65); **head split** `head_split.py head_try.json` (neck cut 0.59 r 0.10 so the whole neck and the collar top are in the
   head set: the head/body seam runs on the collar cloth; the hair shell, braids, ears and the fur lapels Meshy fused into the hair go
   in the head set; `review/head_split.png`); `sleeve_tuck.py 0.75 0.003` -> `work/head_tuck.blend`.
4. **UVs** `texpass_uv.py` (body) and `texpass_head_uv.py` -> `work/texpass_head.blend`; uploads `texturing/try_*_upload_tp.glb`. Never re-run.
5. **Retextures** 4K `requests/retexture_body_tp.json`, `requests/retexture_head_tp.json`.
6. **Face geometry** `eye_relax.py` (EYE_ELLIPSE 0.06,0.04,0.81, strength 0.55; 0.9 flattened the sockets blind) and
   `drop_eyeballs.py` (Meshy's two loose eyeball pieces sat off-centre in jagged sockets; one poked through the relaxed lids) ->
   `work/eyes_v3.blend`, clay `review/face_clay_eyes_v3.png`.
7. **Wrists** `drop_inner_wrist.py 0.018 0.035 0.025 0.013` (Meshy's sleeve closure onto the old forearm and old-hand remnants inside
   the grafted stub) -> `work/eyes_v4.blend`; `cuff_weights.py 1.3 1.4` (sleeve vertices up to 8 cm above the wrist carried Hand
   weight and swung into the stub in MM9's limp death hand) -> **`work/eyes_v5.blend` = the master**.
8. **Maps** `bake_ao_texpass.py`, `compose_texpass.py try_tp ...`, `grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5
   --contrast 1.06 --saturation 1.15`, `sleeve_paint_fix.py`, `bake_hands.py work/eyes_v3.blend middleage_caucasian_male/...`,
   `compose_headhand.py try_tp ... --ref-head --hand-gain 1.12`, then **`scripts/head_chain.sh`**: `fringe_fix.py` (HAIR_MIN_Y 1.56 and a
   warm/saturated skin test, so the fur lapels and the grey hair streaks are left alone) -> `hairline_fix.py 1.700 1.716` (face shell
   above the hair edge -> nearest hair texel) -> `hand_clean.py` -> `project_face.py` with `TOP_WIN=1.696,1.735,0.05` (the Codex eye-area
   and parting repaint `references_face/out_face.png`, brief `references_face/CODEX_BRIEF.md`, `scripts/codex_face.sh`; measured
   alignment with the input 1-3 px, skin tone ratio 1.00-1.02) -> `face_touch.py` (chin edge softened, tear streak under the left eye)
   -> `fix_ear_try.py` (ears, r3; see "Ears" below). The whole chain is reproducible: a full `head_chain.sh` re-run on 2026-11-02 gave
   the same head colour and normal maps bit for bit as the r2 maps plus a stand-alone `fix_ear_try.py` run.
9. **Runtime** `scripts/build.sh [--install]` (= `build_runtime_v2.sh try Tryggva scripts/roles_try.json` with BLEND=work/eyes_v5.blend):
   export -> `clips_mm9.py` (soft offsets) -> `hand_rest.py` per `hand_rest_try.txt` (Fidget, Talk, Applause) -> prepare -> LODs ->
   shadow fix -> extras -> `floor_fix.py` (`floor_ops.txt`) -> `mirror_glb.py` -> winding -> install.
10. **Binding** (repo root, under the flock): `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
    level_generation/creatures/mm9_tryggva_claude/scripts/bind_actors.py && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.
11. **Viewer** `scripts/make_viewer_try.py <rev>` -> `review/viewer/` (r3-20261102).
    `scripts/build.sh` reads `LEASE_TOKEN.txt` and defaults to `work/eyes_v3.blend`: the r3 build ran
    `build_runtime_v2.sh try Tryggva scripts/roles_try.json` directly with `BLEND=work/eyes_v5.blend` and the current lease token
    (identical mesh and clips to the r2 install, so r2 was built from eyes_v5 too).

## Ears (r3, 2026-11-02)
Ear sweep (`claude_shared/mm9_overview/ear_sweep_20261102.png`, row 21): dark jagged hair-coloured patches on and around both ears.
**Cause**: Meshy fused both ears into the hair shell (part 1 of the head primitive; each ear is ~15-20 of its faces under the
hair's side edge). (1) `fringe_fix.py`'s hair-shell step (skin-coloured hair-shell texels above y 1.56 -> nearest hair texel,
meant for the forehead rim) took the ears' skin for a painted fringe rim and stamped hair over most of the right ear and parts
of the left; (2) Meshy's paid head paint already had hair-coloured jagged triangles on the lower ear and on the small hair-shell
faces hanging below each ear (the long hair of the head turnaround falls past the ears). **Fix** (`scripts/fix_ear_try.py`, last
step of `head_chain.sh`, reads `*_preear.png` backups): the 66 hair-shell faces in the ear box with >= 10 % skin in the composed
paint get the composed (pre-fringe_fix) paint back, then: core (the ear proper, >= 40 % skin, plus faces enclosed by core;
37 faces) hair texels -> 3D mean of the skin around them; lower (8 faces below the ear lying on the cheek) -> the face shell's
cheek skin; flap (21 faces at the ear's top edge reaching into the hair, or on the hair locks behind the ear) -> skin texels take
the nearest hair texel, so the hair still frames the ear. Head normal smoothed on the filled texels. Tried and dropped: whole ear
faces as skin (skin flaps poked up into the hair), filling face-shell texels around the ear (skin showed through the hair's gaps).
Only the head base colour and head normal images changed (`glb_diff.py` vs r2: 0.000 mm in every clip, all other images same).
Rollback: `work/installed_preear.glb` (= the r2 install). Sheet `review/sheet_ear_before_after.png` (before r2 / after r3:
rear/lear ear close-ups, both profiles, both 3/4 backs, both under-jaw views, party view from 22 deg). Remaining: the left ear
is low-poly and reads as faceted skin with a faint dark crease between its faces (the face shell under it, painted with hair,
shows through); the right ear's lobe continues as a skin-coloured triangle onto the cheek (geometry).
Regression after the last ear-sweep install (2026-11-02, `review/regression_actors_earsweep.log`): `--world mm9 actors` passed 192,
failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data");
`mm9_actor_models_build_every_binding` **PASS**.

## Faces (the batch's recurring fault list, checked one by one)

- Second brow / light band round the eyes: the Meshy head had jagged eye holes with loose eyeballs, not a recessed plate; relaxed
  softly, eyeballs removed, eye area repainted by Codex from the approved head references and projected from the front: one brow pair,
  no band or outline (`review/sheet_face_final.png`, eyes column).
- Slit / staring eyes, red rims: the Meshy paint had the eyes 1 cm apart in height and round staring irises; the repaint puts both at
  one height, symmetric about the nose, upper lids covering the iris top, no red rims.
- Fringe / hairline: the hair parts in the middle over a skin wedge; the parting notch is repainted as hair, the hair rim's skin texels
  take hair colour (fringe_fix), the face shell above the hair edge takes hair (hairline_fix). The hairline is an arch, darker at its
  very edge (the hair shell's rim seen edge-on).
- Mouth: Meshy's mouth was closed and is kept (no pout); narrower than MM9's broad smile.
- Chin / neck: no seam on the neck (the head set holds the whole neck down to the collar); a slightly lighter rim remains along the
  jaw's lower edge in EEVEE close-ups (softened by `face_touch.py`, not gone).
- Party view (22 deg above) and MM9 side by side: `review/sheet_face_final.png`; viewer heads `review/sheet_viewer_heads.png`.

## Checks (final build, `review/gates/`)

| Gate | Result |
|---|---|
| Arm and hand gate (`arm_hand_gate.py`, every clip, 48 fps) | hands 0 cm in the body in every clip except **Fidget R 1.1 cm, 1 frame** (MM9's chin scratch) and **Applause L 2.0 cm / 33 frames, R 2.1 cm / 46 frames, forearms 1.9-2.2 cm**: every Applause contact is hand against the OTHER hand/forearm (split by `exact_depth`: 0.0 cm against the body), MM9's thin hands clap and our thicker MPFB hands interleave ~2 cm at the claps. `hand_rest.py` (trunk) finds 0; a hand-vs-hand push (`scripts/clap_gap.py`, kept, not in the build) diverged. Five chains per hand (19 joints). Finger stretch p99 max 3.01 (Fidget L). Wrist max 127 deg (Death/Dead: MM9's limp hand) |
| Sleeve poke (`sleeve_poke_gate.py`, every clip) | **0 mm, 0 frames, both sides, all 14 clips** (before the wrist fixes: R 26.8-42.7 mm in every clip, L 9-13 mm) |
| Jitter (`jitter_gate.py` vs MM9's clips) | **0 fails** |
| Floor | `floor_audit.py --match 'MM9 250 *'` ok (stand 0, walk -0.1..+1.9, living -0.1, dead -0.0 world units); script clips (`clip_floor.py`): Sit, Agree, Applause, DeadStatic lowest point 0.000 |
| Winding | 0 inverted closed parts |
| Bones (`bone_length_audit.py`) | 12 checked, 0 stretching |
| Detached (`detached_parts_audit.py`) | 0 detached in any pose (24 components) |
| Flat shading | 0.0 % on both primitives |
| Texture quality | body atlas **50.9 %** (below the 55 % soft target; the pack reached 53.8 % with the head/hand islands Meshy also saw), density p10/p50/p90 1344/1411/1449 (spread 1.08), fragments 0.4 %, stretch p90 1.10; head set 39.1 % (hands are half density by design), spread 1.12, fragments 1.4 %, stretch 1.21 |
| Ears (r3) | `review/sheet_ear_before_after.png`: no hair-coloured patches on the ears from any view; see "Ears" |
| Viewer (`run_creature_review.py check`) | 14 clips, 0 failed, 0 console errors (r3-20261102) |
| Regression `--world mm9 --headless-run-regression-suite actors` (final install) | passed 192, failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS**; log `review/gates/regression_actors.log` |

Sheets read: `review/sheet_ear_before_after.png` (r3), `review/sheet_mm9_vs_ours.png`, `review/sheet_strips.png` (every clip, six times, three-quarter), `review/sheet_face_final.png`
(MM9 vs ours: front, 3/4, both profiles, party view 22 deg above, eyes, mouth, neck both sides), `review/sheet_viewer_heads.png`,
`review/sheet_viewer_body.png`, `review/wrist_{L,R}_v2.png` (Standing, Talk, Death, Applause), `review/sheet_cuffs.png`,
`review/applause_v1.png`, `review/head_split.png`, `review/xray_v1_front.png`, `review/face_clay_eyes_v3.png`, `review/chin.png`.

## Binding plan (map placement)

The rebuilt maps place Tryggva with the legacy stand-in id (607) through `transcode_mm9_dat_to_odm.py`, so the new descriptor does
not show in game yet. Per the brief this switch is the orchestrator's, once for every row: placements of DAT class `TryggvaRavenlocks`
(Frosgard City, Thronheim City, Afterworld) should use 9250. The corpse props (`Tryygva`, PropAnim `Static_die1`, Afterworld and
Yorwick) and `TryygvaProp` (PropAnim `Sit`, Thronheim) are props, not actors: if they become actors, bind `DeadStatic` / `Sit`.

## Deviations and open points

- **Sit floor**: MM9's sit pose has the feet 28 cm above the standing feet (MM9's chairs); as Bjarni and Forad (the same Argument
  table) Sit is grounded (`--ground-loop Sit`) and Agree/Applause sit at the same height (`--seat-like`). If the rebuilt Thronheim
  chairs need MM9's height, drop those three ops.
- **Applause hands interleave ~2 cm** at the claps (hand vs hand only).
- **Body atlas 50.9 %** (soft target 55 %); not re-laid (another 10-credit retexture for ~4 points).
- Close-up face: a small dark hook at the right nostril (geometry), the jaw's lower edge a little lighter than the neck, the hairline's
  dark rim; the braids are smooth dark strands (Meshy fused them; no plait relief).
- Fur mantle is painted with strong dark/light stripes (tabby-like) where MM9's is shaggy grey-brown; reads as fur at game distance.
- Cuffs are Meshy's jagged fringe; the whole cuff now follows the forearm (the hand turns inside it); a few small see-through
  triangles inside the cuff opening from below.
- Not looked at in game (descriptor not placed); motion judged on viewer and Blender strips, not watched at speed; LOD1-3 and shadow
  meshes not looked at. User artistic acceptance: not recorded.


**See-through linings added post-install on 2026-11-05 by `level_generation/creatures/mm9_tryggva_lining_claude/`** (brief `devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md`; LOD0 8,405 -> 10,160, faces appended to the installed mesh; fur capes lined with reversed copies on their own fur UVs). A rebuild from this project must re-run the lining pass. Rollback source: `level_generation/creatures/mm9_tryggva_lining_claude/before/`.
