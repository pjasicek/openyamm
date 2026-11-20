# MM9 PeasantM3 human townsman (mm9_peasantm3) — 3D actor, 2026-11-02

Townsfolk batch (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`, with the 2026-11-02 lessons of `VARIANTS_BRIEF.md`). MM9
`MONSTERS.txt` rows naming `PeasantM3.abc`: **45 Town** "Peasant Human1 MaleB A", skin PEASANTM3B, DAT class `TownHumanMaleA`
(4 placed objects), and **52 Town** "Peasant Human2 MaleB A", skin PEASANTM3A, DAT class `TownHuman2MaleA` (12). No other row
names the model. The skins are **two different men** on one body (A: blond, blue eyes, short full beard; B: dark wavy hair,
moustache and goatee) in the same tunic design recoloured (A wine-red velvet, B brown knit with a jewelled chain), with the
same breeches, boots and belt. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

**No duplicated body.** `meshcmp.py peasantm3:peasantm1,peasantm2,peasantm6,peasantm7,foraddarre,markel` (orchestrator's
script, 2026-11-02): torso p90 3.9-5.7 cm (42-75 % of vertices > 1.5 cm) against every built male body, arms 3.0-20 cm; only
the head is close to PeasantM7's (p90 0.8 cm). So a new body on the approved MM9 humanoid route.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm3.glb` (`tools/install_model.py --world mm9 --name mm9_peasantm3.glb` from `export/mm9_pm3.glb`); variants `pm3_a`, `pm3_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantm3_claude`: `MM9 45 Town` (`pm3_b`), `MM9 52 Town` (`pm3_a`); scale 100, `yaw_offset -1.570796327`, stride walk 1.1 / run 2.8 (`stride.py`: walk 0.95/1.36, run 1.85/3.67 per foot, the clips are PeasantM7's), look `Bip01 Neck, Bip01 Head`, impact 0.5 s (hattack1 `Rattack`, as PeasantM1) |
| Descriptors | rows 45 (legacy stand-in 361) and 52 (370) in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated (208 rows: 9045, 9052) |
| Triangles LOD0/1/2/3 | 10,650 / 5,323 / 1,913 / 634 (Smart Topology 14,759 -> 7,344 after reduction and MPFB hands; + 1,660 waist/boot lining faces, + 1,646 own-paint inner twins of the tunic shell and the skirt, see the see-through lesson) |
| Skeleton | PeasantM3 = PeasantMale, 45 joints, rest rotations unchanged, joints translated onto the HD body (`fit_rig.py`; Head joint move pinned to 1.6 cm, see Route); + 15 finger bones per side; mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps, `source/mm9_lib/pmale.glb`) | Standing stand1, Walking walk3, Running run, Fidget fidget4, Talk conv2, AttackMelee **hattack1**, Hit wince1, Death die1, Dead; script clip Cower (cower) |
| Textures | body 2K colour + 1K normal/ORM, region mask (R tunic, G nape skin, B breeches) + ramps per tier; head + hands set 2K colour + 1K normal/ORM with a **tier B head colour and normal** (`tier_head.py`); specular 0, metallic 0 |
| Meshy credits | **65 / 70** (r3: + head A 4K retexture 10, backup 2835 before; r5: + heads A and B 4K retextures 20);: Smart Topology 5, body 4K retexture 10, head A 4K retexture 10, head B 4K retexture 10 (backup account: 3050 at launch, 3045 / 3005 / 2985 before the paid jobs; other agents spend in parallel) |

## Collar faces on the body r8 (2026-11-02, orchestrator review of r7; 0 credits) - current
Review of r7: the gold painted into the head texture below the neckline read as a blotchy gold bib. The head faces below the
neckline curve now belong to the body material instead of being painted.
- **`head_to_body.py`** (on `work/neck_v2.blend` -> **`work/neck_v5.blend`, the build default**): the 128 head faces lying on or
  below neck_line.py's curve get head = 0 (body material). Faces straddling the curve stay head (skin). Geometry unchanged
  (they stay 4 mm behind the body collar where they overlap).
  - First try `MODE=nearest`: every corner took the body UV of the closest point on the body's collar/tunic surface
    (barycentric). The brocade came out as stretched zigzags (corners up to 43 mm from the body surface, neighbouring corners
    on different collar islands): dropped.
  - Used: **`MODE=panel ANCHOR_X=-0.075 ANCHOR_Z=0.32`**: a closed shirt front in the tunic's own velvet. The faces' (x, z)
    are mapped by one affine map, fitted on a large left-chest tunic island (329 faces) within 8 cm of the anchor, into that
    island: the weave keeps its own scale with no stretch, and the tier ramp recolours it (A wine red, B brown). The first anchor
    (right chest) overran its island at the panel's right edge (a beige patch).
- Paint: `NECKLINE=1 COLLAR_SKIN=1 R5=1 EYE_A="1.0 0 0 0 0" scripts/head_paint_pm3.sh` (head texels below the curve, on the
  straddling faces, are neck skin; no gold in the head texture).
- Sheet `review/sheet_neck_r8.png` (rows r6 A, r6 B, r8 A, r8 B; neck front close-up, 3/4, above, Talk), read zoomed: smooth
  round neckline, one skin tone on the throat, a velvet shirt front behind the collar opening down to the brooch, both tiers.
- Remaining: a faint vertical crease down the panel's middle (mesh shading); a few stretched velvet streaks where the panel
  turns sideways (3/4 view, upper left); a thin skin rim just under the neckline from the straddling faces.
- Gates: see-through on every clip (+ Running 12, `review/gates/see_through_r8/`): collar 6 px at worst, head 4, torso 9,
  sleeves 0-1, trousers 1-3, boots 0; arm/hand 0 frames > 1 cm, jitter 0, sleeve poke 0, detached 0, flat 0.00, winding 0;
  floor ok both; viewer 20 switches 0 failed; installed sha256 52fcf7133249..., `mm9_actor_models_build_every_binding` PASS
  (246 descriptors on 109 models).

## Throat and neckline r7 (2026-11-02, orchestrator review of r6; 0 credits)
Review of r6: lighter flat rectangles across the throat and a blocky stepped neckline.
- **Geometry** `neck_line.py work/mouth_v14.blend work/neck_v2.blend 0.668 7 0.009 0.004` -> **`work/neck_v2.blend`, the build
  default** (replaces neck_tuck.py's `neck_v1`): the neckline curve = the body collar's top per 10 degrees, smoothed over 7 bins,
  never below 0.668 m at the front; the nearer endpoint of every head edge crossing it snaps onto it (27 vertices), head
  vertices below it that lie over the body collar move 4 mm behind it. Tried and dropped: trimming the apron below the curve
  (`TRIM=1`, `neck_v4`): the body set does not close the throat, the front view then looked into the inside back of the tunic;
  `throat_smooth.py` (the throat above the new neckline is too short: 4 vertices, one moved 12.6 mm); `body_neckline_paint.py`
  (kept in scripts, not in the build; its backup restored).
- **Paint** `NECKLINE=1 R5=1 EYE_A="1.0 0 0 0 0" scripts/head_paint_pm3.sh`: head texels above the curve are the neck's skin
  function (one continuous tone); below it the gold of the nearest body-collar texel (gold only: blue < 0.25 x red, the body's
  skin had passed the old saturation test and drew a skin stripe), blur 4, with the head paint's weave as faint detail; the
  head normal map flattened evenly below the jaw line, gutters taking their nearest island texel's weight (the pale island
  outlines).
- Viewer: `scripts/neck_shots.sh`, sheet `review/sheet_neck_r7.png` (rows r6 A, r6 B, r7 A, r7 B; neck front close-up, 3/4,
  above, Talk), read zoomed: one skin tone over the throat, no rectangles or outlines, a smooth round neckline on both tiers.
- Remaining: the gold below the neckline is a plain streaky gold, not the collar's brocade pattern (the head set's layout
  cannot carry the body's pattern); seen from above it reads as a gold bib down to the brooch.
- Gates: see-through (Standing, Talk, Fidget, Death, Dead; `review/gates/see_through_r7/`) collar 6 px at worst (r6: 2), head 4,
  sleeves 0-1, trousers 1-3; arm/hand 0 frames > 1 cm, jitter 0, detached 0, flat 0.00, winding 0; floor ok both; viewer 20
  switches 0 failed; installed sha256 7bff04c93774..., `mm9_actor_models_build_every_binding` PASS (246 descriptors on 109
  models).

## Neck/collar fix r6 (2026-11-02, user note "peasantm3 - some artifacts here?"; 0 credits)
Torn gold and skin shards where the neck meets the collar, both tiers. Source (per-material render
`review/face_r2/neck_parts.png`): head_split.py's level cut gave the head set a flat diamond apron of the shell's chest faces down
to the brooch, with the body's collar faces lying just over it (z-fighting), and fix_neck_pm3.py had painted that apron as a gold
collar band, so it read as gold shards beside the real collar; head flaps also flared over the collar at both sides. There is
no neck cap and no collar lining on this model (the neck is one shell with the tunic; linings_pm3.sh lines waist and boots).
- **Geometry** `neck_tuck.py work/mouth_v14.blend work/neck_v1.blend 0.002 0.003 0.025 0.015` -> **`work/neck_v1.blend`, the
  build default** (positions only): per 10-degree angle the body collar's top and inner rim radius are measured; every head-set
  vertex below the collar top (+3 mm) moves in to a tube 2 mm inside the collar's inner rim (or the neck radius, the larger),
  at most 2.5 cm down: the apron ends hidden under the collar with no gap to look into. Tried and dropped: a tube 4 mm inside the
  neck radius (left a slit along the neckline in side views, see-through collar 9 px in 131 frames) and pulling flaring
  vertices up to 3.5 cm above the collar (moved jaw-side vertices and the Fidget right forearm read 5.9 cm in the body).
- **Paint** `COLLAR_SKIN=1` in `fix_neck_pm3.py`: the head-set texels below the collar line (the throat in the collar's V
  opening) take the neck's skin tone instead of the gold remap, with a coverage-normalised blend (island borders had kept old
  paint as pale seam lines). Run as `COLLAR_SKIN=1 R5=1 EYE_A="1.0 0 0 0 0" scripts/head_paint_pm3.sh`.
