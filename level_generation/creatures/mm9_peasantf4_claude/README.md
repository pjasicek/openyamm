# MM9 PeasantF4, the hooded townswoman in a long-sleeved dress (mm9_peasantf4) — 3D actor on the approved PeasantF1 body, 2026-11-02

MM9 `PEASANTF4.abc` with skins `PeasantF4a` and `PeasantF4b`. `MONSTERS.txt` rows on this model: **30** Commoner "Peasant Human1 FemaleA B"
(F4a; DAT class `CommonerHumanFemaleB`, 5 objects, one with NPC187.scr = Hungerda Atlidotir's voice), **37** Commoner "Peasant Human2
FemaleA B" (F4a; `CommonerHuman2FemaleB`, 2 objects) and **42** Prisoner "Peasant Human2 FemaleD A" (F4b; no DAT placement in the rebuilt
maps). Built as a shared-mesh variant (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`) on the approved, frozen PeasantF1
(`../mm9_peasantf1_claude/`, read only; its sources copied here through `../mm9_peasantf3_claude/`, the sibling variant on the same body).
Own GLB `mm9_peasantf4.glb`, tiers `pf4_a` (rows 30, 37) and `pf4_b` (row 42).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantf4.glb` (`tools/install_model.py --world mm9`) = `export/mm9_peasantf4.glb`, sha256 bccd88d7...07cf (r41, job 8, 2026-11-04; geometry = r40; r31 9c054aca...24a5 kept as `work/j8_rollback_r31_mm9_peasantf4.glb`); tiers `pf4_a`, `pf4_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantf4_claude` (`scripts/bind_actors_pf4.py`, run under the flock by `scripts/bind_under_lock.sh`): `MM9 30 Commoner`, `MM9 37 Commoner` (pf4_a), `MM9 42 Prisoner` (pf4_b); F1's animation block (stride walk 1.0 / run 1.6, look Neck + Head, script clips talk / conv1-3 / cower / stand) |
| Descriptors | rows 30, 37, 42 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 350, 377, 384 = the stand-ins of `mm9_npc_legacy_replacements.tsv`), tables regenerated (229 rows). Map placement is the orchestrator's switch |
| Triangles LOD0/1/2/3 | 14,948 / 7,343 / 2,640 / 880 (r40) |
| Skeleton, weights, clips | F1's: 108 joints (MM9's 73 + 30 finger bones + 5 half-joint helpers), every F1 vertex on F1's exact weights, F1's 11 clips unchanged |
| Textures | body colour 2K, normal and ORM 1K, region mask 1K (R dress, G apron); head colour 1K per tier (2), head normal and ORM 1K |
| Meshy credits | **20 / 30**: body retexture 4K 10, head retexture 4K 10 (backup account; 2845 and 2835 seen before the jobs) |
| Codex | HD masters (body 4 + head 4, one run); face repaint: the joint run stalled in API reconnects twice (killed by literal PID), then one run per woman with smaller inputs |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf4_claude/review/viewer/ revision r41 |

## What differs from PeasantF1 in MM9 (measured)
`mm9_meshcmp.py peasantf4:peasantf1,peasantf3`: the same skeleton (73 nodes, identical binds), head p90 2.8 / max 5.7 cm, torso 1.9,
arms 0.7, legs 1.1 cm. Looked at side by side (`review/mm9/bodies_f1_f3_f4.png`, `heads_f1_f4.png`, `arms_f1_f4.png`, sections
`review/sections.png`), the differences that show are larger than the one-sided distances suggest:
- **Hood**: rounder and 3.8 cm lower on top than F1's peaked hood; it falls to the shoulders at the sides and to the upper back behind (a
  stiff cape; its lower edge runs straight from the front corner at the shoulder, 0.115 / -0.007 / 0.543, to the back tip, 0 / 0.159 /
  0.463, MM9 frame); its front edges hang beside the jaw, the front of the neck bare. MM9's weights: Head; the front corners on the `xpony`
  / `xpony_a` chains, the back tip on Ponytail11.
