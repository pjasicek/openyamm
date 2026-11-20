# MM9 PeasantF3, the young townswoman with a veil and braids (mm9_peasantf3) — 3D actor on the approved PeasantF1 body, 2026-11-02

MM9 `PEASANTF3.abc` with skins `PeasantF3a` and `PeasantF3b`. `MONSTERS.txt` rows on this model: **40** Shopkeeper "Peasant Human2
FemaleC A" (F3a; DAT class `ShopkeeperHuman2FemaleA`, 8 objects: NPC181.scr, NPC182.scr, Shopkeeper.scr, retainer.scr, 4 with the row's
NPCbase.scr) and **35** Prisoner "Peasant Human1 FemaleD A" (F3b; no DAT placement in the rebuilt maps). Built as a shared-mesh variant
(`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`): the approved PeasantF1 body, rig, weights and clips (`../mm9_peasantf1_claude/`, read
only; this project started as a copy of its sources) with F3's veil and braids added and its own paint. Own GLB `mm9_peasantf3.glb`,
tiers `pf3_a` (row 40) and `pf3_b` (row 35).

## Fifth pass (user review in the viewer, 2026-11-02, p5r14) - current

User, viewer front close-up of tier A: "eyes, what are these black things", "nose - is that supposed to be a nose", "texture splotches
next to the nose", "black stuff on her upper lip". The projected Codex face of passes 1-4 was dropped; the head is repainted fresh on
its current mesh and UVs and judged only in the review viewer at the user's zoom (the project's `review.js` head focus is
`[0, 1.60, 0.02, 0.42]`). 20 Meshy credits (two head retextures at 10; the shared backup account reads 2755 after the pass, above the 1740 floor).
- **Geometry check in clay** (`scripts/head_closeups_diag.py`, `review/pass5/geo_check.png`): nose, lips and chin forms intact (pass 3);
  the socket shell round each eye is crumpled at the lid edges and the eyeballs are low-poly spheres.
- **Paint**: Codex HD head masters per tier (front, 3/4, profile, back) painted over viewer-lit renders of the current head with MM9 F3a /
  F3b as reference (`references_head_p5/`, brief `CODEX_BRIEF.md`; calm, warm, young, no make-up), then one Meshy 4K retexture per
  tier on the current head mesh and UVs (`requests/retexture_pf3_head_p5_{a,b}.json`, upload `texturing/pf3_head_upload_p5.glb`) ->
  `textures/pf_head_p5{a,b}_raw|normal|rough.png` by `compose_pf.py`. Tier B's braids come from A's plaits recoloured dark brown
  (`scripts/braid_b_pf3.py`; Meshy painted them flat black). Rebuild: `scripts/rebuild_f3_p5.sh <rev>` (under the memory cap).
