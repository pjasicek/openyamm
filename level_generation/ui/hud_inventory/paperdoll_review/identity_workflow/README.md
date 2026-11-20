# Paperdoll restoration history and accepted ESRGAN set

**Current decision, 2026-09-24:** the user accepted all 466 native-based ESRGAN body/limb sprites for
75 available dolls. They are now canonical accepted artwork in the main browser. Painted restoration is
deferred future work. See [acceptance and verification](esrgan_acceptance_20260924/README.md).
The pilot descriptions and comparison-stage assessments below are historical, not instructions to resume generation.

Open the [paperdoll review browser](../index.html) to see every character with its assigned avatar portrait and
the current 2× candidate art. Open [the `pc01` pilot comparison](pilot.html) for this workflow's first generated
trial. Both generated attempts shown there are **rejected**; neither was installed, approved, or selected as a
default review candidate.
The [in-place arm comparison](in_situ_preview.html) tests a different method against the high-quality existing
body candidate. Its open-hand and shared-bracer shield-hand trials pass alpha registration, but neither is
visually approved or installed. The main browser still loads its original selected candidates.
The feedback in `test_img/2036.png` and `test_img/2037.png` revealed a visual blocker that registration did not
catch: the `pc01lhu` open hand has a flat crop at its sprite canvas bottom. The original 26×54 image already has
11 alpha-128 pixels in its final row; the 52×108 in-place v2 and later red-bracer trial have 32. The red-bracer
trial only changed the forearm's color and therefore retained the same incomplete fingers. The opposite
`pc01rhd` in the assembled comparison is an unfinished raw prepared cutout, not an approved restoration; a
separate full-sheet generated attempt failed geometry checks. The three-panel shield comparison omitted that
opposite arm entirely. Its middle `pc01lho` panel is an older artifacted batch candidate, and the right panel
is a newer unapproved shield-hand trial. The comparison page now marks these provenance and visual failures.
The [Real-ESRGAN 2× comparison](esrgan_baseline/index.html) places enlarged original bodies and limbs beside
the native originals and current restoration candidates, assembled at the paperdoll table offsets. This is a
separate comparison set; it does not select, accept, or install artwork.

## Real-ESRGAN baseline

`esrgan_baseline.py --all` runs the repository's `realesrgan-x4plus` NCNN model over each distinct existing
body and limb. The model receives source-size RGB with nearest visible colors extended through the transparent
area and four native pixels of edge padding. Its 4× RGB output is cropped back to the original footprint and
downsampled to **exactly 2×** with premultiplied alpha. Because this Real-ESRGAN model does not produce alpha,
the alpha comes from the native sprite. It is enlarged with Lanczos, then clipped to the exact 2× native
occupied footprint so the resampling fringe does not expand tiny finger pieces. This preserves the original
anchors and transparent holes but cannot repair a poor original silhouette or invent a new finger gap. The files are
RGBA PNGs with the source transparency; no magenta matte is included. The manifest retains the source, model,
runner, input, 4× return, 2× output hashes, and per-sprite registration flags.
The completed baseline contains **466 exact-2× RGBA sprites** and assembles **75 prepared dolls**. All 466
pass the existing alpha registration guard after the native-footprint clamp. Six body-only originals include an
opaque full-canvas scene; their backgrounds cannot be toggled independently. The other 460 have transparent
pixels. Characters 30 and 31 still lack the inputs described below.

The browser shows the original, ESRGAN, and current candidate at the same placement. It offers the four bare
hand states where the character has movable limbs, the assigned portrait, the corresponding paperdoll
background, and individual part closeups. The hand states intentionally contain no equipped item; use the
[equipment review browser](../index.html) to inspect the item resolver and worn variants. In the PC01 pilot,
ESRGAN makes the body less blocky and retains the original hand anchors. It also exaggerates some dark/red
bracer pixels and produces thin, unnatural fingers. The current painted body has clearer anatomy and material
detail. In sampled MM7 man, minotaur, and body-only dragon rows, ESRGAN likewise retains placement and much of
the original material pattern, while the current painted candidates show clearer faces, fabric, armor scales,
and fingers. This is a useful geometry-faithful baseline and possible reference for difficult limb joins, but
the sampled ESRGAN art is visually behind the current restoration. Passing alpha registration does not establish
facial identity, material coherence, or final visual acceptance.

