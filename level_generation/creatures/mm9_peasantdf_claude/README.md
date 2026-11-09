# MM9 dwarf townswomen PeasantDF1-4 (mm9_peasantdf1..4) — 3D actors, 2026-11-02

Variants batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`, `TOWNSFOLK_BRIEF.md`). MM9 `MONSTERS.txt` rows on the four
dwarf-woman models: 1 Commoner DF1a, 5 Shopkeeper DF1b, 2 Commoner DF2b, 4 Town DF3a, 7 Prisoner DF3b, 3 Town DF4b,
6 Shopkeeper DF4a. Placed DAT objects (`scripts/dat_objects.py` of DM2 with `DwarfFemale`): CommonerDwarfFemaleA 6 (row 1),
CommonerDwarfFemaleB 2 (row 2), ShopKeeperDwarfFemaleB 2 (row 6), TownDwarfFemaleB 1 (row 4); rows 3, 5, 7 are unplaced.
Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

## Body / variant split (the decision)
- `mm9_meshcmp.py` (re-run): every pair is the same 53-node skeleton (bind identical) and worst-region p90 1.9-3.3 cm.
  Side by side (`review/mm9_all_1.png`, `review/mm9_all_2.png`, heads `review/mm9_heads_all.png`) the differences are paint:
  DF1's loose hair, DF2's kerchief and the DF3/DF4 hoods are ONE rounded shell (the same LF/RF_tail chains); DF4's long
  sleeves are painted over bare forearms, DF3's missing apron is paint. So **ONE Meshy body** (design 1 = DF1a, the most
  placed: 6 of 11) and **four paint designs** on it.
- **One GLB per MM9 model** (`mm9_peasantdf1..4.glb`), each the same mesh, rig and clips with its own body + head paint and
  the model's two skins as tiers (region mask + ramps). Not one GLB for all four: the renderer uploads every material's
  images when a model loads (`ModelRenderer.cpp` texture loop), so one GLB would load all four designs' paints for any one
  woman. No geometry differs between the four GLBs (no duplicated body: one Smart Topology, one rig, one clip set).

| Item | Value |
|---|---|
| Runtime GLBs | `assets_source/worlds/mm9/models/mm9_peasantdf1.glb` (pdf1_a, pdf1_b), `mm9_peasantdf2.glb` (pdf2_b), `mm9_peasantdf3.glb` (pdf3_a, pdf3_b), `mm9_peasantdf4.glb` (pdf4_a, pdf4_b); `tools/install_model.py --world mm9` from `export/` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantdf_claude` (`scripts/bind_actors_pdf.py`, under the flock): `MM9 1 Commoner` pdf1_a, `MM9 5 Shopkeeper` pdf1_b, `MM9 2 Commoner` pdf2_b, `MM9 4 Town` pdf3_a, `MM9 7 Prisoner` pdf3_b, `MM9 3 Town` pdf4_b, `MM9 6 Shopkeeper` pdf4_a; scale 100, `yaw_offset -1.570796327`, stride walk 0.35 / run 0.55 (`scripts/stride.py`: 0.27/0.41 m walk, 0.45/0.61 m run), look Neck + Head, impact 0.608 s (hattack `Rattack`) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` rows 1-7 (fallback visuals = the stand-ins 313/314/316/317/319/320/318); tables regenerated, descriptors 9001-9007; heights 118 / radius 31 (see Heights) |
| Triangles LOD0/1/2/3 | 13,476 / 6,737 / 2,423 / 806 (d3 13,884 with the braids; job 7: + 2 x 832 modelled ears; before 11,681 / 5,840 / 2,100 / 699: 8,513 painted + 3,168 back-side twins; Smart Topology 15,226 -> 8.6k after reduction; head + hair 3.4k, MPFB hands 2 x 700) |
| Skeleton | MM9 PEASANTFEMALEDWARF / PeasantDF1-4 (53 nodes: Scene Root -> Spine1, skirt ring Bone22 with eight two-bone hem chains, both thighs; LF/RF_tail hair-side chains; mitten fingers Finger0/01, Finger1/11) + 15 MPFB finger bones per side; mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps, `source/mm9_lib/pfemaledwarf.glb`, the whole 10-clip library) | Standing stand, Walking walk, Running run, Talk conv1, Fidget fidget2, Fidget2 fidget3, Fidget3 fidget4, AttackMelee hattack, Hit wince, Death die1, Dead; no source offset (the female library starts at its bind); root nodes Spine1, Scene Root, Bone22, both thighs |
| Textures per design | body 2K colour + 1K normal/ORM, region mask + ramps; head + hands set 2K colour + 1K normal/ORM, head region mask + ramps (hair / hood / kerchief); specular 0, metallic 0 |
| Meshy credits | **75 / 110** (r4 spent none): Smart Topology 5; body 4K retextures d1, d3, d4 (30); head 4K retextures d1, d3, d4 (30); one combined body+head 4K retexture for d2 (10). Backup 2930 at start, 2765 before the last job (shared balance); no retries |

## Designs and tiers
| Design / GLB | Shared paint (tier A of the GLB) | Other tier | Head set |
|---|---|---|---|
| d1 `mm9_peasantdf1` | DF1a: blonde, blue dress, white blouse and apron | pdf1_b (DF1b): dress and hair recoloured (red-brown, auburn) | own head retexture (d1 turnaround) |
| d2 `mm9_peasantdf2` | DF2b: olive check dress, cream apron | none (DF2a is used by no row) | **d4's head paint** recoloured (cream kerchief, fringe): d2's own head paint came from the combined body+head job and had a doubled lip line and red cheek blotches |
| d3 `mm9_peasantdf3` | DF3a: olive pinafore over ochre underdress, ochre hood | pdf3_b (DF3b): pinafore, underdress and hood recoloured | own head retexture (d3 turnaround) |
| d4 `mm9_peasantdf4` | DF4a: rust dress, cream linen sleeves/yoke/apron, ochre hood | pdf4_b (DF4b): dress, linen and hood recoloured | own head retexture (d4 turnaround) |
Tier targets (`scripts/tiers_pdf.py`): each region texel is matched to the nearest point of MM9's bind mesh; MM9's A and B
skins share the UV layout, so the tier colour is MM9's at the texel's luminance quantile x the gain mapping MM9's shared skin
onto our paint. Fit errors (8-bit mean/p95) are in `textures/d*_ramps.json` (d1 dress 1.5/4.3, d3 pinafore A 1.1/3.9,
B 5.5/16.5, d4 dress A 3.2/9.4, B 6.9/16.7). **The B tiers keep A's face** (MM9 paints a different woman): all three B rows
(3, 5, 7) are unplaced, so no Codex face repaint was spent on them; their hair/hood colours follow MM9's B skin.

## Review r4 (coordinator, 2026-11-02 evening; 0 Meshy credits)
Review of `sheet_mm9_vs_ours.png` / `sheet_faces_r2.png`: (1) pdf3_b's lower face pale under a hair ramp, (2) one egg-shaped
headwear shell for all four, (3) stern, heavy-shadowed, tanned faces, (4) B-tier dresses far darker than MM9's B skins.
- **Face out of every head ramp** (`tiers_pdf.py`): the head's skin shell in front (z > 0.03) below the hairline (y < 1.075)
  is never part of a hair/hood/kerchief/braid region; d3's hair rule dropped (hood + braid column only); d1's hair region
  also takes the blonde scalp under the parting.
- **Per-design headwear geometry** (`headwear.py`, positions only, on each design's copy of the master
  `work/master_v1c_d<N>.blend` -> twins -> `work/master_v2_d<N>.blend`, the build default per design): the hair/hood shell
  is cast radially from the head's centre onto the design's own MM9 hair/hood surface (MM9's face left out), smoothed; the
  hem lowered toward the shoulders at the back and sides (`drop` d1 2 cm, d2 3, d3/d4 3.5) and a hood point over the crown
  (`peak` d3 1.2 cm, d4 2 cm). **DF3a braids**: two tapered plaited tubes along MM9's own hair-side chains (LF/RF_tail,
  rigid per segment), textured with a procedural plait (`braid_paint.py`) in the head set's free column (u 0.82-0.98,
  v 0.05-0.55), its own region for tier B (black braids). DF2's kerchief hem: a darker embroidered band at the back and
  sides (`kerchief_hem.py`). Clay check `review/sheet_headwear_clay.png` (MM9 heads vs ours, front / side / back).
- **Faces**: `smile.py` (shared, positions only: mouth corners lifted 3.5 mm and set 0.8 mm back, the apples of the cheeks
  2 mm forward; the painted lips move with the mesh); `face_warm.py` (every design: skin half way to a light peach,
  eye-socket broad luminance lifted 60 % toward the cheeks with the head normal eased 35 % flat there).
- **B tiers** take MM9's own B colours (x1.3 albedo), not MM9-A-to-our-paint scaled ones, and a body region's MM9 colours
  come from the MM9 skin texels its own colour rule picks on MM9's shared skin (the nearest-point match crossed garments):
  MM9 B medians d1 dress 80/30/23 (red), d3 pinafore 31/29/36 (navy), underdress 99/40/36 (red), d4 dress 79/43/13;
  fit B mean 3.3 / 4.2 / 4.1 / 6.7 levels. Braid B (black) 2x brighter than MM9's shadowed texels so the plait shows.
- **r4 gates** (installed sha256 df1 bc68e5e1f210..., df2 76d62d7ddc84..., df3 e70eb358550a..., df4 8124ddd71cf6...):
  arm/hand 0 frames > 1 cm in 11/11 clips on all four; jitter 0; sleeve poke 0 mm; see-through worst (d1 / d3 / d4) skirt
  43 / 45 / 44, sleeves 44-46 and 27-28, boots 16, torso 17-18, collar 15-16 px, hair and head 0 (`review/gates/see_through_r4_d*`);
  winding 0, detached 0, flat 0.00; LOD0 11,682 (d3 12,090 with the braids); head atlas d3 50.9 % (braid column); floor 7/7;
  viewer r4c 77 switches 0 errors; `mm9_actor_models_build_every_binding` PASS (230 descriptors on 101 models). 0 Meshy credits.
- Sheets: `review/sheet_faces_r4.png` (all seven tiers, MM9 front / 3/4 / profile / back vs ours front, 3/4, true profile,
  low 3/4, party, back, party at 128 px; halves `sheet_faces_r4_top.png`, `_bot.png`), `review/sheet_mm9_vs_ours_r4.png`,
  `review/sheet_headwear_clay.png`. The viewer's head focus still misframes this rig: faces judged in EEVEE.
- Left after r4: expressions are a gentle smile by geometry (3.5 mm) on the same Meshy paint, not MM9's broad grins; no head
  repaint was bought. DF3b keeps A's ginger fringe; DF2's fringe is d4's curls in a warmer tone; the hood points are modest
  (MM9's DF4 peak is sharper); hood fold/brim are paint, not geometry; MM9 DF1's back braids are not modelled.

## Review r5 (coordinator, 2026-11-02 night; 0 Meshy credits)
- **DF3b braids and fringe**: the braid column and a new `fringe` region (the ginger fringe on the face shell above
  1.052 m, allowed through the face exclusion by its saturation) take an explicit dark brown-black hair ramp over our own
  plait / fringe luminance (linear 0.008..0.105), so the plaits and highlights stay; DF3a keeps the ginger.
- **DF3/DF4 hoods smaller**: `headwear.py shrink=0.86,0.82` (the shell narrows 14 % at the temples and loses 18 % of its
  back bulge above the ears, never within 9 mm of the skull) and clearer points (`peak` d3 2.2 cm, d4 3 cm). Clay
  before/after `review/sheet_headwear_r5.png` (MM9 / r4 / r5, front, side, back).
- r5 gates (installed sha256 df3 e4ada034c61c..., df4 fe6f75a3d03f...; df1/df2 unchanged since r4): see-through head and hair
  zones 0 on DF3 and DF4 (cloth slivers: skirt 43, sleeves <= 49, torso <= 19, boots <= 15, collar 13 px;
  `review/gates/see_through_r5_d3|d4/`); DF3 arm/hand 0 frames > 1 cm, jitter 0, detached 0, winding 0; floor 7/7; viewer
  r5 77 switches 0 errors; `mm9_actor_models_build_every_binding` PASS (234 descriptors on 103 models; a first run failed on
  another agent's `MM9 46 Town`, bound before its tables were regenerated, and passed on the rerun).
- Faces keep the r4 gentle smile. Sheets: `review/sheet_faces_r5_d34.png` (DF3 a/b, DF4 a/b vs MM9: front, 3/4, profile,
  low 3/4, party, back, party at 128 px), `review/sheet_faces_r5_before_after.png` (r4 above, r5 below).

## Review r6 (user note via coordinator, 2026-11-02 night; 0 Meshy credits)
User: "head graft obviously wrong since it cuts off the pendant? + the head itself isnt like anatomic? its like missing
some stuff near temples?"
- **Graft seam moved up under the jaw** (`neck_regraft.py`, on the shared master after the smile: a level cut at 0.338 m in
  the MM9 frame, 241 neck/upper-chest faces back to the body material; they always had body UVs, painted by the body
  retexture at the head faces' small upload density). The chest, the collar line and the whole necklace/pendant now come
  from the body paint; `seam_tone.py --cut 0.927` (export frame) meets both sets' skin at one tone under the jaw with the
  normals eased flat 1 cm either side. DF2/DF4's body paints had their collar/kerchief edge on the neck: `neck_fill.py`
  (neck tube above 0.862/0.872 m, non-skin texels -> nearest neck skin). The neck below the jaw is now at the body set's
  low small-island density (plain skin, soft).
- **Temples and cheeks** (`face_widen.py`, geometry before paint changes; measured with `face_measure.py` against MM9
  PeasantDF1a's face skin): temples (z 0.44-0.46) 5.2-5.4 -> 5.6-6.1 cm half-width (MM9 6.2), cheeks (0.40-0.42) 5.6 ->
  6.2-6.3 cm (MM9 6.4); eyes, nose, mouth and the midline untouched (weights fade to 0 near them). The painted head
  paint still fits (positions moved under the existing paint; no new head paint bought). The hair/hood shells
  (`headwear.py`, new `clear=0.004`) keep 4 mm outside the widened skin.
- DF4 linen region s < 0.28 (the neck skin had joined the B linen ramp).
- r6 gates (all four reinstalled: sha256 df1 096baccbe9d6..., df2 531ac166353c..., df3 8abc575f24c4..., df4 4df20ee724b9...):
  arm/hand 0 frames > 1 cm in 11/11 clips on all four; jitter 0; sleeve poke 0 mm; detached 0; winding 0; flat 0.00; body
  atlas 61.2 %, head set 40.7 % (d3 48.7 % with the braid column); see-through head and hair zones 0 on all four, cloth
  slivers skirt 42-43, sleeves <= 49, torso <= 19, collar <= 18, boots <= 15 px (`review/gates/see_through_r6_d*`); floor
  7/7; viewer r6 77 switches 0 errors; `mm9_actor_models_build_every_binding` PASS. 0 Meshy credits.
- Left: a small dark spot at DF4b's V-neck; the neck below the jaw is softer (body set density) than the face.
- Sheets: `review/sheet_face_widen_clay.png` (clay before/after, head set in red: the seam now under the jaw),
  `review/sheet_faces_r6.png` (all tiers: MM9 front/3/4/profile/back vs ours front, 3/4, profile, low 3/4, party, back,
  chest, chest 3/4, party at 128 px), zooms `review/r6_zoom_a.png`, `r6_zoom_b.png`, `r6_zoom_d24.png`.

## Job 7: ears, neck seam, cheek crack lines (user review 2026-11-04; 0 Meshy credits)
User: "df1-df4 - check if something can be done with their ears" (`review/user_20261104/ears.png`, DF1 low 3/4: the ear a
faint painted outline on a flat side of the head, a hard horizontal line across the lower neck, faint polygon crack lines
across cheek and jaw). MM9's dwarf women (`review/mm9_heads_all.png`) cover the ears completely with hair, kerchief or
hood; our hair/hood edge runs diagonally across the ear, so the ear is now modelled whole and tucked into the hair.
- **Ears** (`add_ears_pdf.py`, on each design's `work/master_v2_dN.blend` -> `work/master_v3_dN.blend`, the build default
  now): one closed loose part per side, 100 % `Bip01 Head`, face attributes head = 1 (head set) and ear = 1: an outline
  5.5 x 3.1 cm (tilted 15 deg back, front attachment at the painted ear, top at brow height, lobe at the nose base) over a
  polar grid around the concha; the lateral surface stands off the skin by a plate lean with concha bowl (floor >= 1.2 mm
  off the skin), antihelix ridge, scapha groove, rolled helix rim, tragus and a soft lobe; the front edge and lobe front
  sink 1.2 mm into the cheek; a coarser medial surface runs from the rim into the skull. 832 triangles per ear (LOD0
  11,681 -> 13,476; d3 12,090 -> 13,884). The hair/hood shell and its back-side twin are lifted over the ear where they
  would not clear it by 3 mm (d3 5 mm; bumps d1 9.6, d3 9.3, d4 7.5 mm, d2's kerchief already clears), and the hair
  vertices within 1.5 cm of an ear (fading out at 3.5 cm) are re-weighted to 100 % `Bip01 Head` (they carried 14 % Neck
  and 12 % hair-chain weight there and swayed into the rigid ears by up to 9 mm in AttackMelee and Death).
- **Ear paint** (`ear_paint.py`, per design, from `textures/*_prejob7.png` copies, idempotent): the ears have their own
  islands in the head set's free top strip (u 0.06-0.23, v 0.86-0.92, the face's 22.5 px/cm), painted as the cheek's skin
  tone in front of the ear x cavity shading from the ears' own ambient occlusion (rays over skin, ears and hair,
  smoothed), a slight warm flush on rim and lobe and fine grain; flat normal map, the cheek's ORM; `textures/ear_uv_mask.png`
  keeps them out of every hair/hood ramp (`tiers_pdf.py`). The old painted outline on the skin shell beside and under the
  ear: 3D median of the skin within 7 mm.
- **Crack lines** were paint: every head-set UV island had a 1-2 texel darker rim (border texels 3 % darker in the median,
  11 % at p10 on d1's face). Border texels within 2 px take the nearest texel further inside the same island; only gutter
  texels next to a changed texel are refilled (a global re-pad gave sliver faces a neighbouring island's colour: a blue
  dress wedge on DF1's neck in the first try).
- **Neck seam** was paint too (the vertex normals across the old level cut at 0.909 m agree to 0.02 deg): r6 moved the faces
  between 0.909 and the new seam at 0.926 m to the body material, painted there from tiny low-density upload islands of
  another tone. The broad colour of every skin texel of both sets between 0.865 and 0.96 m is replaced by one 3D-smooth
  field (2 mm voxels, sigma 1 cm, both sets), the paint's detail kept (faded to 30 % at the two seam lines); necklace and
  cloth texels with a 2 px halo untouched; the body normal map eased flat within 1 cm of 0.909 m.
- `shrink_shadow_lods.py`: closed parts thinner than the shrink margin (the ears) turned inside out in shadow LOD2/3
  (4 inverted closed parts in check_winding); such parts now leave the shadow meshes.
- New gate `ear_poke_gate.py` (every 2nd 30 fps frame, every clip; ray from each ear vertex toward the posed head centre:
  a hair/hood/braid face before the skin = the ear stands outside the hair): first build d1 8.9 mm (AttackMelee), 7.8
  (Death), 3.9 (Dead), 2.6 (Fidget2); after the re-weighting d1, d2, d4 0.0 mm in every clip, d3 1.6-1.7 mm in every frame
  (a static spot) -> CLEAR 5 mm for d3 -> 0.0 in every clip; braids 0.0 (`review/gates/job7/ear_poke_d*.txt`).
- **Job 7 gates** (installed sha256 df1 427a0e944504..., df2 14931a12370d..., df3 c59945aa9daf..., df4 60c6bcd2dd83...;
  `review/gates/job7/`, gates_pdf copies in `review/gates/d1..d4/`): ear poke 0.0 mm in every clip on all four (braids 0.0);
  arm/hand 0 frames > 1 cm in 11/11 clips on all four; jitter 0; sleeve poke 0 mm both sides; detached 0; flat 0.00;
  winding 0 (all LODs and shadows); see-through identical to r6 on all four (head and hair zones 0; cloth slivers skirt
  42-43, sleeves <= 49, torso <= 19, collar <= 18, boots <= 15 px); floor 7/7 ok; viewer job7-20261104 77 switches 0
  errors; `mm9_actor_models_build_every_binding` PASS (252 descriptors on 114 models) and mm6-8 PASS. Texture quality,
  head set: atlas 40.7 -> 41.3 %, spread 1.54 -> 1.55, stretch p90 1.92 -> 1.93 (d1; r6 values measured on the r6 viewer
  GLBs): both already over the 1.3 / 1.5 targets before this job (the r4-r6 geometry moves under fixed UVs), unchanged
  by the ears. Body set 61.2 % unchanged. Rollback: rebuild with `BLEND=work/master_v2_dN.blend` after copying the
  `textures/*_prejob7.png` back and deleting `textures/ear_uv_mask.png` (the r6 GLBs themselves were not kept).
- Sheets (viewer, its lighting): `review/ears_job7/sheet_before.png` / `sheet_after.png` (every tier: right and left ear
  side-on, low 3/4 both sides = the user's shot, front close-up, party view), `review/ears_job7/sheet_neck_before_after.png`
  (DF1, DF4, DF2: neck front from below and low 3/4 both sides, before/after rows). Before shots from the r6 viewer GLBs kept
  in `review/ears_job7/viewer_r6_glbs/` (a working copy of the viewer). Clay: `work/job7/clay_d*.png`.
- Left: the DF1 necklace still breaks at the old 0.909 m cut (the band's own paint of the chain sits a few mm off; r6, not
  touched); faint polygon tone patches remain in DF4's neck band; the ears are procedural paint (no Meshy repaint), the
  B tiers keep A's ear tone like their faces.

## Route (scripts/, repo root unless noted)
0. `convert_sources.sh` (8 skins + library), `ref_renders.py` -> `review/mm9/`, `review/mm9_head/`; `ref_sheets.py` (Codex input
   sheets `references_hd/mm9_*`).
1. HD masters (Codex, `codex_slot.sh`): `codex_masters.sh d1 pdf1a 1|2` (brief `references_hd/d1/CODEX_BRIEF.md`; run 1 attempt 1
   selected over Codex's own pick: truer 3/4, MM9's centre-parted bob; `clean_alpha.py`); design views on d1's silhouette
   `design_briefs.py` + `codex_design.sh d2|d3|d4`; head turnarounds `head_briefs.py` + `codex_head.sh d1|d3|d4` (calm, warm,
   no ear jewellery, natural lips).
2. Meshy Smart Topology 15k from `references_hd/d1/00_three_quarter.png`.
3. `fit_rig.py` + `fit_config.json` (Spine2 interpolated: its band hit the back only) -> `drop_trinkets.py` (necklace, beads,
   collar ring, bust brooches: paint in every design) -> `reduce_uv.py` -> `scripts/geo.sh`: `drop_bracelets.py` -> MPFB female
   hands `graft_hands.py graft_pdf.json` (0.135 m) -> `neck_bisect.py` (level cut at 0.32 m, one clean seam line) ->
   `head_split.py head_pdf.json` -> `eye_fill.py` -> `fill_holes.py` (FILL_NEAR: the eye sockets) -> `ear_tuck.py` (Meshy's ears
   under the hair shell) -> `cuff_trim.py -0.03` -> `stub_clamp.py` -> `triangulate.py` -> `uv_pass.sh` (**never re-run**: body
   62.7 %, head 61.6 %) -> eyeball cups dropped (`loose_parts.py`, `work/master_v1.blend`) -> `stub_clamp.py` v2 ring cap
   (`master_v1b.blend`) -> `twin_faces.py` (`work/master_v2.blend`, the build default).
4. Uploads: body `texturing/pdf_body_upload_tp.glb`, head `pdf_head_upload_tp.glb`, d2 `combined_upload.py` (body UVs x0.5
   lower-left, head UVs x0.5 lower-right: one 10-credit job for both sets; `split_combined.py` cuts the return).
5. Paint per design (project folder) `scripts/paint_chain.sh <prefix> <body job> <head job> work/pdf1_noeyes.glb`:
   `compose_texpass.py` -> gentle grade -> `compose_headhand.py` -> `paint_clean.py` (hair/hood underside and inner shell,
   grey/dark scalp and ear skin, pale neckline band projected onto the neck; `--lip-tone 0.55` for d3) -> `seam_tone.py`
   (both sets' broad skin colour meets at the cut, normals eased flat 1 cm either side, gutters re-padded) -> `wrist_fix.py`
   (hands to the cheek tone, met half way with the forearm skin; one wrist band per design: d1/d2 silver, d3 leather,
   d4 the sleeve cuff). Env: d1 `WRIST_BAND=158,160,168`; d2 `WRIST_BAND=165,160,150` with head job `meshy/head_retexture_d4`;
   d3 `CLEAN_ARGS="--lip-tone 0.55" WRIST_BAND=110,70,45`; d4 `HAND_REF=face WRIST_BAND=205,190,160`.
6. Runtime (repo root): `scripts/rebuild_designs.sh d1 d2 d3 d4` (`INSTALL=--install`) = `tiers_pdf.py` + `build_runtime_pdf.sh`
   (export -> `clips_mm9.py` (soft offsets) -> `finger_pose.py` (relaxed fingers from the two-bone mitten) -> `hand_rest.py`
   per `hand_rest_pdf.txt` (Fidget2 left hand on the hip) -> prepare -> LODs -> shadow fix -> `region_variants.py` -> extras ->
   `floor_fix.py` (`floor_ops.txt`) -> `mirror_glb.py` -> winding). Viewer: `viewer_tiers_pdf.py d1 d2 d3 d4` +
   `make_viewer_manifest.py`. Binding: `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c
   'python3 level_generation/creatures/mm9_peasantdf_claude/scripts/bind_actors_pdf.py && python3
   tools/mm9_import_discovery/mm9_monster_bodies.py --write-overrides && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.
   Gates: `scripts/gates_pdf.sh dN`, `see_through_gate.py`, `sleeve_poke_gate.py`, `robe_gate.py` (project folder).
7. Job 7 (2026-11-04, repo root unless noted): `scripts/add_ears_pdf.py work/master_v2_dN.blend work/master_v3_dN.blend
   work/job7/ears_dN.npz` (d3 with `CLEAR=0.5`) -> (project folder) `scripts/ear_paint.py dN work/job7/ears_dN.npz` (after the
   paint chain; restarts from `textures/*_prejob7.png`; re-running the paint chain needs it re-run) -> `rebuild_designs.sh`
   (tiers_pdf.py honours `textures/ear_uv_mask.png`) -> `scripts/ear_poke_gate.py work/mm9_pdfN_floor.glb
   work/job7/ears_dN.npz 2`. Viewer shots: `scripts/ear_shots.sh`, `scripts/neck_shots.sh`, `scripts/ear_sheet_job7.py`.

## Checks (final build r3, installed 2026-11-02; `review/gates/`)
The four GLBs share mesh, weights and clips, so the geometry gates were run on design 1 (and the arm/hand, jitter, texture,
flat, detached, bone and winding set on all four, `review/gates/d1..d4/`: identical numbers).

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, 11 clips, 48 fps) | **0 frames over 1 cm, both hands, every clip** (Fidget2 left hand on the hip was 2.9 cm / 65 frames before `hand_rest.py`); forearms max 0.6 cm (AttackMelee R, one frame); finger stretch p99 <= 1.18, max 1.97; wrist max 94 deg (AttackMelee R, MM9's); 19 joints per hand (five chains) |
| Jitter (`jitter_gate.py` vs the retargeted clips) | **0 fails** (all four GLBs) |
| Sleeve poke (`sleeve_poke_gate.py`) | **0 mm in every clip, both sides** (rest was 20.3 mm, 7 left stub vertices, before the stub ring cap) |
| See-through (`see_through_gate.py`, every 2nd 30 fps frame, 16 views, 3 mm px) | worst background pixels v1 (no twins) -> final: hair 41 -> 0, head (face/hair gap) 60 -> 0, skirt/apron 167 -> 43, sleeves 66/26 -> 46/28, boots 27/22 -> 15/8, torso 20 -> 19, collar 16 -> 15; the rest are slivers at silhouette edges in Fidget3 / Death (`review/gates/see_through_final/`) |
| Legs through skirt (`robe_gate.py`, PF1's, skirt = Bone* chains) | **numeric fail**: 1.2 cm in Standing up to 7.9 cm in Running on its signed-distance test; the textured renders of Walking/Running/AttackMelee from front, side and 3/4 (`review/legs_skirt.png`) show no leg or boot through the cloth: the gate's hem/outer-surface assumptions (PF1's robe) do not fit this skirt; not resolved |
| Floor (`floor_audit.py --world mm9 --match 'MM9 [1-7] *'`) | **7 / 7 ok**: stand 0.0, walk -0.1..+0.6, living -0.3, dead 0.0 |
| Winding / detached / flat | 0 inverted closed parts; 0 detached in any pose (22 components); flat 0.00 on both materials |
| Bones (`bone_length_audit.py`) | 12 checked, 2 "stretching": both thighs (0.18-0.19 m bind vs 0.48-0.50 m): MM9's dwarf female skeleton hangs the thighs from the Scene Root, so the audit measures root motion, not a bone stretch |
| Texture quality | body atlas **61.2 %**, spread 1.05, fragments 0.2 %, stretch p90 1.08; head set 42.9 % of the 2K image (head square + hand squares, as DM1/DM2's 41-42 %), spread 1.24, fragments 1.0 %, stretch 1.12 |
| LOD0 | 11,681 triangles (ceiling 15k) |
| Viewer (`run_creature_review.py check`) | r3-20261102: 77 switches, 0 failed, 0 console errors (7 tiers) |
| Regression (`OPENYAMM_REGRESSION_FILTER=actor_models_build_every_binding ... --world mm9 --headless-run-regression-suite actors`) | `mm9_actor_models_build_every_binding` **PASS** (226 descriptors on 99 models, 0 failed); mm6-8 PASS; `review/gates/regression_actors.log` (only the binding cases were run, not the whole suite) |

Faces (pre-screen, Blender EEVEE with the viewer GLBs' baked tiers; the viewer's `head` focus misframes this rig, as on
DM1/DM2): `review/sheet_faces_r2.png` (all seven tiers: MM9 front / 3/4 / profile mirrored to game handedness; ours front,
3/4, true profile, low 3/4 from below, party view, party view at 128 px), `review/sheet_faces_d3.png` (d3 after its fixes),
`review/sheet_ears.png` (both sides and the nape, bind and Talk: the ears sit under the hair/hood in every tier).
Other sheets: `review/sheet_mm9_vs_ours.png` (every tier, 4 views), `review/mm9_all_1.png`, `review/mm9_all_2.png`,
`review/mm9_heads_all.png`, `review/hands_fp.png`, `review/legs_skirt.png`, `review/strips_d1_q34.png`, `review/xray_v1.png`.

## Deviations and open points
- **B tiers keep A's face** (rows 3, 5, 7 unplaced): DF1b's circlet and coiled braids, DF3b's black braids and DF4b's lighter
  face are not reproduced; hair/hood/dress colours are.
- **DF2's face is DF4's** (d2's own head paint had a doubled lip line); her kerchief keeps faint fold blotches from the hood
  paint it was recoloured from, and the MM9 kerchief's embroidered hem band is missing.
- d3: the turnaround's braids hanging in front of the shoulders were not painted onto the chest (the mesh has none); the
  bust brooches are paint (they read whitish); d1B and d3B dresses come out darker than MM9's (the gain maps MM9 A onto our
  darker paint).
- Expressions are calm but closer to neutral than MM9's smiles; no Codex face repaint was spent.
- Small dark specks on d1's apron (paint) and the skirt's back in some walk frames (twin layer close to the cloth).
- Necklaces, brooches and bracelets of the Smart Topology were deleted (paint per design); MM9 draws them as paint too.
- Not looked at in game (map placement still uses the stand-ins); LOD1-3 and shadow meshes not looked at; motion judged on
  strips and gates, not watched at speed; tier B clips beyond the bind pose not looked at; Android cook.

## Heights
The table generator left rows 1-7 at 61 / 33 until `mm9_monster_bodies.py --write-overrides` was re-run (MM9's rule gives
118 / 31 for FD_1..4, (12, 23, 12)): now 9001-9007 are 118 / 31. That rewrite also added the then-missing overrides of rows
10 (PeasantDM4, 123 / 31), 17 and 19 (PeasantF6, 174 / 31) by the same rule; nothing else changed (diff checked).

## Binding plan (map placement)
The DAT classes above are placed with the legacy ids 313/314/320/317 by `transcode_mm9_dat_to_odm.py`; they should place
9001/9002/9006/9004. Per the brief that switch is the orchestrator's. No transcoder or map change here.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdf_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdf_reduce_claude/before/`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdf_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdf_reduce_claude/before/`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdf_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdf_reduce_claude/before/`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdf_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdf_reduce_claude/before/`.