- Viewer check `scripts/neck_shots.sh` (front close-up of the neck, 3/4, above, Talk 2.2 s, Fidget 1.8 s, both tiers): sheet
  `review/sheet_neck_r6.png` (rows: before A, before B, after A, after B), read zoomed. Remaining: the skin opening's edge
  against the collar is blocky in front (a small step at the character's right), faint lighter flat facets in the throat skin.
- Gates: see-through on Standing, Talk, Fidget, Hit, Death, Dead, Cower (`review/gates/see_through_r6b/`): collar 2 px at worst
  (single slivers), head 4, torso 9 (as r3); arm/hand 0 frames > 1 cm (incl. Fidget R forearm 0), jitter 0, sleeve poke rest 0,
  detached 0, flat 0.00, winding 0; floor ok both; viewer 20 switches 0 failed; installed sha256 9b98c069e4ea...,
  `mm9_actor_models_build_every_binding` PASS (244 descriptors on 107 models).

## Final mouth geometry + fresh head paints r5 (2026-11-02, orchestrator review of r4; 20 credits)
The r4 mouth still read wrong (A lopsided and smeared red, B a red smudge under the moustache): the paints were made for the old
open mouth and every geometric close left paint and geometry disagreeing. So: geometry final first, then both heads repainted.
- **Geometry** (`lip_edge.py`, on `work/mouth_v13.blend` with `mouth_v7.blend` as the before-close reference) ->
  **`work/mouth_v14.blend`, the build default and final**: the groove vertices (75) and the lip-edge vertices (upper 18, lower
  28) fitted to symmetric even polynomials about the midline (x0 -0.003) for height and depth; groove at the mid curve 1.2 mm
  behind the lips, edges 0.4 mm either side: one smooth, symmetric, slightly upturned closed line. Moves faded out beyond
  |u| 2.2 cm and capped at 3 mm (a first try without the cap pulled a corner vertex 26 mm into a sliver). Clay check
  `review/face_r2/clay_mouth_v14.png` (front, 3/4, profile, below; before `clay_mouth_v13.png`). No geometry moved after this.
- **Head masters** (Codex, `scripts/codex_head_r5.sh a|b`, `references_head_r5a/`, `references_head_r5b/`): from viewer renders of
  the current head on v14 + MM9 skin A / B + the previous HD fronts; calm, open eyes, closed symmetric relaxed mouth on the
  geometry's line. Accepted first returns.
- **Meshy** 4K head retextures `head_a_retexture_r5`, `head_b_retexture_r5` (10 + 10; backup 2560 / 2550 before) on
  `texturing/pm3_head_upload_r5.glb` (v14, frozen layout). r4 head maps kept in `work/head_r4/`.
- **Post-paint chain** `R5=1 EYE_A="1.0 0 0 0 0" scripts/head_paint_pm3.sh`: beard-to-neck fade and collar line
  (`fix_neck_pm3.py`), hair rim (`fringe_fix.py`), no eye warp (the fresh paint is calm), `face_fix_r3.py` on both tiers (nose
  underside to skin, nostril holes lifted to soft shadows, red/pale lower lids, under-eye facet toning; the r4 lip-band and
  lip-line edits off), ears as skin (1-texel rim on both), no mouth-slot paint, hands, pad.
- Sheet read zoomed: `review/sheet_faces_r5.png` (viewer lighting; per tier MM9, r4 and r5 x front close-up, 3/4, true
  profile, low 3/4, party, 128 px) and front / 3/4 zooms of both tiers.
- Remaining marks: A - the narrow eye openings in the mesh read a little intent close up; a small pale crescent under the left
  eye and light patches below the inner eye corners (lit mesh facets); faint redness on the lower lids. B - the hairline is a
  stepped edge at the temples (the hair shell's mesh edge). Both - lips, nostrils, neck, collar and ears clean.
- Gates: arm/hand 0 frames > 1 cm, jitter 0, detached 0, flat 0.00, winding 0; floor ok both; viewer 20 switches 0 failed;
  installed sha256 9a8426a489e8..., `mm9_actor_models_build_every_binding` PASS (230 descriptors on 101 models).
  Meshy total **65 / 70** credits (cap raised to 70 for this model).

## Lip fix r4 (2026-11-02, user note "part of lip missing?", `review/user_notes/lip_missing_front_a.png`; 0 credits)
- **Cause** (unlit renders of the master before and after the r3 mouth close, `review/face_r2/albedo_mouth_mouth_v7/v8.png`):
  r3's `mouth_close_pm3.py` took the "lip front" from vertices within 3 mm in height, so the upper lip's overhang made part of
  one half of the lower lip count as pocket and moved it, uncovering a skin-painted wall: a lopsided lip with a chunk
  missing. The paint itself is symmetric.
- **Fix** from `work/mouth_v7.blend` (r3 paint, caps with a lip texel): `mouth_close_pm3.py squeeze=0 groove=0.0015
  deep=0.0015 dz=0.0015 rim=0` -> **`work/mouth_v13.blend`, the build default**: the lip front is taken at the SAME height
  (+-1.5 mm); every mouth-interior vertex more than 1.5 mm behind it (75) comes forward to 1.5 mm behind it, heights
  unchanged; lip front surfaces untouched. The opening becomes a shallow groove (no dark cavity, no jagged sawtooth teeth).
  Tried and dropped: partial and full lip-edge closes (rim 0.5/0.85/1.0, a jagged slit stayed), a 1D regularisation of the
  meeting-line vertices (still a cavity), painting the groove by depth (curvature put the moustache in the band).
- **Paint** (`face_fix_r3.py`, A): the pale skin band under the lower lip takes the beard paint 1.2 cm lower (soft edge);
  painted nostril holes lifted to >= 0.62 x cheek (the cavities' shading makes small soft shadows); the lip line's
  downward-facing faces lightened toward the lip colour (both tiers); the lit triangles under both eyes toned by the surface
  facing up more than its surroundings (smoothed; both tiers; a first unsmoothed try traced the flat facets as lines). B
  otherwise keeps its paint (A-only gating of the nose and lid steps).
- Sheet read zoomed: `review/sheet_faces_r4.png` (viewer lighting, per tier MM9, r3 and after x front close-up, 3/4, true
  profile, low 3/4, party, 128 px), plus front/low zooms of both tiers next to the user's shot.
- Gates: arm/hand 0 frames > 1 cm, jitter 0, detached 0, flat 0.00, winding 0; floor ok both; viewer 20 switches 0 failed;
  installed sha256 187426f182f8..., `mm9_actor_models_build_every_binding` PASS (230 descriptors on 101 models).
- Remaining: the lips meet on a slightly wavy line at the centre (both tiers, from the mesh's lip edges); narrow eye slits in
  the mesh read a little intent close up; nostrils are soft geometric shadows.

## Head repaint r3 (2026-11-02, orchestrator review of r2: repaint tier A fresh; 10 credits)
Review of r2: A's pale golden brows read as painted bands, the lips pursed and parted with a pale inner area, the nostrils a
dark blob; A's second patch pass, so a fresh head paint. B kept (its head colour/normal untouched).
- **Codex head masters** `references_head_a2/` (`codex_head_a2.sh`, brief there): from viewer renders of the CURRENT head
  (`viewer_head_a.png`: shape, hair silhouette, framing) + MM9 skin A + the earlier approved front bust; calm open eyes,
  natural fine-haired blond brows, closed relaxed mouth, small nostrils. Accepted first returns.
- **Meshy** 4K head retexture `head_a_retexture_r3` on the current head mesh with its frozen layout (`head_upload_v2.py`:
  the master's HeadUV / 0.8, no re-unwrap; loose lip piece already gone) - 10 credits (backup 2835 before). Composed with
  `compose_headhand.py`; r2 head A maps kept in `work/head_a_r2/`.
- **Paint on the geometry** (`head_paint_pm3.sh`): fix_neck (beard-to-neck fade, collar line) -> fringe -> eye_open (A, mild:
  opening x1.15, no brow lift or lightening) -> **`face_fix_r3.py`** (A: nose underside and the grey columella patch to skin,
  red alar rims to the cheek hue, red lower-lid rims, a lit fold under the left eye 8 % darker) -> ear_skin (rim dilation
  only on B) -> mouth_slot_paint (recess walls lip-coloured, darker only at the deepest part) -> hands -> pad.
- **Mouth geometry** (positions only; the lips' front surface untouched): the one-texel caps now take the lip front's texel
  (`mouth_hole_fan.py`; the rim texel was dark) -> `work/mouth_v7.blend`; the opening between the lips closed:
  `mouth_close_pm3.py squeeze=1 groove=0.002 deep=0.002 rim=0.6` - the pocket (94 vertices > 2 mm behind the lips) collapses
  to mid-height 2 mm behind them and the inner lip edges (39 vertices) move 60 % toward it, so the lips meet on one line
  (PeasantM2d's approved mouth fix; no smoothing, no normal change) -> **`work/mouth_v8.blend`, the build default**. Shared
  geometry: B's mouth closes the same way.
- The painted nose already sat on the geometry's nose (albedo render `review/face_r2/a_albedo_eyes.png`), so
  `warp_nose_pf1.py` was not needed; the dark nostril look was red/grey paint plus the cavities' shading.
- Sheet read zoomed: `review/sheet_faces_r3.png` (viewer lighting; per tier MM9 front / 3/4 / profile, r2 and r3 x front
  close-up, 3/4, true profile, low 3/4, party, 128 px); zooms of front and low 3/4 both tiers.
- Remaining marks (A): the eye openings are narrow slits in the mesh with deep upper-lid creases (shared with B), so in the
  viewer's top light the eyes still read a little intent close up (the albedo is calm); the nostrils are soft dark shadows of
  the geometry's holes; the upper lip is thin under the moustache; a faint lit fold under the left eye; small faceted
  highlights on the lower-lid geometry. B: unchanged apart from the closed mouth line.
- Gates: arm/hand 0 frames > 1 cm, jitter 0, detached 0, flat 0.00, winding 0; floor ok both; viewer 20 switches 0 failed;
  installed sha256 09b78ef27b11..., `mm9_actor_models_build_every_binding` PASS (216 descriptors on 93 models). Not rerun:
  see-through (mouth closure only shrinks an opening), sleeve poke, full actors suite. Meshy total: **45 / 50 credits**.

## Face pass r2 (2026-11-02, orchestrator review of tier A; 0 credits)
Review: A glared (heavy low brows, squint), a pale band between the lips (second lip / open slot), the beard ended on a hard
line above a lighter neck band with a jagged lower edge at the collar; check B for the same. Rule kept (Wyrde lesson): no
geometry smoothing, normal relaxing or normal-map flattening over the nose or mouth; paint on the geometry, delete only truly
loose pieces. Installed `mm9_peasantm3.glb` sha256 d77da6883f22... (r1 was 006f55c95d88...; no copy of the r1 GLB was kept,
but its master `work/linings_v3.blend` and the `_preneck` head backups rebuild it).
- **Mouth (both tiers)**: Meshy's lips were a LOOSE 40-vertex piece floating in front of the face shell (z 0.742; the boys' and
  PeasantM2d's cause): deleted (`loose_parts.py ... 40 0.045` -> `work/mouth_v1.blend`). Behind it the shell's mouth pocket runs
  2-3 cm back (`mouth_probe.py`) with two openings (31 and 7 edges, 1.5 cm behind the lips): capped where they are with
  one-texel fans (`mouth_hole_fan.py`: every cap corner takes one rim UV; a first try with mixed-island UVs spanned the atlas
  and painted a dark rectangle over the moustache) -> **`work/mouth_v6.blend`, the build default**. No vertex of the lips or
  pocket moved: closing the pocket geometrically (`mouth_close_pm3.py`) gave a pout with a hole and was dropped. Paint:
  `mouth_slot_paint.py` - the pocket walls (deeper than 6 mm behind the lips' local front, or deeper than 2 mm on a surface not
  facing forward) take the tier's lip colour x 0.6, so the lips meet on one soft dark line.
- **Eyes (A)**: paint only (`eye_open_pm3.py`, sampled on the face surface in 3D): the painted opening x1.4 about the iris
  line, brows lifted 4 mm (8 mm at the inner ends, which dipped into a frown), the brows lightened toward golden blond, the
  upper-lid crease and the under-brow band lightened toward the cheek, reddish lower-lid rims moved to the cheek hue. A
  geometric socket relax (`eye_relax.py`) bulged one eye and was dropped.
- **Under the jaw (both tiers)**: `fix_neck_pm3.py` r2 - beard to neck by a 3D gradient (from 6 mm above the jaw line on A,
  2 mm on B, to 14 mm below) instead of a 2-texel edge; neck tone x0.90 at the jaw to x0.82 at the collar (r1 x0.97 read as a
  lighter band); one smooth collar line all round the neck 4 mm above the body set's top at each angle, so the jagged
  head/body seam lies inside the gold; the collar band = the nearest body-yoke colour (softened) with little pattern; the head
  normal map flattened only under that band and the neck (not the face). Body nape strip ramp flatter (`tier_pm3.py`).
- **Ears (both tiers)**: in viewer light they poked out of the hair painted in hair colour. `ear_skin_pm3.py`: face-shell
  texels standing > 7 mm out of the skull (the smallest |x| within +-1 cm) are ear; their hair-coloured texels take the local
  skin colour round them; B's sideburns on the skull stay hair.
- Chain: `head_paint_pm3.sh` (fix_neck -> fringe -> eye_open (A) -> ear_skin -> mouth_slot_paint -> hand_clean -> pad), every
  step under `systemd-run --user --scope -p MemoryMax=12G -p MemorySwapMax=0`.
- Sheet read zoomed: `review/sheet_faces_r2.png` (viewer lighting, `scripts/face_shots.sh`: per tier MM9 front / 3/4 /
  profile, before and after x front close-up, 3/4, true profile, low 3/4, party view, 128 px).
- Gates after: arm/hand 0 frames > 1 cm, jitter 0, detached 0, flat 0.00, winding 0, head set 40.5 %; floor ok both;
  viewer 20 switches 0 failed; `mm9_actor_models_build_every_binding` PASS (216 descriptors on 93 models). Not rerun: the
  see-through gate (only the mouth caps changed, closing openings), sleeve poke (hands unchanged), the full actors suite.
- Left: A's lids still carry a little dark lash shading (reads intent close up, calm at party distance); B's ear roots are a
  little patchy; the collar band under the chin is plain gold.

## Clips the MM9 scripts play
`scripts/dat_objects.py "^Town(Human|Human2)MaleA$"`: 7 objects without a script (row default NPCbase.scr -> npcBase.inc ->
BaseRun.inc `LoopAnim Cower`), NPC183/186/195.scr, Pledge.scr, retainer.scr, HucksterMod.scr (x2), BoatJudge.scr,
shopkeeper.scr: none names an animation (shopkeeper's `LoopAnim Params` is commented out; NPC183/195 take P1 from empty
ScriptParams); no map marker carries PlayAnim/LoopAnim. So the MM9 roles plus Cower only (`roles_pm3.json`). `stand` is
bound to Standing as on the sibling bodies.

## Route (scripts/, repo root unless noted)
0. `convert_sources.sh`; `ref_renders.py` (skins A and B, body and head) -> `references_hd/mm9/`, sheets
   `references_hd/mm9_views_{a,b}.png`, `mm9_head_views_{a,b}.png`, `mm9_skin_x4_{a,b}.png`.
1. HD masters (Codex via `codex_slot.sh`): `codex_masters.sh 1|2` (design = skin A, 12 of 16 placements; brief
   `references_hd/CODEX_BRIEF.md`, calm warm expression), `clean_alpha.py`; head turnarounds `codex_head.sh a` and `b`
   (B: the dark-haired man on A's head silhouette, `references_head_b/`).
2. Meshy Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
3. `fit_rig.py` + `fit_config.json` (NEW option `centre_move_cm`: the front-surface measure put the Head joint 5 cm back,
   18 cm behind the face front; pinned to PeasantM7's 1.6 cm, the same MM9 head mesh within 0.8 cm; `centre_interp` Spine3
   as PeasantM7) -> `reduce_uv.py` -> `graft_hands.py graft_pm3.json` (hands 0.199 / 0.193 m, MM9 0.21) ->
   `head_split.py head_pm3.json` (neck cut 0.62, span part 2) -> `eye_fill.py 8,11` + `loose_parts.py 45 0.035` (eyeball
   cups dropped before the paint, as PeasantDM2) + `fill_holes.py 5` -> `work/eyes_v1.blend`.
4. UVs `uv_pass.sh` (body atlas 62.2 %, head 57.8 %). **Never re-run**: the paid paints belong to these layouts.
5. Paints: `requests/retexture_body_tp.json`, `retexture_head_tp.json`, `retexture_head_b_tp.json` (4K);
   `bake_ao_texpass.py`, `compose_texpass.py`, gentle grade (`grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5
   --contrast 1.06 --saturation 1.15`), `bake_hands.py` (young caucasian male), `compose_headhand.py pm3_tp|pm3b_tp ...
   --ref-head --hand-gain 1.12`, `sleeve_paint_fix.py work/pm3_body_tex.glb` (5,505 skin texels on the cuffs).
6. Geometry on the painted master (positions/faces/weights only): `sleeve_tuck.py 0.75 0.003 1` -> `cuff_trim.py 0.01`
   (nothing to trim) -> **`face_rigid_pm3.py`** -> `work/rigid_v1.blend` -> **`linings_pm3.sh`** (waist rims, boot
   rims) -> `work/linings_v1.blend` -> **`twin_shell.py`** (inner twin of the tunic shell) -> `work/linings_v2.blend` ->
   `twin_shell.py ... rank=2 zmin=-0.06` (the skirt part of the skirt+breeches piece) -> **`work/linings_v3.blend`** (the
   build default).
7. Head paint chain `head_paint_pm3.sh` (project folder; re-runnable from the `_preneck` backups): `fix_neck_pm3.py` ->
   `fringe_fix.py pm3_tp`, `RIM_K=2.4 fringe_fix.py pm3b_tp` -> `hand_clean.py` (HAND_REF A 205,122,90; B 220,148,112) ->
   `pad_head.py`. Body: `tier_pm3.py work/pm3_body_tex_unlined.glb` (the textured export of `work/rigid_v1.blend`: the
   own-paint twins share their faces' UVs and would overwrite the piece and island rasters) -> `breeches_tone.py
   work/pm3_body_tex_unlined.glb` (the breeches' top band toned down to the lower legs' brightness, gain 0.79) ->
   `tier_pm3.py` again.
8. Runtime `TOKEN=<lease> scripts/build_runtime_pm3.sh [--install]` (project folder): textured export -> `clips_mm9.py`
   (soft offsets) -> **`finger_pose.py`** -> `hand_rest.py` (`hand_rest_pm3.txt`: Fidget, Talk) -> prepare -> LODs ->
   `shrink_shadow_lods.py` (PeasantDM2's: shadow meshes drop the one-texel linings; NEW `DROP_LINING_LODS=3` drops them from
   LOD3 too: decimated, the boot lining folded into an inverted 18-triangle shell) -> `region_variants.py` -> `tier_head.py
   PeasantM3Head pm3_b=pm3b_tp` -> extras -> `floor_fix.py` (`floor_ops.txt`) -> `mirror_glb.py` -> winding. Viewer:
   `viewer_tiers.py`, `make_viewer_manifest.py <rev> ...` (see `retier.sh`).
9. Binding (repo root): `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_peasantm3_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`, then `level_generation/projects/mm9r_common/review_root.py`.

## 2026-11-02 lessons (VARIANTS_BRIEF), how each was met
- **Rigid head** (`face_rigid_pm3.py`, after Kira's): the head-set skin at z 0.69-0.72 (chin, jaw, lower lip) carried 35-65 %
  Neck from the fit's diffused MM9 labels. A jaw-following boundary (throat corner y -0.035 z 0.676, rising 0.45 per m to the
  nape, +1.2 x^2 to the jaw angles; `jaw_profile.py`, `face_weights_probe.py`) and Head share = max(boundary t, current):
  lower face 241 vertices, Head weight min 1.00.
- **Faces** (pre-screen against MM9, `review/sheet_faces_vs_mm9.png`, `review/face_a.png`, `review/face_b.png`): one pair of
  nostrils on the geometry's nose, one lip pair (no pink plate), no lower-lid crescent, one brow, no eye-plate band, eyes open
  with irises (A blue, B brown), calm. Fixed: the head retextures painted the turnarounds' collar on the neck (gold brocade, A
  also red velvet) and a saturated gold bead line under the chin -> `fix_neck_pm3.py`: neck below the jaw line = the tier's
  own cheek skin darkened toward the collar; the head set's lowest faces in front (the flare into the V gap of the body's
  brocade yoke, below z 0.668) = the original paint's brocade band, re-mapped by angle and height and colour-transferred to
  the body yoke; saturated gold under the chin -> skin. Tier B's hair shell rim was skin-speckled at the nape ->
  `fringe_fix.py` (RIM_K 2.4: 1.45 also took B's brown highlights).
- **See-through** (`see_through_gate.py`, every 3rd 30 fps frame + Running 12, 8 azimuths x level / 20 deg down):
  see "Checks". Linings at the waist (5 loops: tunic shell bottom, skirt top, belt) and the boot/breeches rims; no neck cap
  (the neck is one shell with the tunic); the sleeves have no open rim (the hand graft joined the cuffs); the remaining holes
  were the tunic shell folding inside-out at the flank (Cower) and the chest opening in Death -> own-paint inner twin of the
  whole tunic shell (`twin_shell.py`, 1.5 mm, capped at 40 % of the gap behind).
- **Hands**: `finger_pose.py` (Kira's) with a NEW two-joint mitten path: PeasantMale has no Finger12, its bone axis is +X
  (Kira's -X), its bind mitten is nearly flat (no curl axis) and its clips turn Finger11 about mixed axes, so flexion is
  measured unsigned (MCP hand axis -> Finger1 segment, PIP segment -> Finger11 axis): relaxed curled fingers standing, MM9's
  fist in AttackMelee/Running. Wrists: `sleeve_tuck.py`, no hollow cuffs end-on (`review/poke_check.png`).
- **Ears**: `ear_views.py` both tiers (`review/sheet_ears.png`, `review/sheet_ears_necks.png`): the ears sit under the hair as
  in MM9, lobes clean skin, no foreign texels; nape strip tone matched per tier (region G).
- **Sleeve poke**: see "Checks".

## Tiers (`tier_pm3.py`)
Shared body paint = skin A (row 52, 12 of 16 placements). Measured on the MM9 skins: breeches, boots and belt are the same art
and colour in both; the tunic changes (A 93,33,23 -> B 66,32,21 mean); the brocade bands only ~20 % duller on B.
- R tunic (hue/value classes on the two pieces that carry the tunic: the torso+sleeve shell and the skirt part of the
  skirt+breeches piece above 0.82 m; gold sheen specks in the velvet included): B = MM9 skin B's colour at the texel's
  luminance quantile x our / MM9-A luminance. Fit (8-bit mean / p95): A 2.74 / 7.04, B 0.35 / 0.68.
- G nape skin (the body set's strip of neck skin below the head-set cut): each tier's own head-set neck tone (fix 0.23 / 0.27).
- B breeches (both tiers): the 4K paint made them bright gold-ochre; MM9's are dark brown with a gold weave in both skins ->
  MM9's colour at each luminance quantile x our weave (fit 1.55 / 4.24). The breeches are one Meshy piece with the tunic
  skirt and xatlas charts cross the hem: breeches = that piece below 0.81 m, whole islands without tunic red, and on mixed
  islands the non-red texels below that island's lowest red that are not hem brocade (no bright orange-red within 3
  texels); the weave painted on the skirt's lower/inner faces near the hem too. `breeches_tone.py` darkens the top band
  first (the ramp keeps the paint's brightness order). Checked with the mask rendered on the model
  (`review/maskdbg_backlow.png`) and in Running/Walking (`review/sheet_breeches.png`).
- Brocade bands are no region (a luminance ramp cannot keep A's red zigzags on gold: 10 / 36 levels).
- Heads: one head colour + normal per tier (`tier_head.py`), the hands in the same set (one clean skin tone per tier).

## Checks (final build, LOD0 10,650 triangles; installed sha256 006f55c95d88...)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, all 10 clips, 48 fps) | **0 frames > 1 cm, hands and forearms, both sides, every clip**. Finger stretch p99 <= 1.62; wrist max 119 deg (Death/Dead R: MM9's limp death hand). hattack2 (PeasantM7's AttackMelee) put the punching elbow 5-6 cm into this fuller tunic; the least upper-arm turn that cleared it (`arm_clear.py`) jittered 5-8 deg/frame at the punch, so AttackMelee is hattack1 (0 cm, untouched) |
| Jitter (`jitter_gate.py` vs MM9's clips) | **0 fails** |
| Sleeve poke (`sleeve_poke_gate.py`, PeasantDM2's) | rest **0 mm** both sides; 0 in Standing, Walking, Talk, Cower; 1-2 vertices flagged in bent wrists (Running, Fidget, AttackMelee, Hit, Death, Dead; 9.9-32.3 mm): **checked with the vertices marked** (`render_poke.py` -> `review/poke_check.png`, four views of each worst frame): every mark sits on visible wrist skin just past the cuff rim; no skin shows through any sleeve (the gate's perpendicular ray meets the cuff's far wall when the wrist folds, as PeasantDM2) |
| See-through | see the table below |
| Floor (`floor_audit.py --world mm9`) | `MM9 45 Town` and `MM9 52 Town` ok: stand 0.0, walk -0.2..+2.4, living -0.2, dead 0.0 |
| Winding | 0 inverted closed parts (LOD3 lining shell fixed) |
| Detached | 0 detached in any pose (17 components) |
| Flat shading | 0.00 on both materials |
| Bones | L thigh 11-13 % (MM9's own hip slide, as PeasantM7/Annud) |
| Texture quality | body atlas **61.2 %** (layout before the linings: density p10/p50/p90 1459/1495/1527, spread 1.05, fragments 0.1 %, stretch 1.09; the one-texel linings and own-paint twins make the spread read as unbounded and the uv sum over 80 %); head set 40.6 % of 2K (head square 57.8 % from the UV pass; hands half density by design, as PeasantM7's 41.2 %), spread 2.87, fragments 2.8 %, stretch 1.37 |
| Viewer (`run_creature_review.py check`) | 20 tier/clip switches, 0 failed, 0 console errors |
| Regression | final install: `mm9_actor_models_build_every_binding` **PASS** (214 descriptors on 92 models, 0 failed); full `actors` suite on the geometry-final install: **passed 192, failed 1** (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"), `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 / 185); logs `review/gates/regression_binding.log`, `regression_actors.log` |

See-through (`see_through_gate.py`, every 3rd 30 fps frame of all 10 clips + Running 12, 8 azimuths x level / 20 deg down,
3 mm pixels; worst background pixels per zone; `review/gates/see_through_r0..r3/`):

| Zone | r0 unlined | r1 waist + boot linings | r2 + tunic-shell twin | r3 + skirt twin (final) |
|---|---|---|---|---|
| torso (waist, flank, skirt) | 317 (Cower) | 231 | 47 (Death 18) | **9** (Hit 6) |
| collar | 168 (Death 18) | 168 | 1 | **1** |
| sleeve R / L | 121 / 12 (Death 18; the waist hole attributed to a sleeve face) | 121 / 12 | 0 / 1 | **0 / 1** |
| boot L / R | 28 / 25 | 0 / 0 | 0 / 0 | **0 / 0** |
| trousers L / R | 38 / 9 (corpse) | 23 / 4 | 23 / 4 | **1 / 3** |
| head (mouth corner, not cloth) | 4 | 4 | 4 | 4 |

The remaining pixels are single slivers at silhouette edges (`hole_probe.py` traced the r1/r2 holes: the flank folding
inside-out in Cower, the chest opening in Death 18, the waist in the corpse).

Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm3_claude/review/viewer/index.html` (tiers pm3_a,
pm3_b; three.js has no region ramps, so `viewer_tiers.py` bakes each tier's ramps into its own viewer GLB).

Sheets read: `review/sheet_mm9_vs_ours.png` (MM9 renders mirrored to game handedness vs viewer shots, both tiers, front /
three-quarter / back / side), `review/sheet_faces_vs_mm9.png`, `review/face_a.png`, `review/face_b.png` (Blender close-ups:
front, three-quarter, eyes, mouth, both sides), `review/sheet_ears.png`, `review/sheet_ears_necks.png`,
`review/neck_front_v2.png`, `review/sheet_clips_a.png`, `review/sheet_clips_b.png`, `review/sheet_hands.png`,
`review/poke_check.png`, `review/attack_forearm.png` (hattack2's elbow), `review/sheet_breeches.png`,
`review/maskdbg_backlow.png`, `review/sheet_final_a.png`, the see-through worst-case images.

## Binding plan (map placement)
The rebuilt maps place these townsfolk with the legacy stand-in ids (361 for `TownHumanMaleA`, 370 for `TownHuman2MaleA`)
through `transcode_mm9_dat_to_odm.py`, so the new descriptors do not show in game yet. Per the brief this switch is the
orchestrator's, once for every row after the batch: placements of those two DAT classes should use 9045 / 9052. No
transcoder or map change here.

## Deviations and open points
- Tier B has no jewelled chain necklace (MM9 skin B): the body paint is shared, and a chain painted for B would show on A.
- The brocade bands keep A's orange-gold on B (B's are ~20 % duller in MM9).
- The front collar under the chin is a re-mapped band from the head paint: slightly streaky in close-ups (under the beard).
- The inside of the tunic's side slits shows the paint's bright gold breeches weave (not in the breeches region).
- A's expression reads a little intent around the eyes in front close-ups (the Codex masters are calm); the ears' lobes show
  under the hair edge (MM9's hair covers them).
- Not looked at in game (descriptors not placed yet); LOD1-3 and shadow meshes not looked at; motion judged on viewer stills,
  gates and strips, not watched at speed; sounds; Android cook.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantm3_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm3_reduce_claude/before/`.