Rebuild the baseline from the repository root with:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/esrgan_baseline.py --all
```

## Identity and reference coverage

The authoritative avatar is the **original** portrait named by `character_data.txt`'s `facePicturesPrefix` plus
`01`, matching `portraitTextureNameFromCharacterDollEntry()` in the game. An existing restored 2× portrait is a
secondary comparison until its own review is accepted. The same portrait can legitimately serve more than one
character row.

`prepare.py` made individual reference packs for 75 of 77 character rows. They cover 69 jointed dolls and six
body-only dolls: 466 distinct existing body/limb sprites, with no missing limb inside a prepared pack. Character
30 lacks its original assigned portrait and body; character 31 has a portrait but no body. The other 24 active
`paperdoll_parts` targets are seven backgrounds and 17 head/beard fields, so they are outside these body/limb
packs. The head/beard fields are not currently composited by the paperdoll renderer.

Each `prepared/doll_NN/` directory contains the original assigned portrait enlarged without repainting, an
exact-position sheet of the original body and distinct movable limbs, a four-pose assembly at the table offsets
for jointed dolls, source hashes, cell rectangles, and a prompt draft. These are **references**, not newly
restored or accepted sprites. `prepared/manifest.json` lists all rows and missing inputs. The assembly shows
empty, one-hand, two-hand, and shield hand states without worn items. Actual equipment still needs review in the
main browser at the renderer's item offsets and layer order.

## What the two `pc01` trials established

The first imagegen edit received the native body/limb sheet, original assigned portrait, and assembled poses.
Its raw return has genuine transparent alpha and a face closer to the assigned portrait. Splitting it at the
recorded cells gives exact-2× dimensions, but **all six sprites fail the registration guard**. The grip hand
and finger overlay changed shape substantially. See `prepared/doll_01/pilot_v1_report.json` and the comparison
page. The second, hand-only edit kept the fingers extended, but changed the silhouette's width-to-height ratio
from **2.00 to 2.64**. `grip_v2_geometry_locked_preview.png` shows what a forced bbox resize and native alpha
would look like; it is diagnostic only. `MATTE_AND_FITTING.md` disallows using a native mask to conceal displaced
generated art as an acceptance shortcut.

These trials show why a consistent face and matching skin color are insufficient for a drop-in paperdoll. Each
state must retain its original logical canvas, wrist/shoulder join, fingers, grip opening, and transparent holes.
The game places separate limbs at fixed offsets; imagegen does not inherently enforce those coordinates.
Generation should therefore use the assigned portrait **together with** the original body/limb states and
assembled poses, then pass a per-cell registration and visual join review before continuing to another doll.
The current whole-sheet prompt is a draft, not a validated bulk template.

## In-place limb method tested on PC01

`test_img/2031.png` exposed the strong body / mismatched forearm join. The body candidate was kept pixel-for-pixel
as the style anchor. An arm-only crop was assembled at the **actual doll-type hand offset**, with the original
limb silhouette as the edit target and a separate white edit-region guide. Imagegen repainted the lower bracer
while seeing the upper bracer and skin in place. The return was downsampled, cut back to its original **52×108
pixel 2× canvas**, and reassembled without editing the body. The second open-hand attempt (`pc01lhu`) has genuine
alpha and passes the existing registration guard: silhouette intersection-over-union 0.912/0.914 at alpha 16/128,
and occupied-area ratios 1.063/1.021. This is a **technical pass, not visual acceptance**. Its contour and
attachment still need review over the intended backgrounds and equipment.

The first shield-pose (`pc01lho`) attempt used the restored open arm only as a material reference. Its bracer
looked consistent, but the generated hand became too narrow: at alpha 128, silhouette intersection-over-union
was 0.838 and occupied-area ratio 0.881. The second shield-pose attempt tests exact shared material: its seed
copies the first **48 2× pixel rows** of the restored open-hand bracer at the actual table offsets, then edits
only the cuff and shield hand. The bracer occupies nearly the same silhouette in both states (1,494 copied
pixels, 50 nearby contour colors filled). The generated hand and the protected bracer were extracted together
into the original **64×124 pixel 2× canvas**. This candidate passes whole-sprite registration at alpha 16/128
(intersection-over-union 0.942/0.923) and the hand-only region remains close to its source (0.907/0.875). One
confirmed alpha-3 purple fringe pixel had its RGB corrected without changing alpha. Technical passage does not
approve its anatomy, cuff seam, alpha edges, or appearance under a shield. The body candidate also remains
unapproved and has its own registration flag.

This suggests a production sequence per doll: choose the body and assigned portrait as the identity/material
anchor; restore one **native-geometry limb in place**; reuse its accepted bracer/cuff as the reference for nearby
hand states, changing only the region whose pose actually differs; generate a different forearm orientation as a
separate in-place state. Extract each state to its own exact 2× canvas and review its silhouette, wrist/cuff join,
finger gaps, and all engine-composited poses. A shared bracer may be transferred exactly only where source masks
and placement really coincide. Do not cut an arbitrary limb out of a full-doll image or force a native mask over
misplaced art to make a failed return pass.

### Full-context PC01 retest after `test_img/2035.png`

A third open-forearm imagegen edit included the full restored doll, original limb silhouette, detailed red-bracer
candidate, and edit-region guide. It reproduced the crimson bracer pattern more faithfully than the first two
in-place prompts, which had incorrectly described the lower bracer as brown. It also curled the relaxed fingers
and expanded the alpha-16 footprint to **1.124×** the original (limit 1.10×); see the
[side-by-side](prepared/doll_01/in_situ_left_open/old_vs_in_situ_v3.png),
[raw return](prepared/doll_01/in_situ_left_open/raw_arm_only_v3.png), and
[registration report](prepared/doll_01/in_situ_left_open/return_report_v3.json). It is rejected and not selected
in the main browser. This is direct evidence that even a full-doll reference and explicit geometry instructions
do not make a generated limb drop-in automatically.

The practical source of truth should be one accepted body per doll and one approved proximal arm/bracer master
for each orientation. Generate that master **in its assembled position**, with the body and native pose as
references. Keep the body pixels fixed by recompositing the original body after the edit, then extract the arm
to its unchanged canvas at the table offset. Reject outputs that move the elbow, wrist, fingers, or transparent
gaps. For hand states sharing the same forearm placement, copy the approved proximal bracer pixels exactly and
edit only the distal cuff/hand. Where the arm orientation changes, use a separate in-place pose but the same
material and lighting reference. Small seam or fingertip corrections may need direct 2× pixel painting after
generation. Never stretch or mask a displaced whole limb into a passing shape.

The [red-bracer fit comparison](in_situ_preview.html) now tests that split directly. A material-transfer trial
uses the third return's red-bracer RGB only where it covers the earlier **registered** open arm, retaining that
arm's exact alpha and relaxed fingers below row 72. It passes the existing registration guard. The matching
shield trial samples **2,133** corresponding pixels from that open arm at the game-table offset, fills
**130** nearby contour colors, preserves the previously registered shield-hand alpha and distal fingers, and
also passes registration. An equipped comparison places sword #1 and shield #99 at their table offsets. These
are unapproved visual trials: the closeups still need a judgment of bracer pattern, elbow/wrist seams, finger
anatomy and item clearance before either sprite can be selected as a main-browser candidate.

## Reproduce the preparation and technical checks

From the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/prepare.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/process_pilot.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/process_grip_v2.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/prepare_in_situ.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/process_in_situ.py --version 1
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/process_in_situ.py --version 2
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/prepare_shield_variant.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/process_shield_variant.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/prepare_shared_bracer_seed.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/process_shield_variant.py --shared-bracer
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/process_in_situ.py --version 3
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/compose_pc01_arm_material.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/compose_pc01_shield_material.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/verify.py
```

The processors expect the retained raw `pc01` attempts in `prepared/doll_01/` and only make local review
artifacts. They do not modify the accepted checkpoint or runtime icons. Exact submitted prompts, raw images,
processed previews, source hashes, and failure reports are retained beside that doll's references.