- **Sleeves**: long bell sleeves (radius 3.8 cm at the elbow widening to ~5.6 cm, open ~3 cm above the wrist) where F1 has bare forearms;
  an embroidered band where F1's short sleeve ends.
- **Skins**: A a dark-haired woman of ~45 in an olive-green tunic dress (embroidered keyhole placket, belt), cream apron, near-black
  skirt; B an older, thinner woman in a rust-brown dress with a torn, dirty apron and a teal-hemmed underskirt. Different art from F1.

## Route (20 Meshy credits)
1. Baseline: F1's frozen asm (`work/asm_frozen_f1.npz`) and tweaked head (`work/uv_tex2_f1.npz`), both copied from the F3 project (which
   took them from F1); F1's rig (`work/rig.json` = F1's, refitted identical). MM9 F4 converted with both skins (`source/mm9/pf4a|b.glb`).
2. `scripts/reduce_asm_pf4.py` (Blender): F1's skirt lining (hidden in the skirt) collapse-decimated to 45 % on new asm rows
   (1,426 -> 640 triangles), every other asm index unchanged.
3. `scripts/add_parts_pf4.py` -> `work/asm_frozen.npz`:
   - **hood4**, a new outer hood. Directions from the head centre (0, 0, 0.665) are parametrised round a pole behind and above the head:
     rings of polar angle up to one boundary curve, so the hood is a disk whose single clean boundary is the face opening, the front edges
     and the hem (10 rings, 64 boundary columns, fewer inside). Boundary: the face opening 5.5 deg beyond F1's hood/head seam (its zigzag
     and F1's hood teeth lie under the new hood), the hem on MM9's line from the front corner to the back tip. Radius: MM9 F4's hood
     surface (the first exit of MM9's closed head mesh from the centre), never closer than 3 mm to our head (F1's old hood only below the
     crown, so the crown takes MM9's rounder, lower top), opening toward MM9's hem over the outer four rings, 8 mm in front of the bodice
     where a ray meets the shoulders or back, the opening edge hugging the head 1.5 mm out; smoothed. A lining 2.5 mm inside over the outer
     two rings and a rim strip close the cloth.
   - F1's hood ('scarf') stays as the hidden skull: its free vertices pulled 3 mm inside the new hood, its crown triangles under the hood
     deleted (LOD0 budget). Every F1 head / hood vertex within the hood's domain pushed 2.5 mm under it.
   - **sleeve4**: a round tube per arm, from 2.5 cm inside F1's short sleeve to 0.86 of the forearm, at MM9's radius (3.8 cm at the
     elbow, 5.6 cm at the open end) and never closer than 4.5 mm to the arm (every arm vertex checked between rings); a lining from 0.32
     of the forearm to the end, a rim, and a cap closing the lining onto the arm. The MPFB arm under the tight part of the tube
     (f -0.25 .. 0.28) is deleted (hidden; nothing left to poke through at the elbow); the hand and wrist are F1's.
   LOD0 14,926 triangles.
4. `scripts/fix_shards_pf4.py`: F1's old hood poked green shards through the new hood beside the cheeks where a ray from the centre
   missed it; every free old-hood vertex within 3 cm and less than 3 mm under the hood surface moved along its normal (positions only).
5. Weights (`scripts/rig_f4.sh`): `weights_pf3.py` on F1's own asm (F1's rules, verified to reproduce F1) gives **every F1 vertex exactly
   F1's weights** (`merge_weights_pf4.py`); `weights_pf4.py` weights the new rows: the hood from MM9 F4's own hood weights (Head, the
   front corners on xpony/xpony_a, the back tip on Ponytail11; interpolated from MM9's hood surface), easing below the jaw (asm z
   0.54 -> 0.65) onto the bodice's weights (the cape rests on the shoulders: head turns no longer push the hem into them), the opening
   edge rigid on Head, the lining = its outer twin; the sleeve = the arm under it at the same arm coordinate, the bell beyond 0.40 of the
   forearm on the arm's weights at 0.40. F1's clips unchanged (no arm corrections).
