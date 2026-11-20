# MM9 young elf townsman PeasantM2d (mm9_peasantm2d) — 3D actor variant, 2026-11-02

Variants batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`). MM9 `MONSTERS.txt` rows naming `PeasantM2d.abc` (only these two):
**24 Town** "Peasant Elf MaleB A" (skin PEASANTM2C, DAT class `TownElfMaleA`, 6 objects) and **26 Shopkeeper** "Peasant Elf MaleC A"
(skin PEASANTM2D, DAT class `ShopkeeperElfMaleA`, 8 objects; 14 placements). Two skins = two tiers of one model.
Status log: `devdocs/mm9_rework/overnight/status/variants_peasantm2d.md`. Lease identity `mm9:peasantm2d`.

## Decision: variant route on PeasantM2's approved body (no warp)
`meshcmp.py peasantm2d:peasantm2` (re-run): head/torso/legs p90 2.6 cm, arms 2.1 cm. A vertex-level look explains it:
- the two ABCs have **identical skeletons** (all 45 bind matrices equal) and nearly the same topology (354 vs 365 vertices,
  708 vs 714 faces);
- most of the "difference" is a **rigid 2.6 cm offset** of the whole M2d mesh against the skeleton (spine vertices: exactly
  (0, 1.88, -1.84) cm, std 0.0007); aligned on the spine, torso and head p50 are 0, the head's 14 extra/moved vertices are the
  **elf ears** (tip 12.4 cm out, 85.6 cm up), limbs 2-6 cm (hem/sleeve flare, boot tops) — all below our Meshy-vs-MM9 fit noise
  and invisible in the silhouette overlay (`review/sheet_sil_m2_red_m2d_green.png`: only the ears differ).
So M2d = PeasantM2 + elf ears. A per-vertex warp would only move our mesh by MM9's mesh offset, so none was applied: PeasantM2's
body, rig, weights and clips are reused unchanged (clips bit-identical, `scripts/anim_diff.py`), with procedural elf ears,
a closed mouth, an upper-tunic lining, a new body paint and two head paints. Own GLB `mm9_peasantm2d.glb`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm2d.glb` (`tools/install_model.py --world mm9` from `export/mm9_peasantm2d.glb`) |
| Variants | `pm2d_d` (row 26 Shopkeeper, PEASANTM2D, base), `pm2d_c` (row 24 Town, PEASANTM2C) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` (`scripts/binding.yml`, `scripts/bind_under_lock.sh` under the flock): `MM9 24 Town` (pm2d_c), `MM9 26 Shopkeeper` (pm2d_d); PeasantM2's values: scale 100, yaw -1.570796327, stride 1.1 / 2.8, look Neck/Head, impact 0.533 |
| Descriptors | rows 24 (stand-in 343) and 26 (346) in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated |
| Triangles LOD0/1/2/3 | 13,599 / 6,798 / 2,445 / 814 (PeasantM2's 12,039 at LOD0 less Conv-clip nothing + 588 ear + 970 upper-tunic lining + 2 lip-hole faces) |
| Clips | PeasantM2's: Standing stand1, Walking walk3, Running run, Fidget fidget4, Talk conv2, AttackMelee hattack2, Hit wince1, Death die1, Dead, Cower cower. Conv1/Conv3/Bow dropped (only Wilam.scr plays them) |
| Textures | limbs 1792 + torso 2048 colour (new 4K paint on PeasantM2's frozen UVs, `uv_pm2.py` never re-run), 1K normal/ORM; torso mask R tunic / G sleeves + ramps (C: teal tunic and sleeves); head 1792 colour per tier, shared 1K normal/ORM |
| Meshy credits | **20 / 20**: body 4K retexture 10 (backup 3035 before), head D 4K retexture 10 (backup 3025 before); 2985 seen after both (other agents spend too) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm2d_claude/review/viewer/ (r4-20261102) |

## Clips the rows play
DAT objects (`../mm9_peasantm7d_claude/scripts/dat_objects.py "(Town|Shopkeeper)ElfMaleA"`): 6 without a script (NPCbase.scr ->
BaseRun.inc `LoopAnim Cower`), shopkeeper.scr x4 (BaseWander, no animation names), NPC188/190/193/206.scr (sounds, quest text;
NPC193/206 take an animation from ScriptParams, empty). So the core roles + Cower, as PeasantM7d.

## Route (project folder unless noted; PeasantM2's scripts copied into scripts/, PeasantM2's project only read)
0. Sources `source/mm9/pm2d{c,d}.glb`, `pm2{a,b}.glb` (`convert_abc_model.py --scale 0.0256`); `scripts/ref_sheets.sh` -> `references_hd/mm9_*`.
1. **Ears** `scripts/add_ears.py` (PeasantM7d's generator adapted to PeasantM2's master: `mat`/`part` attributes, midline x = 0,
   HeadUV islands in the free band v < 0.072) on `../mm9_peasantm2_claude/work/uv_v3.blend` (read only) -> `work/ears_v4.blend`:
   `root=0.085,0.004,0.776 tip=0.146,0.064,0.866 width=0.046 press=1 pressbox=-0.025,0.058,0.705,0.825 smooth=25`. Ears rigid on
   `Bip01 Head`, normals recalculated outward (M7d's inside-out lesson; 588 faces flipped by recalc), part 22. PeasantM2's human ears
   (crumpled helix, wider than M7's) pressed flat to the cheek line + 25 Laplacian passes, so no second ear shows. Clay checks
   `review/clay/earclose4_sheet.png`, `earclose4b_sheet.png`, `references_head/ear_shape_views.png`.
2. **Mouth closed** `scripts/mouth_close.py work/ears_v4.blend work/mouth_v2.blend deep=0.001 squeeze=1.0 groove=0.0025 smooth=30
   xw=0.036 smoothx=1` (positions only; UVs/paints valid): PeasantM2's mouth was closed 1-5 cm back by its face_fix.py, which
   left a 2-3 mm slot with a pale back wall between the lips ("second lip / plate"); the pocket vertices move to 2.5 mm behind the
   lips and collapse to a crease; a 4-edge hole in the lower lip's centre filled (2 faces). **Master `work/mouth_v2.blend`.**
   Clay `review/clay/mouth3_sheet.png` (before: `review/clay/mouth_sheet.png`).
3. **Body HD masters** (Codex, `scripts/codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`; design from the MM9 D renders,
   pose/silhouette authority PeasantM2's masters), halo removed, `scripts/align_masters.py` onto PeasantM2's masters (IoU 0.57-0.80 ->
   0.88-0.91) -> `references_hd/aligned/`. **Head masters** (`scripts/codex_head.sh`, `references_head/CODEX_BRIEF.md`): edits of
   PeasantM2's clean-shaven B head views with the clay ear views, young blond elf D -> `references_head/clean/` (aligned, IoU 0.97-0.98).
4. **Meshy**: `requests/retexture_body.json` on `texturing/pm2d_body_upload.glb` (= PeasantM2's upload, sha256 equal);
   `requests/retexture_head_d.json` on `texturing/pm2d_head_upload_v4.glb` (head faces + ears, HeadUV).
5. **Maps**: `compose_pm2.py` (tier d only), gentle grade, `tone_pm2.py` (dark cloth texels take the LOCAL cloth colour: two cloths
   now), `finish_tex.py`. PeasantM2's `head_seam.py` is **not** run (this paint has no forehead seam; the blend joined the brows).
   Head D: `scripts/head_d_fix.sh` = finish_tex -> `mouth_fix2.py` (the closed groove painted from the 8 nearest lip texels with a soft
   contact line) -> `eye_fix.py` (red rims to cheek ratios, the grey under-eye circles lifted). Head C (0 credits): `scripts/head_c.sh`
   = Codex repaint of the flat front render (`scripts/face_front.py render`, `scripts/codex_face.sh`, `references_face/`) ->
   `fit_face_c.py` (nostrils x0.68 and smile x0.84 narrower to fit the geometry: no doubled nostrils / lip on the cheeks; painted
   catchlights removed; low frequencies matched to D at the window edge) -> `face_front.py project` (face window, z-buffered, front
   facing) -> `eye_fix.py`. C shares D's head normal/ORM.
6. **Tiers** `scripts/tiers_fit_pm2d.py` (torso mask by paint class: R dark green tunic, G cream sleeves, split by luminance 0.38 and
   chroma; C targets from the MM9 C/D skin quantiles): fit tunic D 1.24 / C 0.36, sleeves D 2.10 / C 0.09 (mean 8-bit).
7. **Runtime** `scripts/rebuild.sh [--install]` (IN = mouth_v2.blend): PeasantM2's chain + `collar_lining.py` (upper tunic lined:
   PeasantM2's tunic is welded to the neck, the holes were folds over empty interior in Death/Dead) -> export -> clips_mm9 (soft line)
   -> arm_const -> hand_rest -> half/skirt keys -> prepare -> LODs -> shadow LODs -> `tiers_pm2.py` (C head image) -> extras -> floor ->
   winding. Viewer: `scripts/viewer_tiers.py`, `scripts/make_viewer_manifest.py`.

## Approved PeasantM2 unchanged
`assets_source/worlds/mm9/models/mm9_peasantm2.glb` sha256 `fc3e623f4d1d...` before (`work/pm2_sha256_before.txt`) and after; its
master `work/uv_v3.blend` opened read-only (sha256 `5db9b8a7...` unchanged); nothing written into `../mm9_peasantm2_claude/`; its
actors.yml block untouched (rows 24/26 are a new block).

## Checks (installed build, sha256 af2bba9b...; `review/gates/`)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps) | = PeasantM2 (same clips): hands 0 frames over 1 cm except **Fidget R 5.3 cm, 15 frames** (MM9's fidget4 rubs the forehead, PeasantM2's accepted value) and Talk L 1.1 cm on 1 frame; finger stretch max 2.8; 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | **0 fails** |
| Sleeve poke (`sleeve_poke_gate.py --skin-mat PeasantM2d --cloth-mat Pm2dTorso`) | 0 mm, 0 frames, every clip, both sides |
| See-through (`see_through_gate.py`, step 3, 8 azimuths x 0/20 deg) | worst background px before -> after the upper-tunic lining: torso 359 -> 88 (Death 18 / Dead, slivers at the belt and hip), sleeve L 49 -> 28, sleeve R 40 -> 20 (single slivers at the bell-cuff rim), head 9 -> 9 (ear-root specks), trousers 0. Images `review/gates/st_final_sheet.png` (before `st_dry_sheet.png`) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 2[46] *'`) | both ok: stand 0, walk -1.3..+0.7, living -1.3, dead 0 |
| Detached (`detached_parts_audit.py`, 24 fps) | 0 detached, 26 components |
| Winding | 0 inverted closed parts |
| Flat shading | limbs 0.00, torso 0.01, head 0.07 (10 flat faces in the LOD0 head primitive) |
| Texture quality | limbs atlas 59.0 %, spread 1.54 (hands 1.5x by design), fragments 0.0, stretch 1.26; torso 54.9 % (PeasantM2's frozen layout; linings on one texel make the spread meaningless), fragments 1.8 %, stretch 1.10; head 63.0 %, spread 1.16, fragments 0.0, stretch 1.16 |
| Bones | 12 checked, 0 stretching |
| Tier ramp fit (8-bit mean) | tunic D 1.24 / C 0.36, sleeves D 2.10 / C 0.09 |
| LOD0 | 13,599 triangles (ceiling 15k) |
| Viewer `run_creature_review.py check` | 20 switches, 0 failed |
| Binding regression `mm9_actor_models_build_every_binding` | **PASS**, 206 descriptors on 91 models (`review/gates/regression_binding.log`) |

Sheets read: `review/sheet_mm9_vs_ours.png` (MM9 D/C rows vs ours, front, 3/4, back, side), `review/sheet_face_vs_mm9.png` (MM9 face,
our face, party view; both tiers), `review/sheet_ears_d.png`, `review/sheet_ears_c.png` (front, party, profiles, sides, ear close-ups,
3/4 backs, from below, jaw-neck), `review/sheet_d_details.png`, `review/sheet_shoulders_d.png`, `review/clay/mouth3_sheet.png`,
`review/clay/earclose4_sheet.png`, `review/sheet_sil_m2_red_m2d_green.png`, `review/gates/st_final_sheet.png`.

## Deviations and open points
- Ears procedural (cupped leaf), MM9's are flat cards; they read a little pinker than the cheek.
- C's face is a Codex repaint projected from the front (sides and neck are D's paint matched at the edge): a ruddier, older, lined
  face; MM9's C grins with teeth, ours is a closed smile (no jaw bone, closed mouth).