- **Face fixes after the paint** (F1's order where they apply): `head_fix_pf3.py` with `FRESH=1` keeps only the eye-rim, ear-speck, neck
  and veil-edge steps (no lip, teeth or dark-lip-line paint; no veil dirt cleanup, which made B's cream veil patchy);
  `skin_harmonize_pf3.py` / `hood_edge_pf3.py` are off (`P5_HARMONIZE=1` restores them; on the fresh paint they turned the blonde temple
  hair into skin). New `scripts/eye_lip_clean_pf3.py`: lower-lid band and the eyeballs' lower part / rim to cheek skin, the mouth's and
  nose's midline strips (own thin UV islands painted skin and cream) from the texels beside them, lip-line and nasolabial lines softened.
- **What the viewer showed and why** (each traced with a viewer-only test GLB: no normal map, unlit emissive, UV-coded texture,
  roughness 1, per-material and per-piece tints):
  - *dark wedges under the eyes*: not paint (unlit render clean) and not the normal map; the eyeballs' lower halves show below the jagged
    lower-lid edge and their sphere normals face down, so the viewer's lights from above and the hemisphere's dark ground darkened them.
    `build_glb_pf.py`: each eyeball takes the mean normal of the face shell round its eye (20 % of its own kept); the socket disc's normals
    are relaxed as well.
  - *pale glint on the lower lip*: 293 collapsed slivers (closed lip slit, small holes), a fraction of a millimetre in 3D, whose corners
    sit in different UV islands, so across them the texture ran over the gutters. New `scripts/uv_sliver_fix_pf3.py` gives each its own
    rows on one texel (the corner with the median luminance); +879 rows, LOD0 unchanged at 14,982 triangles.
  - *dark lip parting*: the upper lip faces down into the lip line: the mouth zone's normals lean toward the face's forward direction.
  - midline normals lose their sideways component (fins snapped onto the symmetry plane); gutters between head UV islands take their
    island edge's colour (`scripts/gutter_fill_pf3.py`, base, normal and ORM).
  - Tried without visible effect: flattening the head normal map in the face (`flatten_face_normal_pf3.py`, kept at 0.85), Taubin
    smoothing of the eye-opening rims (in `chin_smooth_pf3.py`).
- **Sheets (viewer, read zoomed)**: `review/pass5/viewer_ba_{a,b}_head.png` (before r34 / after, same zoom: front close-up, 3/4, both
  profiles), `review/pass5/viewer_ba_{a,b}_body.png` (party view front and 3/4), `review/pass5/final_front_zoom.png` (both tiers),
  `review/pass5/r7_r9.png` (wedges gone), `review/pass5/r13_mouth.png` (glint gone). The viewer's shot API has no low camera; 3/4
  from below was judged in pass 4.
- **Gates on p5r14** (`review/gates_pass2/`, `scripts/gates_pass2.sh` + `headwear_gate_pf3.py`): collapse, robe, arm/hand, jitter, bone
  length, sleeve poke and see-through identical to pass 4; flat 0.00 / 0.00; detached-parts report unchanged; head set atlas 54.2 % (the
  single-texel sliver rows count as 251 extra islands; fragments 1.6 %); headwear: veil <= 2.9 cm as before, braids <= 1.9 cm (Fidget 1.9,
  Dead 1.1; were 1.4 / 0.9: the added head rows change the gate's body sample). Winding 0. Binding test PASS (224 descriptors on 98
  models, 0 failed), floor rows 35 / 40 ok (stand -0.2, walk -0.1..+1.6, living -1.2, dead 0.0), viewer p5r14 0 console errors.
  Installed sha256 4c8f6d61... (= export).
- **Remaining marks** (read at the user's zoom): two pixel-size dark ticks on the nose ridge; very faint arcs from the mouth corners;
  the eyeballs read flat-lit with small pale corners; a white tick between the ear and the braid in 3/4 (the veil's front edge seen
  through the gap between the hair and the braid, as in pass 4); the hood's frayed front edge (Meshy, unchanged since pass 2).

## Fourth pass (orchestrator, 2026-11-02, r34)

The white zigzag streak on the cheek in front of each ear in profile (F1 has the same; F1 stays frozen). 0 Meshy credits.
- **Cause**: Meshy left a small hole in the head shell beside each cheek (a 4-vertex rim about 1 cm across, |x| 6.2 cm, 1.59 m over the
  soles). F1's `tweak_pf1.py` ("HOLES closed") closes it by collapsing the rim onto its centre, so the faces round that point fold into two
  thin wedges, which a light from the side draws as a bright "<" (geometry: it shows in grey clay with and without the normal map). Not
  paint, UVs or the hood mask. (For F1: same hole, same collapse; the fix below applies there too.)
- **Fix** (`scripts/chin_smooth_pf3.py`, first step): the rim vertices go back onto a small ring (half their original spread round the
  centre, in the cheek's plane) and the hole gets a two-triangle cap with its own rows on one skin texel (the rim rows lie in different
  UV islands; a cap on their UVs stretched over the atlas). Positions that coincided before this script now stay coincident (each group
  takes its mean): smoothed separately, the collapsed points had reopened the hole and shown the white veil lining through it.
- Also in this pass: `scripts/hood_edge_pf3.py` paints the few hood faces that the ear clamp folds flat onto the cheek with the head paint
  under them (they carried linen). Tried and dropped: smoothing the ear ridge (it opened a gap to the veil lining: a white sliver).
- LOD0 14,982 (+4 cap triangles). Gates on r34 (`review/gates_pass4/`): arm/hand 0 frames > 1 cm in all 11 clips, jitter 0, robe 0,
  winding 0, flat 0.00 / 0.01, head set atlas 55.7 %, fragments 1.6 %. Binding test PASS (216 descriptors on 93 models, 0 failed), floor
  rows 35 / 40 ok, viewer r34 0 errors. Installed sha256 8c7de192... (= export).
- Sheet (read): `review/pass4/profile_sheet.png` (MM9 F3 B, F1, ours B r21 / r34, MM9 F3 A, ours A r21 / r34: profile, 3/4 from below,
  front, party view; back faces culled as in the game); cheek close-ups `review/pass4/after_cheek.png` (r34: both profiles, 3/4 from below,
  party view, both tiers). Remaining: a tiny pale tick at the braid's top in the 3/4-from-below close-up.
- All Blender/Python jobs of this pass ran under `systemd-run --user --scope -p MemoryMax=12G -p MemorySwapMax=0` (VARIANTS_BRIEF "Memory").

## Third pass (user review, 2026-11-02, r21)

User: "has giga strange face geometry there? like check the profile" (`review/user_notes/chin_jaw_q34_tierb.png`, `profile_tierb.png`, tier B).
0 Meshy credits. Before state: r17 (`work/r17/`, `export/mm9_peasantf3_r17.glb`; pass-2 scripts in `work/before_pass2/`).
- **Diagnosis** (`review/pass3/profiles_diag.png`, `clay_profile_diag.png`): F1's head (unchanged in F3) has an older woman's soft chin, 1.5 cm
  behind the lips and rounding into the neck; pass 2 made it worse in shading (the normals of the chin and the neck's front relaxed into one
  surface, so the under-chin/neck angle disappeared: the "slab"). MM9's F3 is a young woman: chin nearly under the lips (0.8 cm behind), a
  flat under-chin, a clear angle at the neck.
- **Chin and jaw** (`scripts/chin_smooth_pf3.py`, positions only, UVs unchanged; the whole face stays on F1's rigid Head weights): pass 2's
  under-chin smoothing removed (only the lip-corner crease above the chin point is smoothed now), the chin point brought 12 mm forward and
  4 mm down (Gaussian round 1.525 m, x sigma 2.5 cm, front faces only), a 2.5 mm mentolabial fold under the lower lip, and the corner between
  under-chin and neck carved (vertices in the rounded bulge moved to the nearer of the neck line and the under-chin plane, capped 14 mm, per
  |x| toward the ears); `build_glb_pf.py`'s chin/neck normal relax removed. **Part seams** are coincident but separate vertices (the split
  Meshy shell): now held by position (pass 2's hood tuck had opened the nape seam by 4.6 mm, a background line across the neck in r20).
- **Nose**: tip rounded (Laplacian within 9 mm of the tip, at most 2.5 mm, lifted 1.5 mm); `project_face_pf3.py` repaints every nose texel
  darker than 0.95 of the nose's own skin with that skin (the painted nostril marks on the front of the nose were the "dirty patch"); nostril
  shading only on faces pointing straight down.
- **Veil front edge** (`scripts/hood_edge_pf3.py`, new): F1's hood/head split is a zigzag of triangles, so linen and hair met in teeth. In a
  band round that border (above 1.52 m, in front of the ears) every texel becomes linen or hair by the share of hood surface within 16 mm of
  its 3D point, taking the nearest clean linen or hair (or cheek skin) colour; a hem band just inside the line x0.88.
- **Temple blotches**: `skin_harmonize_pf3.py` treats the temple in front of the ear below the hood edge (|x| > 5 cm, 1.58-1.64 m) as skin.
- Sheet (read): `review/pass3/profile_sheet.png` (MM9 F3 B, F1 approved, ours B r17 / r21, MM9 F3 A, ours A r17 / r21: profile, 3/4 from
  below as the user's shot, front, party view). Also `review/pass3/faces_r21.png`, `review/pass3/check_r19.png`, `review/pass3/edge_diag.png`.
- Gates r21: see `review/gates_pass2/` (same set as pass 2) and the status file. Installed sha256 5c6071d5...; viewer r21.
- Still visible: a light/dark split along the chin's midline in close-ups (the mirrored halves, as before); the chin reads a little pointed
  from the front; small dark hair teeth remain at the very top of the hood edge on tier B from above; a pale line at the clamped ear in Blender
  studio renders (also in F1's approved renders; not in the user's viewer shots).

## Second pass (orchestrator review, 2026-11-02, r17)

Six faults found in the sheets, all fixed without Meshy (0 credits; F3 total stays 20). Rebuild: `scripts/rebuild_f3.sh <rev> [--install]`
(the steps below are wired in). Before state: `work/before_pass2/` (r5 GLBs, head textures, asm and uv npz).

1. **Square patch in front of each ear** (3/4 and side views). Not the UVs (the ear-plate islands have the face's density, 1,614 px/m): paint
   and shape. The plates had one flat fill colour; a darker block of skin-painted hood texels sat beside them; the plate facets shade
   differently. New `scripts/skin_harmonize_pf3.py` (after the face projection, both tiers): every head-shell skin texel outside the face
   core takes a 3D low-pass of the skin round it (Gaussian 6 mm, over the welded surface, ignoring UV seams) plus its own fine detail; the
   ear plates take the cheek in front of them plus the Meshy paint's fine detail; hair (tier B's dark, A's blonde) stays out. Geometry: the
   plates are Laplacian-smoothed into the cheek (`scripts/chin_smooth_pf3.py`, head vertices near the hood's interleaved faces held: moving
   them bared white hood faces as a zigzag) and their normals were already relaxed.
2. **Hard lighter block on the chin**: geometry. A grey-clay render with and without the normal map showed a crease from the lower lip's
   corner to the chin's underside. `chin_smooth_pf3.py` smooths the chin below the lower lip (cap 5 mm), `build_glb_pf.py` relaxes the
   normals of the chin and the front of the neck (as F1 does for the lids and ear plates), `project_face_pf3.py` flattens the normal map
   below the lips.
3. **Pixelated block under the chin**: the flat neck fill met the face repaint's window along hard edges; the harmonised skin (1) and the
   relaxed normals (2) make the jaw, chin underside and neck one surface. A soft light/dark split along the neck's front midline remains
   in the under-jaw view.
4. **Ledge where the veil starts on the hood**: the veil's top row now lies 1.5 mm on the hood (was 4 mm) and its lining closes onto the
   outer sheet at the top edge (no rim step); the hood's lower back (with the neck seam it shares, all under the veil) is tucked 8 mm in
   (`chin_smooth_pf3.py`) so its rim no longer pokes out over the veil when the head turns. A small bump at the hood's top seam remains in
   walk/talk back views (F1's hood ridge).
5. **LOD0 17,494 -> 14,978** (< 15k): `scripts/grid_reduce_pf3.py` merges the veil's grid 2 x 2 and the braids' rings 4 at a time, keeping
   the paid head UVs (a merged quad only when one UV chart holds its four corners; 38 veil blocks stay unmerged at chart seams); F1's skirt
   lining (hidden inside the skirt) decimated to 60 % by `scripts/reduce_pf3.py` (Blender collapse; its surviving vertices become new asm
   vertices at their decimated positions, weighted by the lining's rules). A general decimation of the veil and braids was tried first and
   shredded the thin veil and flattened the braid tubes (`review/pass2/face_before_after.png` history in this section's notes).
   LODs 14,978 / 7,344 / 2,643 / 1,043.
6. **Contacts** (`headwear_gate_pf3.py`, cm into the body beyond the bind pose, worst per clip): braids now 0.2-1.9 (were 0.3-2.7: the lower
   braid rides 65 % on Spine3), veil 0.3-1.6 in most clips (Walking 1.1, Running 0.8, Death 1.3; were 1.5 / 1.8 / 2.6), but 2.9 in Talk,
   Conv1 and Cower (head turns and the cower's bowed neck against the shoulders; the veil's back gap was raised from 12 to 18 mm).

r17 also thickens the braids (radius 10.5 -> 12.5 mm, shallower plait pinch: they read thin once 4 rings became 1). Gates on r17: see "Gates (second pass)" below. Sheets (read): `review/pass2/face_before_after.png` (r5 vs r16, both tiers: front, 3/4,
both sides, mouth, both under-jaw views), `review/pass2/ears_sheet.png`, `review/pass2/close_a_sheet.png`, `review/pass2/close_b_sheet.png`,
`review/pass2/diag_chin.png` (clay with/without normal map, before/after the chin fix), `review/pass2/harm_diag.png` (unlit cheek/jaw).

### Gates (second pass, r17, `review/gates_pass2/`; see-through on r16, whose body and veil are identical)

| Gate | r17 | r5 (first pass) |
|---|---|---|
| `arm_hand_gate.py --outer-only --exact` | 0 frames > 1 cm, every clip; hand depth <= 0.7 cm | 0 |
| `jitter_gate.py` | 0 fails | 0 |
| `robe_gate.py` / `sleeve_poke_pf1.py` | 0 frames / 0 mm | 0 / 0 |
| `collapse_gate.py` | as F1 (Hit armpit R 74, waist 67; Death waist 60, skirt 28) | the same |
| `detached_parts_audit.py` | 2: the legs, by design (as F1) | 2 |
| `bone_length_audit.py` / `flat_shading_check.py` / `check_winding.py` | 0 stretching / 0.00 body, 0.01 head / 0 inverted | the same |
| `texture_quality.py` | body: F1's layout (atlas 66.8 %, spread 3.42, stretch p90 1.09, fragments 0.0 %); head set atlas 55.7 %, spread 1.66, fragments 1.6 %, stretch p90 1.22 | head fragments 0.9 % |
| LOD0 triangles | **14,978** | 17,494 |
| `headwear_gate_pf3.py` (cm, worst per clip) | braids <= 1.9 (Walking), 0.0-1.6 elsewhere; veil 0.3-1.6, Talk/Conv1/Cower 2.9 | braids <= 2.7, veil <= 3.0 |
| `see_through_gate.py` hole max px | boots 0; head 49 / 30, sleeve R 28 / 22; torso 749 / 123, sleeve L 1592 / 26, collar 618 / 6 (elevation 0 / 20 deg): the large ones all at Death 30-39 seen from the feet at ground level, up the open skirt into F1's hollow dress, unchanged by this pass | torso 757, sleeve L 1546, collar 620 (corpse seen up the skirt) |
| `floor_audit.py --world mm9` rows 35, 40 | ok (stand -0.2, walk -0.1..+1.6, living -1.2, dead 0.0) | ok |
| `mm9_actor_models_build_every_binding` | PASS, 204 descriptors on 90 models, 0 failed | PASS |
| Viewer `run_creature_review.py check` (r17) | 22 switches, 0 failed, 0 console errors | the same |

Installed `assets_source/worlds/mm9/models/mm9_peasantf3.glb` sha256 967f547d... PeasantF1 unchanged after the second pass: its four
installed GLBs, every file of `../mm9_peasantf1_claude/` and its two `actors.yml` blocks are identical to the hashes taken at the start
(`../mm9_hag_claude/work/approved_sha_before.txt`). Old Hag untouched (sha256 6409f937... as approved).

## What differs from PeasantF1 in MM9 (measured)
`meshcmp.py peasantf1:peasantf3` and per-bone vertex distances (`review/mm9/f1_vs_f3.png`, `heads_f1_vs_f3.png`, `skins_f3ab.png`):
- **Skeleton, binds, clips**: identical (73 joints, every bind matrix equal; both rows play the shared PeasantFemale library).
- **Torso, arms**: identical (p90 0.7 / 0.6 cm). Legs ~2 cm (inside the skirt, not visible).
- **Headwear**: a long linen veil down the back (MM9 bone Ponytail12, up to 20.6 cm beyond F1's hood) and two braids from the temples to the
  chest (the `xpony` / `xpony_a` chains; F1 has no braid geometry).
- **Skins**: F3a a young blonde woman in a blue dress, white apron, red lacing, a red-bead necklace; F3b a dark-haired young woman (another
  face) in a brown, dirty, torn dress, beige apron, worn cream veil. Both have a low neckline (F1 has a high chemise). Different art from F1:
  a new body paint.

## Route (20 Meshy credits)
1. Baseline: F1's runtime rebuilt from the copied sources in this project = byte-identical to the installed `mm9_peasantf1.glb`.
2. `scripts/add_parts_pf3.py` (F1's frozen mesh + its tweaked head -> `work/asm_frozen.npz`; F1's copies kept as `*_f1.npz`):
   - **veil**: a sheet round the back of the head (105 deg either side of the back), its top row on the hood at 1.615 m (4 mm out),
     falling to 1.185 m at the back and to the shoulders at its front ends (MM9's veil reaches the mid back); per column it follows the
     head/hood/bodice radius (|x| < 15.5 cm: over the shoulder blades, not the arms) plus a 4-12 mm gap and never falls inward faster than
     0.28 (a stiff linen hanging from the hood, as MM9's); a lining 2.5 mm inside and a rim strip close it (one-sided cloth). 1,284 triangles.
   - **braids**: two tubes (7 sides, a ring every 6 mm, swelling and pinching every half plait, tapering to a tie and a tuft) from under the
     hood's side edge at the temple along MM9's braid path in front of the shoulders to the upper chest, kept 4 mm clear of the body,
     capped, shortened to 82 % of MM9's length (`LEN_SCALE`, same ring count: the full length ran the ends into our fuller bust in
     Standing and Hit). 1,736 triangles. LOD0 17,494 triangles (F1 14,474 + 3,020).
3. Weights `scripts/weights_pf3.py` (F1's weights for every F1 vertex, verified identical): the veil's top band takes the hood's weights
   (Head, its back on Ponytail11/12) and eases from 1.53 m down to the bodice's spine/clavicle weights (cloth resting on the back), lining =
   its outer twin; braids along the `xpony` chains by length (Head at the top 10 %), joint boundaries softened +-4 %. The mirror-partner
   search is limited to F1's parts (the braids beside the face had changed 116 F1 vertices' weights in the first run).
4. UVs `scripts/uv_pf3.py`: the body set is F1's, row for row; the head set (head, hood, veil, braids) re-laid with `uv_atlas.py` (face 1.7x),
   then `scripts/fix_lining_uv_pf3.py` (each lining face takes its outer twin face's UVs). **Never re-run uv_pf3.py** (the head paint
   belongs to this layout).
5. HD masters (Codex, brief `references_hd_f3/CODEX_BRIEF.md`): four body views of F3a on F1's approved masters as the shape authority
   (no veil or braids, so nothing hides the dress) and a four-view head turnaround with veil and braids on F1's head (face structure).
6. Meshy (backup account): body retexture 4K `pf3_body_tex_4k` (10) and head retexture 4K `pf3_head_tex_4k_a` (10); balances seen
   3175 / 3165 before the jobs. Uploads: the body without veil and braids, the head set without the lining.
7. Paint: `compose_pf.py`, AO bakes + `pad_ao.py`, `finish_pf.py` (gentle grade), `sym_paint.py`; `scripts/head_fix_pf3.py` (F1's head
   fixes without the collar recolours; the neck eases from the chin's tone to the body's chest skin; Meshy's red bodice paint on the
   veil's lower tip cleaned); `scripts/tier_b_head_pf3.py` (tier B's head base: braids and hair dark brown, veil and hood toward worn
   linen); **faces**: Codex repaint by landmarks of both women (`references_face_f3/`, brief there: closed-lip smiles, no teeth, no red
   rims; B a different, dark-haired woman), `scripts/align_face_pf3.py` (skin gains on chin and cheeks), F1's `warp_nose_pf1.py` (the nose
   fitted to the geometry's), `scripts/project_face_pf3.py` (F1's projection; veil and braids neither occlude nor take the repaint; tier B
   also over the hair, `HAIRWIN=1`; softer nostrils; the clamped ear plates take the surrounding skin).
8. Tiers `scripts/tiers_pf3.py`: one body paint (skin A); region R the blue dress cloth (bodice, sleeves, skirt by hue, the lacing out),
   G the apron; ramps from MM9's own texels (dress: A blue, B brown; apron: A its own white, B MM9 B's beige). Head colour per tier.
9. One command: `scripts/rebuild_f3.sh <viewer rev> [--install]` (tweak -> head paint -> faces -> finish -> tiers -> rig -> runtime -> viewer).

## Gates (final GLB r5, `review/gates/`, `scripts/gates.sh`)

| Gate | PeasantF3 | PeasantF1 (approved) |
|---|---|---|
| `arm_hand_gate.py --outer-only --exact` | 0 frames > 1 cm in all 11 clips (hand depth <= 0.7 cm, Hit L) | 0 |
| `jitter_gate.py` | 0 fails | 0 |
| `robe_gate.py` / `sleeve_poke_pf1.py` | 0 frames / 0 mm in every clip | 0 / 0 |
| `collapse_gate.py` | identical to F1 (Hit armpit R 74, waist 67; Death waist 60, skirt 31) | the same |
| `detached_parts_audit.py` | 2: the legs, by design (as F1); veil and braids attached | 2 |
| `bone_length_audit.py` | 14 checked, 0 stretching | 0 |
| `flat_shading_check.py` | 0.00 body, 0.01 head set | 0.00 / 0.01 |
| `check_winding.py` | 0 inverted | 0 |
| `texture_quality.py` | body = F1's layout (atlas 66.5 %, fragments 0.0 %, stretch 1.05); head set atlas 55.8 % (70.7 % with the lining sharing the veil's charts), density spread 1.67 (face 1.7x), fragments 0.9 %, stretch p90 1.13 | head 58.5 % |
| **`headwear_gate_pf3.py`** (new: veil and braids inside the rest of the body, beyond the bind pose's own reading, 30 fps) | braids: Standing 0.3 cm, Cower 0.6, Talk 1.2, Conv1 1.4, Conv3 1.7, Hit 1.7, Walking 2.0, Running 2.5, Fidget 2.5, Death/Dead 2.7 cm (the braid ends swinging onto the bust/shoulder on MM9's `xpony` keys); veil: 1.3-1.9 cm, Talk/Conv1 3.0 cm (head turns against the shoulders), Death 2.6 | - |
| `see_through_gate.py` (pdm2), hole max px (elevation 0 / 20 deg) | torso 757 / 121, sleeve L 1546 / 14, collar 620 / 4 (all at Death 30-39 and Dead from the feet at ground level: up the open skirt into the hollow dress), head 50 / 27, sleeve R 24 / 14; boots 0. Run on r4 (braids shortened after; veil and body unchanged) | not run on F1 |
| `floor_audit.py --world mm9` rows 35, 40 | stand -0.2, walk -0.1..+1.6, living -1.2, dead 0.0: ok | the same |
| `mm9_actor_models_build_every_binding` (`--world mm9`) | PASS, 198 descriptors on 86 models, 0 failed | |
| Viewer `run_creature_review.py check` | 22 switches, 0 failed, 0 console errors (revision r5-20261102, tiers pf3_a, pf3_b) | |

## Sheets (read)
`review/final/before_after_sheet.png` (MM9 F1 B, our approved F1, MM9 F3a, ours pf3_a, MM9 F3b, ours pf3_b: five views each),
`review/r2/faces_ab.png` (both women: front, 3/4, both sides, eyes, mouth, both neck sides; bind and Talk), `review/r2/unlit_ab.png`
(unlit 3/4, side, from below), `review/final/ears_sheet.png` (both ears, under the jaw, party view, both tiers),
`review/r3/close_a_sheet.png`, `review/r3/close4_b_sheet.png` (head, veil and braids in eight clips, four views),
`review/final/braids_sheet.png` (braids at the gate's worst frames), `review/geo/parts_v2.png` (the added parts), `review/geo/mm9pose_sheet.png`
(MM9's own F3 on the library clips: its veil and braids fly through the body too), `references_face_f3/review.png`,
`references_hd_f3/selected_views_review.png`, `references_head_f3/selected_views_review.png`.

## Binding
`assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantf3_claude` (`scripts/bind_actors_pf3.py`, run under the flock by
`../mm9_hag_claude/scripts/bind_under_lock.sh`): `MM9 40 Shopkeeper` (pf3_a), `MM9 35 Prisoner` (pf3_b); F1's animation block, stride
walk 1.0 / run 1.6, script clips talk/conv1-3/cower/stand. Rows 35 and 40 added to `mm9_npc_actor_rows.tsv` (fallback visuals 357, 382 =
the stand-ins of `mm9_npc_legacy_replacements.tsv`), tables regenerated. Map placement is the orchestrator's switch.

## Approved PeasantF1 unchanged (proof)
sha256 before and after: `assets_source/.../mm9_peasantf1.glb` e07f87e9...45dbd and `assets_dev/.../mm9_peasantf1.glb` c8a5cbb5...d219
identical (`../mm9_hag_claude/work/approved_sha_before.txt`); every file of `../mm9_peasantf1_claude/` hashed before and after: identical;
the `MM9 29 Commoner` and `MM9 33 Shopkeeper` binding blocks identical. Nothing was written there (its sources were copied here).

## Deviations and open points
- **Tier B** is a ramp of skin A's paint: a clean brown dress and beige apron; MM9 B's dirt streaks and torn hem are not reproduced.
- **Veil**: shorter and narrower than MM9's and stiff (no cloth simulation); a visible ledge where it starts on the hood (1.615 m); the
  headwear gate reads 1.3-3.0 cm of veil against the shoulders in head turns. MM9's own veil swings through the body (`mm9pose_sheet.png`).
- **Braids**: plaited by geometry and paint, follow MM9's `xpony` keys; the ends still touch the bust in walk/run/fidget (gate above);
  in the fall they stick out as in MM9.
- **Hood edge** on top of the head: F1's head shell shows small teeth along the veil's front edge (dark on B); tried a hood-coloured fill
  near the edge, no visible gain, dropped.
- **Ear plates** (F1's clamped ears): painted with their surrounding skin; still a faint lighter patch in 3/4 and side views.
- **Neck**: eases from the chin's tone into the chest skin; the body paint's necklace beads reach the head/body seam at the sides.
- **See-through**: the hollow dress shows background up the skirt for the corpse seen from its feet at ground level (F1's construction);
  not lined in this pass.
- LOD0 17,494 triangles, above the 15k MM9 ceiling (F1 14,474 + veil 1,284 + braids 1,736); LOD1-3 8,588 / 3,089 / 1,027.

## What was not checked
In game (the maps place neither descriptor yet); motion by eye at normal speed; LOD1-3 by eye; the see-through gate on F1 for a baseline.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantf3_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf3_reduce_claude/before/`.