6. UVs `scripts/uv_pf4.py` (never re-run: the paid paints belong to `work/uv.npz`): both sets re-laid with `uv_atlas.py` (body 2K: arms
   1.4x, legs 0.5x, skirt lining and sleeve caps 0.3x; head 1K: face 1.7x, F1's hidden old hood 0.3x); linings take their outer twin
   faces' UVs.
7. HD masters (Codex, `references_hd/CODEX_BRIEF.md`, one run): four body views of F4a on F1's approved masters as the shape authority
   (no hood, so the dress and shoulders are painted; long bell sleeves), four head views (hood to the shoulders) on F1's head turnaround.
   Gate: overlay on F1's masters (`review/master_overlay.png`), palette vs MM9.
8. Meshy (backup account): body retexture 4K `pf4_body_tex_4k` (10) and head retexture 4K `pf4_head_tex_4k` (10); balances seen 2845 and
   2835 before the jobs (2815 after, other agents included). Uploads: the body without the hood and linings, the head set without linings.
9. Paint: `compose_pf.py`, AO bakes on the uploads + `pad_ao.py`, `finish_pf.py` (gentle grade); head: `sym_paint.py`, `head_fix_pf4.py`
   (F3's fixes), `scripts/hood_tone_pf4.py` (the hood one plain wool: median colour + 3D low-pass deviation clamped to +-10 % + its own
   weave; F1's old hood as the dark inside; black specks on hidden head texels filled; tier B's hood x 0.93/0.84/0.76 = MM9 B / A);
   faces: Codex repaint by landmarks (`references_face/`), `align_face_pf4.py`, `warp_nose_pf1.py`, `project_face_pf4.py` (the new hood
   occludes; HAIRWIN for both women: dark hair under the hood edge).
10. Geometry after the paint (`rebuild_f4.sh`, positions only): F1's `tweak_pf1.py`, `scripts/chin_pf4.py` (F3's pass-3 chin: 12 mm
    forward, 4 mm down, mentolabial fold, under-chin/neck corner carved; MM9 F4's chin is 1.2 cm further forward than F1's), and
    `scripts/under_hood_pf4.py` (head / old-hood faces the tweak brought within 2.5 mm of the hood pushed under it).
11. Tiers `scripts/tiers_pf4.py`: one body paint; R the olive dress (bodice, sleeves, tubes; embroidery out by hue), G the apron; ramps
    from MM9's texels (dress A olive, B rust; apron B dirty beige, A its own). Head colour per tier (`tier_images.json`).
12. One command: `scripts/rebuild_f4.sh <viewer rev> [--install]`; quick geometry/texture refresh `scripts/build_quick.sh`.

## Faces (2026-11-02)
- Meshy's head paint: wide staring eyes, dark lipstick lips painted open, no hair under the hood. Codex repaint by landmarks
  (`references_face/CODEX_BRIEF.md`, `scripts/codex_face_one_pf4.sh a|b`): A a woman of ~45 with dark hair parted under the hood and a gentle
  closed-lip smile, B an older (~60), thinner woman with grey-streaked dark hair and a calm closed mouth. Projected with F1's tools
  (`align_face_pf4.py`, `warp_nose_pf1.py`, `project_face_pf4.py`, HAIRWIN for both).
- The repaint's lids and nose did not sit on F1's lid and nose geometry (a jagged lash line over a pale band on the iris, a brown blob
  on the nose tip): `scripts/f1_lids_nose_pf4.py` carries PeasantF1's approved, geometry-fitted paint there (read only, by shared asm
  triangles) as luminance detail on the repaint's own skin tone; nostrils kept soft.
- `scripts/underchin_pf4.py` (the jaw's underside: Meshy's dark brown shadow paint -> throat skin), `scripts/skin_match_pf4.py` (face /
  neck pale pink vs Meshy's orange body skin: both scaled half way, to 220/152/116; no line at the neckline, hands no longer orange under a
  pale face), `scripts/pad_set_pf4.py` (gutters re-padded after the paint: thin pale UV-seam lines on the neck).
