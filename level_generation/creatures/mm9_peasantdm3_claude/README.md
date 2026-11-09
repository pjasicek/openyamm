# MM9 PeasantDM3 dwarf townsman (mm9_peasantdm3) — 3D actor, variant of PeasantDM1, 2026-11-02

Shared-mesh variants batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`). MM9 `MONSTERS.txt` rows naming
`PeasantDM3.abc`: **11 Town** "Peasant Dwarf MaleB B", skin PEASANTDM3B, DAT class `TownDwarfMaleB` (1 placed, no script), and
**12 Shopkeeper** "Peasant Dwarf MaleC A", skin PEASANTDM3A, DAT class `ShopkeeperDwarfMaleA` (1 placed, no script).
Two skins = two tiers. **Route: variant of the approved PeasantDM1** (`mm9_peasantdm1_claude`, frozen, untouched): DM1's
body, rig, weights, hands and clip chain, reshaped where MM9's DM3 differs (long hair to the shoulders, a longer pointed
beard, no medallion), with its own body and head paints. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantdm3.glb` (`tools/install_model.py --world mm9 --name mm9_peasantdm3.glb` from `export/mm9_pdm3.glb`, sha256 561040214e77...), variants `pdm3_a`, `pdm3_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantdm3_claude`: `MM9 11 Town` (pdm3_b), `MM9 12 Shopkeeper` (pdm3_a); DM1's binding values (scale 100, `yaw_offset -1.570796327`, stride 0.4 / 0.7, look Neck+Head, impact 0.966 s) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 11 -> 326, 12 -> 328 (the stand-ins of `mm9_npc_legacy_replacements.tsv`); tables regenerated (226 rows), descriptors 9011 / 9012 |
| Triangles LOD0/1/2/3 | 10,656 / 5,291 / 1,904 / 633 (DM1 7,586; + hair twin 483, linings, neck cap, rim strips; shadow meshes drop the one-texel linings) |
| Skeleton, clips | DM1's (41-joint dwarf male townsfolk skeleton, MPFB five-finger hands, `peasantmaledwarf` library, DM1's source offset, soft offset line, mirrored to MM9 handedness). MM9 DM3's bind equals DM1's except `Bip01 Ponytail1` (14 deg; MM9's hair tip): not used, our hair is skinned to Head/Neck/Spine2. Clips: Standing, Walking, Running, Fidget, Fidget2, Talk, AttackMelee, Hit, Death, Dead, Cower (NPCbase -> BaseRun.inc); no miner clips (no DAT script) |
| Textures | body 2K colour + 1K normal/ORM on DM1's body UV layout (new paint), region mask (R tunic, G trim, B shirt panel, A trousers) + ramps; head + hands set 2K/1K on **new head UVs** (the head was reshaped), region mask (R hair and beard) + ramps; specular 0, metallic 0 |
| Meshy credits | **20 / 25**: body 4K retexture 10 (backup 2925 before), head 4K retexture 10 (backup 2875 before). No Smart Topology, no rig |

## MM9 comparison (why the variant route)
`mm9_meshcmp.py peasantdm3:peasantdm1` (re-run): same 41-node skeleton (bind max 0.59 cm; only Ponytail1's rotation differs),
head p90 1.9 cm (max 5.8), torso 2.4, arms 1.0, legs 1.6 after the rigid shift. Renders `review/sheet_mm9_dm3_vs_dm1_dm2.png`,
`review/sheet_mm9_heads_dm3_dm1.png`, `review/sheet_mm9_torso.png`: DM1's cut (short-sleeved tunic over linen undersleeves, bare
forearms with wrist bands, belt, folded boots). What DM3 changes: **hair** (long, hanging to the shoulders, hiding the ears;
MM9 skins the back tip to Ponytail1), **beard** (4-5 cm longer, a broad point, its tip on the chin bone `Bone03`), **costume
paint** (B: charcoal tweed open over a cream shirt, ochre braid trims, beaded collar; A: deep purple knit with a pale gold
ring-chain yoke and front strip), **no medallion**. The skins paint two similar long-haired, bearded faces.

## Route (scripts/, repo root unless noted)
0. `convert_sources.sh` (PEASANTDM3 both skins + the library); `ref_renders.py`, `grid.py` -> the MM9 sheets above.
1. **Geometry from DM1** (copy of DM1's `work/eyes_trim.blend` in `work/from_dm1/`; DM1's project is only read):
   `reshape_dm3.py` -> `work/shape_v1.blend`: deletes the medallion (cord, pendant, bail), DM1's eyeball cups and the shin
   sliver (DM1 dropped them at export); **beard wedge** on the head shell below the mouth (-4.2 cm down, -2.2 cm forward,
   half width 11 cm); **hair** below z 0.47 stretched per column to the shoulders (back 0.29, sides 0.33, front 0.36 m),
   pushed out of the body, two smoothing passes; the lengthened hair blends Head -> Neck -> Spine2 below 0.38 m (the
   hanging ends follow the shoulders). `nomed_v1.blend` (shape=0) is the same without the reshape, for the body upload.
2. **Uploads**: body = `export_upload.py work/nomed_v1.blend texturing/pdm3_body_upload.glb UVMap` (DM1's body UV layout, DM1's
   head silhouette so the masters' unchanged heads fit); head = `uv_pass.sh` (`texpass_head_uv.py` on the reshaped head:
   head atlas 58.8 %, hand squares kept). **Never re-run `uv_pass.sh`**: the head retexture belongs to `work/texpass_head.blend`.
3. **Codex masters** (`codex_runs.sh body|head`, briefs in `references_hd/` and `references_head/`): body = DM1's five approved
   masters repainted with skin B's costume (pose, figure and head kept; `clean_alpha.py` removed the alpha haze of 01);
   head = the DM3 dwarf painted onto clay silhouettes of the reshaped head (`references_head/silhouette/`, IoU 0.98-0.998);
   the profile needed one targeted rerun (`codex_profile_fix.sh`: the beard ran 4 cm past the mesh; first in `superseded/`).
4. **Meshy**: `requests/retexture_body.json`, `requests/retexture_head.json` (4K, original UVs).
5. **Paint** (project folder): `bake_ao_texpass.py` -> `compose_texpass.py pdm3_tp ...` -> `grade_basecolor.py` (gentle) ->
   `neck_body_fix.py <export> pdm3_tp` (skin-coloured texels at the collar's back -> hair shadow) -> `paint_match.py <export>
   pdm3_tp` (boots and belt half way to MM9 B's dark leather; both skins have dark brown leather); head: `compose_headhand.py
   pdm3_tp meshy/head_retexture ... --ref-head --ref-lum-min 135 --hand-gain 1.0` -> `ear_shade.py <export> pdm3_tp` (ear and
   neck skin under the hair -> hair shadow) -> `hand_clean.py pdm3_tp 0.95` (dark vein lines). `<export>` = any build's
   `work/*_tex.glb` (texel positions). `swatch_paint.py` painted an unused dark block (from a dropped hair-wall try).
6. **Geometry after the UV pass** `geometry_after_uv.sh` (positions / faces / weights only): `ear_flatten.py` (ears pulled to the
   skull) -> `curtain_close.py` (the curtain moved in onto the cheek and jaw, smoothed sigma 3.5 cm, pushed 6 mm out of the
   tunic: from the front the background showed between face and hair; MM9's hair hugs the face) -> `rigid_beard.py` (22
   beard/jaw vertices to 100 % Head) -> `hair_twin.py` (hair thickness below 0.44 m) -> `linings.sh` (DM2's `neck_cap.py` +
   `rim_lining.py`: collar, belt rims, boots, sleeves from the wrist ring to the shoulder) -> `cuff_lining.py ... force 0.0`
   (the folded linen cuffs have no open rim) -> `work/linings_v2.blend` (build default).
7. **Tiers** `tiers_pdm3.py <export> textures/pdm3_tp_basecolor_graded.png textures/pdm3_tp_head_basecolor.png`.
8. **Runtime** `TOKEN=<lease> scripts/build_runtime_pdm3.sh [--install]` (DM1's chain; `hand_rest_pdm3.txt` = DM2's Talk line;
   `floor_ops.txt` without the miner clips; region variants for body and head materials; mirror; winding). Viewer:
   `scripts/retier.sh <rev>` (project folder). Binding: `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock
   bash -c 'python3 level_generation/creatures/mm9_peasantdm3_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`. Gates: `scripts/gates.sh` (project folder), `sleeve_poke_gate.py`,
   `see_through_gate.py` (Blender), `face_shots.sh <prefix> [clip] [s]` (viewer, both tiers).

## Tiers
Shared paint = skin **B** (row 11 Town; its costume has the details a ramp cannot invent: shirt panel, braid bands). Body
regions: R tunic, G trim (ochre braid and brooch; the beaded collar stays shared), B shirt panel, A trousers. Tier B is fitted
to our paint, except the trim (`MATCH_B`: MM9 B's own ochre; the graded paint was lemon yellow). Tier A: MM9 A's colours at
the texel's luminance quantile x the MM9 B -> ours gain; A's panel takes A's purple knit; A's trim MM9 A's pale ring-chain colour
x 0.55 (old gold; at full brightness every band read as a white stripe). Head region R hair and beard (eroded 2 px off the
skin): tier A = a luminance-preserving chroma shift toward MM9 A's greyer brown (a quantile ramp gave tier A high-contrast
light strands and a pale rim at the beard edge). Fit (8-bit mean/p95): tunic B 1.1/3.7, A 2.1/5.9; trim B 5.2/15.4, A 6.2/19.2;
panel 2.4/8.0, 2.3/6.9; trousers 2.9/7.9, 5.1/14.0; hair 1.5/4.7, 1.6/5.4.

## Checks (r4 build, `review/gates/`)

| Gate | Result |
|---|---|
| Face pre-screen (viewer lighting, both tiers; `review/shots/sheet_f4_b.png`, `sheet_f4_a.png`, `review/sheet_faces_viewer.png` with 128 px party sims; Blender `review/t8_faces.png`, `review/t9_faces.png` incl. true profiles, low 3/4, under the jaw, Talk) | one nose on the geometry, one lip line under the moustache, no lower-lid crescent, one brow line per eye, eyes open with brown irises from party height, calm half-smile; no beads or ties (Codex brief); no net strands (tier A hair fixed, above); no neck seam line (neck under the hair shaded). Beard chin solid in profile |
| Ears | MM9 hides them under the hair: flattened and shaded hair-dark (`ear_shade.py`); a small dark ear shape shows at the hair edge in the true profile and 3/4 back (`review/holes/sheet7.png`, `sheet_f4_*` earL) |
| See-through (`see_through_gate.py`, every 2nd frame of all 11 clips + Running 12/15/16, 16 views, 3 mm px; `see_through_v1/` before, `see_through_r4/` final) | worst background px before -> after: sleeve R 268 -> 42 (two lining-free slivers inside the lower edge of the right cuff, AttackMelee 34 at the party's 20 deg; `review/holes/sheet4.png`), sleeve L 186 -> 1, boots 24/24 -> 0/0, trousers 27/7 -> 0/1, collar 93 -> 63 (Death only, 4 frames, level camera), torso 82 -> 81 (the lying corpse seen from its feet at floor level, under the skirt to the tunic's back at the belt; 23 at the party's 20 deg; living clips <= 21 px, AttackMelee) |
| Arm and hand (`arm_hand_gate.py --outer-only`, 48 fps, 11 clips) | sparse test: hands 0 frames > 1 cm in every clip except **Talk L 1.4 cm, 3 frames** (as DM1; `hand_rest.py` finds no push); exact test (`--exact`, `arm_hand_gate_exact.txt`): hands **0 frames > 1 cm in every clip** (Talk 0.9 cm); exact forearm 1.5-1.8 cm in Running only with the linings in the mesh (the pre-lining build `work/t9.glb`: 0) |
| Jitter (`jitter_gate.py` vs MM9's clips) | **0 fails** |
| Sleeve poke (`sleeve_poke_gate.py`) | L as DM1 (bent-wrist frames: AttackMelee 56.9 mm 22 f, Fidget 24.3, Running 4.9; DM1 68.2/37.0/4.9); R **60.3 mm on 2 vertices in every frame, an artifact of the sleeve lining**: the pre-lining build gives R 0 mm at rest and in every clip; the flagged hand vertices sit past the cuff and the ray now meets the lining's rim strip near the axis; renders of the rest wrist (`review/holes/sheet6.png`, `sheet4.png`) show no skin through cloth |
| Rigid head | face, lips, chin, jaw and beard 100 % Head (`head_weight_probe.py`: 23 neck-side vertices behind y -0.01, under the hair, keep DM1's Head/Neck blend) |
| Hands | MPFB hands with MM9's curl (DM1's); `hand_clean.py`: one clean skin tone, the bake's dark vein lines gone (`review/holes/sheet6.png`) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 1[12] *'`) | MM9 11 Town, MM9 12 Shopkeeper ok: stand 0.0, walk -0.1..+1.7, living -0.6, dead 0.0 |
| Winding / bones / detached / flat | 0 inverted; 12 checked 0 stretching; 0 detached (12 components); flat 0.00 both materials |
| Texture quality (`texture_quality.py`) | body atlas 53.1 % (DM1's layout, reused with its new paint; DM1 53.4 %), fragments 0.4 %, stretch p90 1.07; head set 41.5 % of 2K (head square + hand squares), fragments 1.0 %, stretch p90 1.57 (the hair twin repeats hair UVs; 1.35 before it) |
| LOD0 | 10,656 triangles (< 15k) |
| Viewer (`run_creature_review.py check`) | 22 tier/clip switches, 0 failed, 0 console errors (r4-20261102) |
| Regression `--world mm9 --headless-run-regression-suite actors` | **passed 192, failed 1** (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS**; log `review/gates/regression_actors.log` |

Sheets read: `review/sheet_mm9_vs_ours.png` (MM9 renders vs viewer shots, both tiers), `review/shots/sheet_f4_b.png`,
`review/shots/sheet_f4_a.png`, `review/sheet_faces_viewer.png`, `review/t9_faces.png`, `review/t8_faces.png`,
`review/clay/sheet_curtain.png`, `review/clay/sheet_wedge3.png`, `review/holes/sheet1.png`..`sheet7.png`,
`review/st_v1_sheet.png`..`st_v4_sheet.png`, `review/head_masters.png`, `review/body_masters.png`,
`review/head_profile_fix_overlay.png`, `review/tiers/sheet_v1.png`, `review/t1_hair_motion_small.png`.

## DM1 unchanged
`review/dm1_dm2_sha256_before.txt` (installed DM1 source and runtime, DM2 source, DM1 export) checked with `sha256sum -c` after
the install: all OK; the whole `mm9_peasantdm1_claude/` tree hashed before (`review/dm1_project_tree_sha256_before.txt`) and
after: identical.

## Deviations and open points
- **One face for both tiers.** MM9 paints two similar but different men; the 25-credit cap allowed one head retexture, so tier
  A is tier B's face with greyer hair and beard. A second head retexture (10 credits) would give A its own face.
- **Tier A's costume is B's paint recoloured**: A shows B's braid bands (old gold) and an open front panel in purple; MM9 A
  has a gold ring-chain yoke and front strip and no sleeve/hem bands. The beaded collar is shared.
- **Hair**: one shell on Head/Neck/Spine2 (MM9: Head + the Ponytail1 tip). A thin crease remains on the right side of the
  hair (`review/clay/sheet_wedge3.png`); the ears show as small dark shapes at the hair edge from the side.
- No beard braid beads (MM9 has two small red ones): left out on purpose (painted detail without geometry).
- See-through residuals: the corpse's skirt from floor level (torso 81 px), collar 63 px in one Death pose.
- Not looked at in game (map placement still uses the legacy stand-ins 326 / 328; the switch is the orchestrator's, as for DM1);
  LOD1-3 and shadow meshes not looked at; motion judged on gates and stills, not watched at speed; sounds; Android cook.

## Binding plan (map placement)
`TownDwarfMaleB` and `ShopkeeperDwarfMaleA` objects are placed with legacy ids 326 / 328 by `transcode_mm9_dat_to_odm.py`; they
should place 9011 / 9012. Per the brief that switch is the orchestrator's; no transcoder or map change here.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdm3_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdm3_reduce_claude/before/`.