- C's trims stay D's gold braid (MM9 C: brown trims and a rope belt tie); only tunic and sleeves are recoloured.
- The vest's armhole edge carries Meshy's grey-brown shadow band in places (shoulder close-ups).
- Map placement (rows still placed as legacy 343/346) is the orchestrator's.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantm2d_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm2d_reduce_claude/before/`.

## Seated and work clips for RUDEProps (2026-11-07)
MM9's posed townsfolk (RUDEProps: the Sturmford innkeeper, Ludwig, Tryggva, Halfdan, Ercc, the drinkers; The Arena's
spectators) loop clips from MM9's PeasantSeated.abc and PeasantWork.abc libraries. Those clips are grafted onto the
**installed** `mm9_peasantm2d.glb` (meshes, LODs, reduction, variants and the old clips byte-identical, `graft_byte_check.py` OK),
not rebuilt, so the 2026-11-04 LOD0 reduction stays.
- Sources: `convert_abc_model.py --scale 0.0256` of both libraries (system python + gltf venv: `../mm9_peasantm2_claude/scripts/py_yaml_gltf.sh`),
  `mirror_glb.py`, `reparent_skirt.py` -> `../mm9_peasantm2_claude/source/true/peasant{seated,work}_src.glb`. The seated library
  lacks Bone15/Bone23 (second segments of two skirt hinges): they follow their first segment.
