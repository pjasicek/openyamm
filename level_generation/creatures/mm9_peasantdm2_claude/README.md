# MM9 PeasantDM2 old dwarf townsman (mm9_peasantdm2) — 3D actor, 2026-11-02

Townsfolk batch, wave 2 (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`). The only MM9 `MONSTERS.txt` row naming
`PeasantDM2.abc` is **9 Commoner** "Peasant Dwarf MaleA B", skin PEASANTDM2A, DAT class `CommonerDwarfMaleB` (**6 placed
objects**, legacy stand-in 323: Sturmford 1, Thjorad mine 5; the brief's "about 10" counted other classes). Skin PEASANTDM2B
(another man with a studded headband, a laced leather tunic) is used by no row; it is tier B. Second body on MM9's dwarf male
townsfolk skeleton: **PEASANTDM2's bind equals PEASANTDM1's exactly** (41 joints, every translation and rotation, checked
with `scripts/cmp_skel.py`) and the `peasantmaledwarf` library bind, so DM1's retarget (source offset, root nodes, roles)
is reused unchanged. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantdm2.glb` (`tools/install_model.py --world mm9` from `export/mm9_pdm2.glb`, linings + ears r7 sha256 dec7348e99ad...; r6 rollback in `work/rollback_r6/`, r4 in `work/rollback_r4/`), variants `pdm2_a`, `pdm2_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantdm2_claude`: `MM9 9 Commoner` (pdm2_a); scale 100, `yaw_offset -1.570796327`, stride walk 0.4 / run 0.7 (DM1's, same skeleton and clips), look `Bip01 Neck, Bip01 Head`, impact 0.966 s (hattack1) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 9 -> 323; tables regenerated (186 rows), descriptor 9009 |
| Triangles LOD0/1/2/3 | 11,942 / 5,969 / 2,145 / 714 (r7: +3,264 lining, rim and twin faces, +28 neck cap; r6 8,650 / 4,322 / 1,553 / 515; face pass: +17 patch faces, +90 backing-plate faces) (Smart Topology 15,458 -> 8,865 after reduction; head + hair + beard 4,538, MPFB hands 2 x 700). Shadow meshes drop the one-texel linings |
| Clips (30 fps, `source/mm9_lib/pmaledwarf.glb`) | DM1's set: Standing, Walking, Running, Fidget, Fidget2, Talk (conv1), AttackMelee (hattack1), Hit, Death, Dead, Cower, RubBeard, Rock, Hammer, Dump |
| Textures | body 2K colour + 1K normal/ORM, region mask (R tunic, G trousers, B boots, A belt) + ramps per tier; head + hands set 2K colour + 1K normal/ORM with a **tier B head colour and normal** (different man); specular 0, metallic 0 |
| Meshy credits | **35 / 60**: Smart Topology 5, body 4K retexture 10, head A 4K retexture 10, head B 4K retexture 10 (backup 3400 -> 3295) |

## Face pass (2026-11-02, orchestrator review; 0 Meshy credits, one Codex run)
Review of r4: the face read as a ruddy mask with a hard edge against the paler scalp and temples; small dark marks on the right
cheek; small, sunk, frowning eyes, irises barely visible; hands near-white against the face; tier B irises near black (MM9's B
has blue eyes). Rollback of r4: `work/rollback_r4/` (source GLB, export, head maps, viewer GLBs, build script).
- **One skin tone** `scripts/skin_unify.py` (per head set): skin texels of the head shell (the hair is its own loose part and
  stays out, as do the beard zone, brows, lips and eyes) take one target colour (the front cheek/forehead skin moved 35 %
  toward MM9 A's warm tan by chromaticity) times the paint's own detail (img x T / mask-normalised low-pass, sigma 28 texels),
  feathered. Scalp/back skin median before 175/117/94 (A) and 127/100/87 (B), after 201/125/87 and 174/102/74; face 220/125/81.
- **Neck sides** `fix_neck_pdm2.py`: the knit paint also covered the neck sides and back up to 1.02 m (`NECK_SIDE_TOP`).
- **Eyes and mouth** Codex repaint by landmarks (Sven/PeasantM1 route): `render_face.py` unlit front (centre 1.045 m, ortho 0.26) ->
  `codex_face.sh` (brief `references_face/CODEX_BRIEF.md`, inputs: our render, the HD head front, MM9's face) -> open, smiling,
  crinkled eyes with light blue irises (B grey-blue), relaxed brows, a gentle closed smile, cheek patches removed ->
  `warp_faces.sh` (`warp_face.py` + measured anchors: Codex moved the eyes 6-16 px and the mouth 15/20 px up; after the warp
  A's irises are within 1 px, B's within 2-7 px, the mouth lines on the mesh's) -> `project_face.py` with two overlapping windows
  (1.022-1.11 m |x| < 7 cm; 0.975-1.05 m |x| < 5.5 cm: the first windows met at 1.035-1.04 m with both ramps at half weight and
  left a band of old paint), z-buffer of front-facing triangles only (the game culls the single-sided beard sheet's back).
- **Cheek gaps** (geometry, positions/faces only): `bridge_hole.py` (one pinhole), `patch_islands.py`: the collapsed-UV patch faces
  get their own UV islands in free head-set cells (`work/patch_islands.json`; `project_face.py` paints them at full weight,
  `PATCH_CELLS`) and 90 backing-plate faces (the face skin copied 2 mm inward) sit behind the three gap spots; `PATCH_SPOTS`
  repaints every texel within 8-11 mm of them whatever its facing. `pad_head.py` refills every gutter.
- **Hands** `hand_clean.py` with `HAND_REF` A 205,118,80 and B 182,100,70: texel medians hand 208/120/81 vs cheek 220/123/86 (A),
  185/101/71 vs 197/110/77 (B).
- Chain: `scripts/head_paint.sh` (reset_head_backups -> fix_neck -> skin_unify -> project_face -> hand_clean -> pad_head), then
  `TOKEN=<lease> scripts/build_runtime_pdm2.sh --install` (BLEND `work/eyes_relax_fix.blend`).
- Sheets read: `review/sheet_faces_before_after.png` (MM9 front/3-4/side vs r4 and r6: front, 3/4, side, party view 22 deg above
  front and 3/4, both tiers), `review/faces_a.png`, `review/faces_b.png` (bind and Talk incl. eye close-ups),
  `review/sheet_hands_vs_face.png` (viewer front, face and both hands under the same light, both tiers),
  `review/sheet_mm9_vs_ours.png` (viewer, both tiers), `references_face/review.png` (Codex inputs vs returns).
- Gates on r6 (`review/gates/`): arm/hand 0 frames > 1 cm in all 15 clips; jitter 0 fails; floor ok; winding 0; bones 0;
  detached 0 (16 components: the two backing plates); flat 0.00; body atlas 62.4 %, head set 42.2 % (fragments 1.3 %, the patch
  islands); sleeve poke as before; viewer r6 30 switches 0 errors; regression passed 192, failed 1 (known out05),
  `mm9_actor_models_build_every_binding` PASS (`review/gates/regression_actors_facepass.log`).
- Left: a ~1 cm shading facet beside the nose on the character's left cheek where the beard sheet meets the cheek (geometry; the
  paint there is skin); the irises are a little smaller than MM9's; tier A remains balder and longer-bearded than MM9's
  (the approved HD masters); B's irises read grey-blue.

## See-through openings and ears (r7, 2026-11-02; 0 Meshy credits)
User note "holes in sleeves + some in knees (e.g. running anim 12)" (`review/user_notes/sleeve_knee_holes_running12.png`;
the screenshot's pose is our 30 fps frame ~16, the viewer counts frames differently) and the orchestrator's ear sweep
(`../claude_shared/mm9_overview/ear_sweep_20261102.png` rows 17-18). Rollback of r6: `work/rollback_r6/` (installed GLB,
viewer GLBs, head maps, build script with the old BLEND default).
- **Causes.** Meshy's cloth and leather are single-sided and the game (and viewer) cull back faces. *Cuffs*: `sleeve_tuck.py
  0.75` pulls the hand stub to 75 % of the sleeve radius and `cuff_trim.py` leaves a clean open ring, so through the ring
  the view met the sleeve's inside (and up the sleeve, the shoulder's) = background. *Knees*: each leg is two pieces: the
  trouser piece ends in the boot's turned-down cuff (rim r 7 cm) and the boot shaft starts 1-2 cm inside it (rim r 6.4 cm);
  when the knee bends the cuff lifts off the shaft and the view runs down the inside of the shaft to the ankle (and up
  the trousers, whose thigh weights go partly to the skirt ring's `Bone22`). *Also found by the gate*: the tunic's belt-level
  rims (skirt and upper tunic meet under the belt, open at the hips in bent poses), the collar, and the head shell's open
  neck bottom (inside the tunic; seen through the collar of the lying corpse).
- **Fix** `scripts/linings.sh` (step 7b, on `work/eyes_relax_fix.blend` -> **`work/linings_v1.blend`**, the build default;
  positions/faces only, existing UVs and paints unchanged): `neck_cap.py` (fan over the 28-edge neck bottom, neck-skin texel)
  -> `rim_lining.py` (new, generalises `sleeve_lining.py`) per rim: collar band 12 cm, belt band 12 cm, boots + trousers band
  30 cm (boot/trouser texels only), sleeves band 55 cm (to the shoulder). Each band is duplicated behind itself (3 mm,
  weights copied, flipped) on one dark texel of its region (tier ramps recolour it), the rim joined to the lining by a
  strip; later runs skip faces an earlier run lined; offsets are capped at 40 % of the distance to other cloth behind;
  Meshy's inner-layer faces (facing the bone axis) are skipped in the sleeves (their twins showed as dark patches) and
  elsewhere get a 0.5 mm twin in their own paint (a 3 mm or dark twin showed as dark specks where a posed fold pokes the
  inner layer through). Tried and dropped: `sleeve_lining.py`'s forearm continuation of the hand stub (poked 10-28 mm out of
  the back of the sleeve at rest, sleeve-poke gate), its own lining (arm-weighted sleeve only: views up the sleeve met the
  unlined shoulder), inner faces unlined everywhere (reopened 18-40 px at the boots, collar and belt).
  `shrink_shadow_lods.py` now drops one-texel triangles from the shadow meshes (shrunk with the cloth they crossed it:
  inverted closed parts in `check_winding.py`) and leaves them out of its reference surface.
- **Gate** `scripts/see_through_gate.py` (new): LOD0, every clip at every 2nd 30 fps frame (+ Running 15), 8 azimuths x
  {level, party 20 deg down}, orthographic 3 mm pixels, two Workbench renders with back faces culled (mesh alone; mesh + a
  normal-flipped red twin): a pixel covered only by back faces is background through the cloth (HOLE); each is ray cast to
  its first face and attributed to a zone by the face's dominant bone. `scripts/hole_probe.py` lists the faces behind the holes
  of one frame/view; `scripts/closeup.py` renders textured, culled close-ups (optional red twin, section cut).
- **Hand on the hip** (Running 14-18): fingers in front of the belt, not through it (close-ups front and side; arm and hand
  gate 0 frames > 1 cm).
- **Ears** `scripts/fix_ear_pdm2.py` (head paint chain, after `hand_clean`; reads `*_preear.png` backups, `reset_head_backups.py`
  moves them and restores the head ORM): both head turnarounds wear braid ties at ear height, the mesh has none, and the head
  retextures painted them onto the ears (each ear its own ~80-triangle loose part) and the shell just below/behind (A: white
  beads + brown smudges; B: copper bows, also on the hair bob). Neither tier has a clean ear, so the ears are synthesised:
  the tier's temple skin (A 187/135/103, B 165/104/78) x a crease near the head x a faint grain, flat normal, temple ORM; on
  the shell within 2.5 cm of the ear (below its top) dark smudges, tie colours and anything not light-grey hair below the ear
  centre, and tie colours on the hair bob within 4 cm, take the mean of the clean paint around (12/6/3 px, else the hair
  median). `ear_islands.py` (ear/part rasters), `ear_views.py` / `ear_sheet.py` (copied from DM1, plus image overrides and a
  16-bit/EXR UV pass), `exr_to_npy.py`.
- Sheets read: `review/sheet_holes_before_after.png` (r6 vs r7, both tiers: Running 12 front, Running 16 = the user's pose with
  its cuff and boot tops, cuffs and boot tops at 12 and 15, the gate's worst frames), `review/sheet_ear_before_after.png`
  (r6 vs r7, both tiers: tight ear views, low views, sides, 3/4 backs, party view).
- Left: a ~1.5 cm smooth light-grey patch under each ear where the ties were (filled paint, no strand detail; under the braid,
  not visible from party distance); the gate's few remaining pixels (table) are at the edge of the lying corpse and the
  beard/mouth (head zone, not cloth); the detached-parts audit now lists the boots (lining artifact, below).

## Clips the MM9 scripts play
`scripts/dat_objects.py DwarfMale`: `CommonerDwarfMaleB` 1 without a script (NPCbase -> BaseRun.inc `LoopAnim Cower`), NPC8.scr and
NPC9.scr (`LoopAnim Params`: the params are voice files, basemelee.inc), Shopkeeper.scr (BaseWander: walk), two
`scripts\DwarvenMiner.scr` (stand, rub_beard, rock, hammer, dump). Same clip list as DM1 (`dwarf_roles.py` default). The miner's
pick prop is not modelled.

## Route (scripts/, repo root unless noted; DM1's chain with the changes marked NEW)
0. `convert_sources.sh` (NEW for DM2: DM1's copy still held PeasantM7's text), `ref_renders.py` -> `review/mm9/`, sheets
   `references_hd/mm9_views_{a,b}.png`, `mm9_head_views_{a,b}.png`, `mm9_skin_x4_{a,b}.png`.
1. HD masters: `codex_masters.sh 1|2` (brief `references_hd/CODEX_BRIEF.md`; run 1 first return kept), `clean_alpha.py`; head
   turnarounds `codex_head.sh a|b` (A: balding, white braids, white beard; B: the headband man on A's silhouette).
2. Meshy Smart Topology 15k from `00_three_quarter.png`.
3. `fit_rig.py` + `fit_config.json` -> `work/fit_v1.blend`, `reduce_uv.py` -> `rig_v1.blend`, `graft_hands.py graft_pdm2.json`
   (NEW option `hand_len` 0.222: Meshy's hands were 0.277 / 0.265 m, 1.3x MM9's 0.21 m and uneven; both MPFB hands now 0.234 m
   to the fingertip), `loose_parts.py` (NEW: drops a 21-vertex stray finger piece), `head_split.py head_pdm2.json`.
4. Eyes before paint (NEW order): `eye_fill.py ... 7,9` then `loose_parts.py` deletes the eyeball cups (parts 7, 9) **before** the
   UV pass, so Meshy paints the filled shell and `export_fix.drop_parts` is empty; `fill_holes.py` (4-5 edge holes, triangulated).
5. UVs `uv_pass.sh` (on `work/eyes_v1.blend`): body atlas 62.8 %, head 59.7 %. Never re-run.
6. Paint: `bake_ao_texpass.py`, `compose_texpass.py`, gentle grade; `bake_hands.py ... old_caucasian_male/...`;
   `compose_headhand.py pdm2_tp|pdm2b_tp ...`.
7. Geometry fixes on the painted master (positions/faces only, paid paints stay valid): `sleeve_tuck.py 0.75 0.003 1`
   (DM2 wears real sleeves to the wrist, so PeasantM7's route, not DM1's bare-wrist route) -> `cuff_trim.py ... 0.01` (clean
   sleeve ring 1 cm past the hand joint over the tucked stub; the graft had left a toothed sleeve rim with the stub showing
   between the teeth) -> `sheet_flush.py` (NEW: beard sheet edge laid onto the cheek) -> `cheek_patch.py` x6 (NEW: closes the
   see-through gap beside the nose where the beard sheet and face shell were both open; faces between existing boundary
   vertices only, smooth UVs where the vertices share an island) -> `eye_relax.py` strength 0.4 (PeasantM1's, NEW frame
   options `SHELL_Z=0.40 Y_FRONT=-0.08 EYE_ELLIPSE=0.066,0.034,0.462`) -> `work/eyes_relax.blend` -> face pass ->
   `work/eyes_relax_fix.blend` -> **7b `scripts/linings.sh`** (r7: neck cap, collar / belt / boot / sleeve linings, see
   "See-through openings and ears") -> **`work/linings_v1.blend`** (build default).
8. Paint fixes, in order: `sleeve_paint_fix.py export/mm9_pdm2.glb` (skin wedges on the cuffs) -> `fix_collar_pdm2.py
   work/pdm2_body_tex.glb` (NEW for DM2: body texels within 5 cm of the neck opening: pink inner rim and the orange-speckled
   "leopard" neckline band -> the tunic's dark knit) -> `fix_neck_pdm2.py work/pdm2_body_tex.glb pdm2_tp` and `pdm2b_tp`
   (NEW for DM2: the head retexture painted the neck base as dark knit; dark saturated texels behind the beard -> the tier's
   cheek skin, thin dark strokes removed by a grey closing, the head normal map flattened there, all gutters refilled; the
   beard is kept out by saturation and depth) -> `hand_clean.py` (NEW `HAND_REF`: A 212,136,100; B 200,124,94 — the script's own
   reference left the ruddy cheeks out and gave grey hands) -> `tiers_pdm2.py` (NEW for DM2, below). Head set since the
   face pass: `scripts/head_paint.sh` (reset -> fix_neck -> skin_unify -> project_face -> hand_clean -> **fix_ear_pdm2** (r7)
   -> pad_head).
9. Runtime `TOKEN=<lease> scripts/build_runtime_pdm2.sh [--install]` (`hand_rest_pdm2.txt`: RubBeard, Talk with the head as
   a surface and a near-constant push `--hold-path 1.0 --sigma-path 0.3 --sigma-dir 0.5`, Death; BLEND default
   `work/linings_v1.blend`); viewer `scripts/retier.sh <rev>`
   (project folder). Binding: `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_peasantdm2_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`. Gates `scripts/gates.sh` + `sleeve_poke_gate.py` +
   `see_through_gate.py` (Blender: `blender --background --python scripts/see_through_gate.py -- <glb> <out json> step=2
   extra=Running:15`; project folder).

## Tiers
Shared paint = skin A. MM9 skin regions come from the MM9 mesh's own UVs and joints (`mm9_skin_labels.py`,
`review/mm9_skin_labels.png`); our regions by joint, height and colour: R tunic, G trousers (purple-red stripes below the hem),
B boots (saturated leather below 0.31 m, gold ornaments out), A belt (the braided cord, 0.585-0.65 m). Tier B target per texel =
MM9 B's region colour at the texel's luminance quantile x the MM9 A -> ours gain. Belt and boots: our paint was far brighter than
MM9's relative to the tunic (belt 3.4x: a silver-white band), so tier A also takes MM9 A's own colours there (`MATCH_A` belt 1,
boots 0.5). Fit error mean / p95 (8-bit): tunic A 2.0/5.7, B 3.0/8.9; trousers 2.2/6.4, 4.1/11.0; boots 3.0/8.7, 4.1/11.0;
belt 3.8/10.2, 2.4/6.8. **B is A's paint recoloured**: B's lacing and belt buckle are not reproduced (B has no row). Head B is its
own retexture (headband, grey hair over the crown).

## Checks (final build r7, viewer r7-20261102; `review/gates/`; r4 values where a row says so)

| Gate | Result |
|---|---|
| See-through (`see_through_gate.py`, r7: 377 frames = every 2nd 30 fps frame of all 15 clips + Running 15, 8 azimuths x level / party 20 deg, 3 mm pixels; `review/gates/see_through_r7/`, r6 in `see_through_before/`) | Worst background pixels per zone, r6 -> r7: sleeve L 431 -> 4, sleeve R 391 -> 4, boot L 241 -> 0, boot R 181 -> 0, collar 129 -> 2, torso (belt, skirt, back) 109 -> 6, trousers L 61 -> 0, trousers R 7 -> 0, head (beard sheet, mouth; not cloth) 41 -> 11. Running: cloth 0 in every frame (12, 15, 16 included; r6: sleeves 284 / 129, boots 241 / 181); head 2 px. The remaining cloth pixels are single slivers at silhouette edges (AttackMelee, Fidget, RubBeard, Death) |
| Arm and hand (`arm_hand_gate.py --outer-only`, all 15 clips, 48 fps) | r7 **0 frames over 1 cm, both hands, every clip** (15 / 15). r4: forearms 0. Before the rest passes: RubBeard L 5.4 cm, Talk L 7.4 (6.9 without the beard as a surface, then 1.6 left), Death L 3.9 cm / 5 frames. Talk's push is ~9 cm, kept nearly constant (in front of the beard). Finger stretch p99 <= 1.73 (Rock R), max 3.22; wrist max 86 deg (Fidget2 R, MM9's) |
| Jitter (`jitter_gate.py`) | r7 and r4 **0 fails** (Talk failed at 1.2-2.5 deg/f upper arm with a varying push; the constant push gives 0.78 deg/f, skin 1.5 mm/f2) |
| Sleeve poke (`sleeve_poke_gate.py`) | r7 as r4 (AttackMelee L 48.4 mm, 5 f, 4 v; others identical); rest **0 mm** both sides; 0 in 8 clips. Flagged 1-6 vertices in hard wrist bends: AttackMelee L 51.3 mm (5 f), Death R 36.1, Dump R 27.8, Rock R 15.9, Hammer R 13.3, Cower L 4.2, Fidget2 R 3.6. **Checked with the vertices marked** (`render_poke.py` -> `review/poke_check.png`, worst frame of each, four views): the marked points are on visible wrist skin just past the cuff ring, or hidden by cloth (AttackMelee); no skin shows through the sleeve. The gate's perpendicular ray meets the cuff's far wall when the wrist folds |
| Floor (`floor_audit.py --world mm9`) | r7 unchanged; MM9 9 Commoner ok: stand 0.0, walk -0.1..+1.7, living -0.8, dead -0.0 |
| Winding / bones / detached / flat | r7: 0 inverted; 12 checked, 0 stretching; flat 0.00 on both materials; detached audit lists both boots (parted up to 1.7 / 1.0 cm in 12 / 4 of 744 poses, Running): an artifact of the linings (the boot's lining vertices inside the trouser cuff count as its root); the same GLB without its one-texel lining triangles audits 0 detached, as r6 (the cuff-to-shaft separation is the one now lined) |
| Texture quality | r7 body atlas 62.4 % (uv sum 66.4 %: the inner-layer twins reuse their faces' texels), fragments 0.8 %, head set unchanged 42.2 %; r4: body **62.4 %**, density p10/p50/p90 1255/1284/1314 (spread 1.05), fragments 0.3 %, stretch 1.10; head set 42.2 % of 2K (head square + hand squares, as DM1's 41.4), spread 2.26 (hands half density by design), fragments 1.1 %, stretch 1.35 |
| Viewer (`run_creature_review.py check`) | r7-20261102: 30 switches, 0 failed, 0 console errors |
| Regression `--world mm9 --headless-run-regression-suite actors` | r7: **passed 192, failed 1** (known out05), `mm9_actor_models_build_every_binding` **PASS** (`review/gates/regression_actors_r7.log`); r4: **passed 192, failed 1** (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS** (186 descriptors on 79 models, 0 failed); log `review/gates/regression_actors.log` |

Sheets read: `review/sheet_mm9_vs_ours.png`, `review/sheet_tiers.png`, `review/sheet_faces_vs_mm9.png` (MM9 heads mirrored to
game handedness vs ours: front, 3/4, side, party view 22 deg above, both tiers), `review/faces_a.png`, `review/faces_b.png`
(bind and Talk: front, 3/4, side, party, party 3/4, eyes), `review/stills_final.png` (faces, both hands, torso, full body; both
tiers), `review/poke_check.png`, `review/strips_a_q34.png`, `review/strips_a_front.png` (every clip at 15/50/85 %),
`review/neck_v8.png` (neck), `review/graft_hand{L,R}.png`, `review/xray_v1.png`, `review/wrist_trim_compare.png`.
The viewer's `head` and `arms` focus misframe this rig (empty shots); faces and hands are judged on Blender renders.

## Deviations and open points
- **Face vs MM9**: see "Face pass" (expression, eyes, skin, hands fixed; residual cheek facet).
- **Neck**: a one-pixel dark V on the front of the neck in Blender renders is a texture-sampling artifact on a UV seam (shading
  and texture there are uniform skin: checked with a UV-coded render), not paint.
- Hands 0.234 m (MM9 0.21 m) and in the face's tone; our body is fuller than MM9's (Meshy from the master).
- **Triangles** (r7): LOD0 11,942 (+3,264 lining, rim and twin faces over r6's 8,650): the price of closing every open
  garment rim with real geometry instead of a two-sided material; the linings sit on one texel each and are left out of
  the shadow meshes.
- Hammer / Dump without the miner's pick; Talk's left hand ~9 cm in front of MM9's place (the beard is in the way).
- Not looked at in game (map placement still uses the legacy stand-in, below); LOD1-3 and shadow meshes not looked at; motion
  judged on strips and gates, not watched at speed; tier B clips not looked at beyond bind/Talk; sounds; Android cook.

## Binding plan (map placement)
`CommonerDwarfMaleB` objects are placed with legacy id 323 by `transcode_mm9_dat_to_odm.py`; they should place 9009. Per the brief,
that switch is the orchestrator's (one change for every row after the batch). No transcoder or map change here.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdm2_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdm2_reduce_claude/before/`.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_RHand1`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