- The chin: F3's pass-3 sculpt (`chin_pf4.py`), MM9 F4's chin being 1.2 cm further forward than F1's. Nose geometry untouched (F1's).

## Second review pass (2026-11-02, r16-r31; no Meshy credits)
The coordinator's review of r15: faces worried, pale, staring (whites showing, lower-lid bags), a dark nostril blob, thin mouth; F1's
puffed lace-banded sleeves and laced bust instead of MM9's plain fitted bodice and plain sleeves; a clean cream apron instead of MM9's dirty
grey linen (B torn at the hem, teal underskirt). All in `scripts/rebuild_f4.sh` (one chain from the paid inputs):
- **Faces**: a second Codex repaint (`references_face/v2/CODEX_BRIEF.md`: warm tan, rosy, relaxed lids, A a warm closed smile with lifted
  corners, B older and calm) painted over renders of our own projected face, mapped back to texture space (`agx_to_tex_pf4.py`: Blender's
  AgX view transform had made the renders paler than the texture), so no nose warp (`NOSEKEEP`: the repaint's own nose kept, no paler
  underside plate). Lids: the lid skin rotated over each eyeball (`eyelid_pf4.py`, Wyrde's route: upper 10 deg down, lower 6 deg up, the
  lower-lid shelf smoothed) and the lid painted on the eyeball spheres themselves (`eyeball_lids_pf4.py`: the ball above 0.42 r and below
  -0.55 r takes the lid margin's tone with a soft lash line). Normals relaxed on the upper lids (their facets drew a zigzag dark lash line
  under the viewer's key light) and part way on the nose underside (the dark blob under the tip from the front) in `build_glb_pf.py`;
  positions of nose and mouth untouched. Skin tanned (x 0.94/0.88/0.83), rosy cheek apples (`skin_match_pf4.py` TAN / BLUSH), body skin
  matched to the tanned head.
- **Bodice and sleeves** (`body_plain_pf4.py`, `bust_pf4.py`, `puff_pf4.py` KEEP 0): the lace bands round the upper arms and the bust
  lacing repainted as the dress cloth (the lacing column from the cloth beside it at its own height); the lacing's AO (it was multiplied
  into the base colour by the grade) and normal-map relief flattened in copies (`pf_ao_2k_plain.png`, `pf_body_normal_plain.png`); the
  modelled lacing bumps smoothed (main bodice, positions only, <= 11 mm; its separate small pieces ride along, relief pressed 75 %); the
  upper puff squeezed onto the sleeve tube. Gutters re-padded after the recolour. F1's weights and UVs unchanged.
- **Apron** (`tiers_pf4.py`): grime in the base paint (soft blotches, darker toward the hem) and the ramps graded darker/greyer for the
  viewer's bright key (apron x 0.60 and 35 % grey; dress x 0.82); B keeps the torn dark hem band and the teal underskirt, darkened to x 0.22.