- Chain: `clips_mm9.py` with `scripts/roles_seated.json` on the project body, `arm_const.py` (4 deg, as every clip),
  `half_keys.py`, `skirt_keys.py` (front flaps swing 44-53 deg over the thighs), `claude_shared/graft_clips.py` onto the
  installed source, `check_winding.py` 0, `tools/install_model.py`; `claude_shared/bind_script_clips.py` (role = clip name).
  Floor (`claude_shared/floor/floor_fix.py`, after the graft): MM9's seated library carries the feet 25.4 cm above the
  model origin (MM9 drops these props with MoveToFloor), so every chained seated clip moves by ONE amount, the offset
  that grounds `sitting`'s first key (`--seat-like sitting <clip>`, -25.43 cm; list `sitting` last or it measures 0):
  feet on the floor, Ercc's set 0.7 cm up, no pop between sitting, listen, conv_seated, ercc*, ludwig_*. Seated hip
  joint 0.59 m (seat about 0.48 m). `innkeeper2` `--raise-uniform` +1.07 cm. **`sitting2` keeps MM9's origin** (the
  bar-stool pose: feet 26.9 cm above the origin, pelvis 0.93 m), so its placement goes at the DAT position without a
  floor drop, as MM9 places that prop (no MoveToFloor).
- Clips (s): sitting 1.37, sitting2 1.70, listen 6.70, ludwig_writing 9.00, innkeeper2 2.20, ercc_out 0.10 (loops);
  conv_seated 18.13, ercc01a 21.70, ercc01b 21.67, ercc01c 22.67, ercc02 8.70, ludwig_lookup 4.03 (one-shots, no ease:
  ercc01a-c start and end in the sitting pose; ercc02 ends slumped and ercc_out holds that last pose).
- Gates (`review/seated/`): arm/hand 0 frames over 1 cm except ercc01b (L 5.1 cm, 22 frames; R 3.3 cm, 3) and ercc01c
  (L up to 6 cm on the M2 body): MM9's drinking gesture brings the hand to the mouth/chest. Skirt gate: the thighs pass
  through the side panels in every seated clip (about 19.6 cm, the hinge ring cannot drape a horizontal thigh); front and
  back read correctly (`../mm9_peasantm2_claude/review/seated/clay_skirt.png`). Strips: `review/seated/clay_a.png` (this body), `../mm9_peasantm2_claude/review/seated/clay_{a,b,ercc,skirt}.png` (same clips on the M2 body).
- Rollback: `work/seated/before/mm9_peasantm2d.glb` (the source before the graft).