## Job 8: forearm sleeves, bodice holes and hem (user review 2026-11-04, r32-r40; no Meshy credits)
User: "the arm part from elbow down has like transparent parts or like holes in the sleeve" (`review/user_20261104/6.png`, `7.png`,
`8.png`, tier B). Causes found with `scripts/diag_parts_pf4.py` (rest-pose renders, every part its own colour, back faces magenta =
what the one-sided viewer culls; `review/diag/`):
- **Sleeve tube (the "transparent" patches and the olive jagged fragments).** `add_parts_pf4.py` built each tube ring in a local frame
  (axis, ref = axis x Z). The upper five rings (f <= 0: inside F1's short sleeve down to the elbow) used the upper-arm axis, the forearm
  rings the forearm axis; those point opposite ways, so the upper rings ran the other way round the arm (a mirror image). 216 of 576
  outer tube faces were wound inward (culled: the near wall vanished and the far wall's inside showed, dark "translucent" patches), and
  the band from ring 4 (elbow) to ring 5 was twisted through the tube (olive, jagged). Meshy had painted those bands while inverted:
  a smooth dark smear without the weave, ending in a line at mid-forearm. Fix: `scripts/sleeve_rings_pf4.py` (one-time on
  `work/asm_frozen.npz`, backup `work/asm_frozen_prej8.npz`; positions only) permutes each upper ring's vertices into the forearm rings'
  order (the reflection j -> 6 - j that makes the elbow band shortest: 74.6 -> 29.8 cm summed): 0 faces inward. Weights follow (the
  tube's weights are taken from the arm under each vertex's position). `scripts/sleeve_paint_pf4.py apply 6 0 4` re-paints bands 0-4
  from band 6 of the same tube (same column, same triangle of the quad, barycentric) in the base colour, normal, ORM, tier mask and
  material classes (texels inside other faces never written).
- **Green blot at the wrist** (seen up the bell): the forearm skin inside the bell was painted olive by Meshy under the tube.
  `scripts/region_paint_pf4.py wrist` re-paints it from the bare wrist below the bell (3D donor lookup along the forearm), all maps.
- **Light triangles on the chest and beside the belt**: F1's bodice has open eyelet holes where its lacing sat (loops of 4-14 edges,
  7 holes: 5 on the placket, 2 beside the belt); the dress is hollow, so each showed the culled back of the dress (background). F1's
  laced bust covered them; F4's plain bodice (bust_pf4.py) uncovered them. `scripts/bodice_fix_pf4.py` (new mesh step after
  `eyelid_pf4.py`, in `rebuild_f4.sh` and `build_j8.sh`) fills every small hole of the main bodice (ear clipping, wound like its
  neighbours; new UV rows by the affine map of the largest bordering face, so they show the cloth beside the hole) and drops the two
  pressed lacing chevrons (32 + 60 triangles; the bodice under them is closed).
- **Spikes at the bodice hem over the belt**: F1's sawtooth peplum (tips 2.5 cm below the notches at each side; MM9's F4 bodice ends
  straight). In `bodice_fix_pf4.py`: the side hem's notches come down to the tips' line (height only, |x| > 7.5 cm eased in, max 32.5 mm),
  the four side tips carried by one face are dropped (they lay flat as needles), and the skirt's and skirt lining's own sawtooth top
  edges under the peplum come down to z 0.098 at the sides (their tips stood out below the new hem as dark teeth in motion). Tried and
  rejected: lifting the tips instead (r33/r34: bared the skirt's notches), re-painting the lowered band (r37: it cut the apron band; the
  dark teeth were the skirt, not paint), raising the skirt's back top edge to close the back slit (r39: it poked through the bodice).
- **r41 (coordinator, user's back view `review/user_20261104/13_back_elbows_r40.png`)**: the shot shows r31's artefacts exactly (the dark
  inside of the upper tube under the short sleeve, the twisted elbow band, the hem spikes): rendering the r31 GLB from the same back-low
  angle reproduces each one, r40 from behind (Blender posed renders with back faces magenta, `review/diag_posed/`; viewer back views of
  Standing / Walking / Fidget / Hit / Cower, both tiers, `review/back/`) has none. The browser had served the r31 manifest and GLB from
  its cache (`fetch('manifest.json')` without cache control; the old file was 35 h old, so heuristic freshness kept it for hours);
  `review/viewer/review.js` now fetches the manifest with `cache: 'no-store'`. A hard reload shows r41. Also in r41: the tube repaint v2
  (`sleeve_paint_pf4.py apply 5 6:10`: bands 0-5 sample the clean bands by arc length and angle on the tube, mirrored at ring 6, so the
  weave keeps its scale and no step shows at mid-forearm, which r40 had faintly), then `pad_set_pf4.py` on the body colour, normal and
  ORM (dark gutter dashes along the tube's UV seams). Geometry byte-identical to r40 (every gate above holds); binding regression PASS
  (250 descriptors on 112 models); viewer r41 check 22 switches, 0 failed. Sheet: `review/back/sheet_back_before_after_r41.png`.
- Triangles LOD0 14,948 (was 14,994: +50 hole fills, -92 chevrons, -4 side tips). Head geometry (LOD0) and every head map are
  byte-identical to r31; F1's weights, UVs of all existing faces and the clips are unchanged.
- One build without the paint chain: `scripts/build_j8.sh <rev> [--install]` (the textures carry the job 8 paint steps; `rebuild_f4.sh`
  runs all of them from the paid inputs). Viewer arm/torso shots: `scripts/arm_shots_pf4.sh <rev> [clip:sec]` -> `review/arms/<rev>[_clip]/`.

## Gates (final r31 after the second review pass, `review/gates_r31/`; r15 in `review/gates_r15/`; `scripts/gates_pf4.sh`)

Job 8 gates (r40, `review/gates_r40/`, before = r31 `review/gates_r31/`):

| Gate | r31 | r40 |
|---|---|---|
| Outer sleeve-tube faces wound inward (`sleeve_rings_pf4.py` check) | 216 of 576 | 0 |
| `see_through_gate.py`, every clip, sleeve "inside" pixels (the view through the culled tube wall), max per living clip | 620-990 | 0-148 (Hit R 148 at 20 deg: a view up into the short sleeve's opening on the inner side of the raised arm, `review/gates_r40/see_through_sleeveR_Hit_21_az045_el20.png`; Cower R 61, Fidget R 37; the rest 0-3) |
| see-through holes, sleeve R / sleeve L (living clips) | 8-25 / 13-28 px | 0-2 / 0-2 px |
| see-through holes, torso (living clips) | 61-108 px | 36-77 px (a level slit between the bodice hem and the skirt top at the back, from F1; 0-6 px at the party's 20 deg) |
| see-through overall max (Death/Dead from the feet up the hollow skirt, as F1) | torso 1559, sleeve L 2003, collar 907, head 157 | torso 1596, sleeve L 2003, collar 907, head 157; boots 0 |
| `sleeve_poke_pf1.py` (F1's short sleeve), every clip | 0 mm | 0 mm |
| `gate_pf4.py` arm under the tube beyond rest | max 0.75 cm (Cower), 0 frames > 1 cm | max 1.0 cm (Cower), 0 frames > 1 cm; hood 0.8 cm, 0 frames > 1 cm |
| `arm_hand_gate.py --outer-only --exact` | 0 frames > 1 cm, Cower forearm 2.4 cm | identical file |
| `jitter_gate.py` / `robe_gate.py` | 0 / 0 | 0 / 0 |
| `collapse_gate.py` | Cower elbow L/R 14/8 | Cower elbow L/R 20/13 (the corrected upper tube now counts at the elbow fold); the rest within 0-3 |
| flat / bone length / winding / detached | 0.00 / 0.01, 0, 0, the 2 legs | same |
| `texture_quality.py` body | 69.6 %, 143 islands, stretch p90 1.06 | 69.6 %, 134 islands, stretch p90 1.08 |
| `mm9_actor_models_build_every_binding` | PASS (240 on 105) | PASS, 250 descriptors on 112 models, 0 failed |
| Viewer `run_creature_review.py check` | 22 switches, 0 failed | r40: 22 switches, 0 failed, 0 console errors |

r31 matches r15 on every gate below (hood max 0.8 cm, sleeve tube 0.8 cm, 0 frames > 1 cm; detached = the 2 legs; flat 0.00 / 0.01;
see-through head 147 / 157, torso 1559 / 118, sleeve L 2003 / 24, collar 907 / 23, sleeve R 27 / 20, boots 0). Installed r31: sha256
9c054aca...24a5 (source = export), binding regression PASS (240 descriptors on 105 models, 0 failed), floor rows 30/37/42 ok, viewer
check 22 switches 0 failed.

| Gate | PeasantF4 r15 |
|---|---|
| `arm_hand_gate.py --outer-only --exact` | 0 frames > 1 cm (hand) in all 11 clips, hand depth <= 0.2 cm; forearm 2.4 cm in Cower L (the bell sleeve on the bust when the cower raises the forearms; `arm_clear.py` tests hands only and changed nothing; clips left as F1's) |
| `jitter_gate.py` | 0 fails |
| `robe_gate.py` / `sleeve_poke_pf1.py` (F1's short sleeve) | 0 frames / 0 mm |
| `gate_pf4.py` (new; hood vs body, arm vs sleeve tube, F1's hidden old hood vs the new hood) | hood <= 0.9 cm beyond rest, 0 frames > 1 cm; arm under the tube <= 0.8 cm beyond rest, 0 frames > 1 cm; old hood: 5 vertices beside the jaw come up to 4-8 mm out in motion (painted hood colour) |
| `collapse_gate.py` | as F1 (Hit armpit R 74, waist 67; Death waist 60) |
| `detached_parts_audit.py` | 2: the legs, by design (as F1) |
| `bone_length_audit.py` / `flat_shading_check.py` / `check_winding.py` | 0 stretching / 0.00 body, 0.01 head / 0 inverted |
| `texture_quality.py` | body atlas 69.6 %, fragments 0.0 %, stretch p90 1.05, spread 3.39 (arms 1.4x, legs 0.5x, linings 0.3x by design); head atlas 61.3 %, fragments 1.9 %, stretch p90 1.21, spread 5.6 (face 1.7x, the hidden old hood 0.3x) |
| `see_through_gate.py` (pdm2's), hole max px (elevation 0 / 20 deg) | head 146 / 156 (Death 24-33: slivers between the face and the hood edge in the fall, `review/see_r15.png`; Standing/Hit/Talk/Walking at r4: 21 / 36); torso 1559 / 119, sleeve L 2000 / 21, collar 907 / 22 (all Death 30-39 seen from the feet at ground level, up the open skirt into F1's hollow dress, as F1/F3); sleeve R 23 / 15; boots 0 |
| LOD0 | 14,994 triangles (<= 15k) |
| `floor_audit.py --world mm9` rows 30, 37, 42 | stand -0.2, walk -0.1..+1.6, living -1.2, dead 0.0: ok |
| `mm9_actor_models_build_every_binding` | PASS, 229 descriptors on 100 models, 0 failed |
| Viewer `run_creature_review.py check` (r15) | 22 switches, 0 failed, 0 console errors |

## Sheets (read)
Job 8 (read): `review/arms/sheet_arms_r31_vs_r40_a1.png`, `_a2.png`, `_b1.png`, `_b2.png` (viewer, Standing: arms front, back, 3/4
both sides, back 3/4 both sides, low 3/4 both sides, elbow close-ups, torso front and 3/4, hem from behind; r31 above, r40 below),
`review/arms/sheet_r40_walking.png` (Walking 0.45 s, both tiers), `review/arms/sheet_r38_cower_b.png` (Cower), `review/sheet_mm9_vs_ours_r40.png`,
`review/diag/r31_elb_sheet.png` / `r31_hem_sheet.png` (the causes: back faces magenta), `review/diag/r32_sheet.png`, `hip_close2.png`,
`review/gates_r40/see_through_*.png`.
Second pass: `review/sheet_face_r31.png`, `review/sheet_face2_r31.png`, `review/sheet_mm9_vs_ours_r31.png`,
`review/face_before_after_r31.png` (r15 vs r31, both tiers: front, 3/4, profile, low 3/4). First pass:
`review/sheet_face_r15.png` (MM9 F4 a and b in studio light, ours in the review viewer's lighting: front close-up, 3/4, true profile, low
3/4 from below, party view and its 128 px simulation), `review/sheet_face2_r15.png` (right profile, Talk 1.4 s, both hood-edge / ear
close-ups, under the jaw; both tiers), `review/sheet_mm9_vs_ours_r15.png` (MM9 vs ours, both tiers: front, 3/4, left, back),
`review/faces/r10_eyenose.png` (eye and nose close-ups before the nostril softening), `review/face_codex.png` (Codex inputs/outputs),
`review/body_r4_close.png`, `review/cower.png` (the bell on the bust in Cower), `review/see_r4.png` (see-through worst cases),
`review/geo_v2.png` and `review/geo_cheek.png` (the added parts in clay), `review/sections.png` (F1 vs MM9 F4 sections),
`review/mm9/bodies_f1_f3_f4.png`, `review/mm9/heads_f1_f4.png`, `review/mm9/arms_f1_f4.png`, `review/master_overlay.png`,
`references_hd/selected_views_review.png`, `references_head/selected_views_review.png`.

## Approved PeasantF1 unchanged (proof)
`work/f1_sha_before.txt` (taken before any work: every file of `../mm9_peasantf1_claude/` and the installed `mm9_peasantf1.glb` in
`assets_source` e07f87e9...45dbd and `assets_dev` c8a5cbb5...d219) and `work/f1_sha_after.txt` (at the end): identical, 1,050 files. Its
`actors.yml` block (`work/f1_actors_block_before.yml` / `_after.yml`) identical; rows 29 and 33 of the rows tsv untouched. F1's files
were only read (its uv npz and head paint by `f1_lids_nose_pf4.py`), never written.

## Deviations and open points
- **Job 8 leftovers (r40)**: from behind at eye level a thin slit between the bodice hem and the skirt's top edge shows the hollow dress
  (F1's; 36-77 px in the gate, 0-6 px from the party's height); raising the skirt's back edge poked it through the bodice (r39), so it was
  left. The forearm tube's upper bands carry band 6's paint: a faint repeat of the weave is possible close up. With the arm raised, the view
  can still go up into the short sleeve's opening on the arm's inner side (sleeve "inside" pixels, Hit R 148 / Cower R 61; no background).
- **Hood**: a smooth surface fitted to MM9 F4's hood (rounder and lower than F1's peak, falling to the shoulders); no folds in the
  geometry (the paint carries a few). F1's hood stays inside as the hidden skull: its lappet faces in front of the ears were dropped (they
  poked through the cape), five of its vertices beside the jaw still come 4-8 mm out in some frames, painted the hood's colour.
- **Inside of the cape**: lined over the outer five rings; from straight below (a corpse seen from its feet, low 3/4 views) the unlined
  inside higher up and the hollow dress show background (see the see-through gate). Under the jaw the inside reads dark.
- **Sleeves**: round tubes on F1's arms; in Cower the bell presses 2.4 cm into the bust (one frame region; clips kept as F1's).
- **Faces** (r31): relaxed and warm now; the brows' inner ends still sit a little high (A can read faintly concerned), A's smile is
  gentle rather than MM9's broad grin, and close up the lid margins keep a soft fuzzy lash line. Under the jaw the carved under-chin still
  shades as a dark band seen from below (geometry; F3's chin-relax had made a swollen slab).
- **Sleeves**: the puff now hugs the sleeve tube but F1's shoulder-to-elbow sleeve still reads fuller than MM9's fitted sleeve, with a
  step where it ends over the tube (the arm's own geometry and F1's weights; not rebuilt).
- **Bodice**: the lacing is gone from paint, AO and normals; its modelled bumps are smoothed/pressed, faint relief remains close up.
- **Tier B**: a ramp of skin A's paint: rust dress, dirty grey apron with a torn dark hem band, teal underskirt band at the skirt hem
  (painted; the hem geometry is not torn).
- **Under the jaw** the carved under-chin faces down and shades dark in a light from above (the paint there is throat skin).
- **Skin**: tanned head (~217/115/62 median) with the body skin matched to it.
- **Map placement not switched** (the orchestrator's step): the rebuilt maps still place 350 / 377 (rows 30 / 37; row 42 has no
  placement); descriptors `MM9 30 Commoner`, `MM9 37 Commoner`, `MM9 42 Prisoner` are ready.

## What was not checked
Job 8: the Cower and Hit arm close-ups in the viewer (gates only; the Cower sheet frames the torso), the inside of the short sleeve by eye; the floor audit was not re-run (feet and clips unchanged).
In game (the maps do not place these descriptors yet); motion at normal speed by eye (viewer stills and numeric gates only); LOD1-3 and
shadow meshes by eye; tier B in every clip close up (same mesh, weights and clips as A).


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantf4_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf4_reduce_claude/before/`.
