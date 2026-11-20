# Packed animation sheets with outline-only anatomy guides

This is the user's selected creature-restoration method from 2026-09-30: **one complete original animation per
stored view**, packed tightly in native coordinates, submitted with a separate outline-only geometry guide and a
selected detailed appearance reference. Keep the native pose and limb anatomy while reconstructing fine surface
detail and natural shading. This is the preferred generation recipe for the Creature Restore skill; explicit user
scope and method overrides still apply.

The worked reference is the final MM6 Goblin
[outline_walk_detail_v2 run](mm6_goblin/outline_walk_detail_v2/redo_2x/run.json).
Its earlier internal-contrast trial and washed-out outline trial are superseded appearance references.
The user's 2026-10-01 resolution decision prioritizes complete animation/view sheets even below the 2× detail
target. Offset/size calibration, anatomical acceptance and truthful sampling measurements remain required.

## Invoke the method

These are agent requests, not shell commands:

```text
$creature-restore gob*.bmp — packed outline sheets, all native walking views
$creature-restore m230*.bmp — packed outline sheets, front attack only
CREATURE_RESTORE <native-pattern> — one complete animation per view, outline-only geometry, preserve fine detail
$creature-restore gob*.bmp — inspect and plan packed outline sheets only; do not generate
```

The [Creature Restore skill](../../.agents/skills/creature-restore/SKILL.md) routes here and to the
[atlas/variants pipeline](SPRITE_ATLAS_VARIANTS_PIPELINE.md) for the export contract. Read the imagegen skill and
inspect the actual local references before generation. Use the available built-in image-generation tool.
Saving this procedure, discussing it or planning a run does not start generation.

## 1. Resolve the original animation before packing

Resolve creature descriptors and native frame groups before interpreting filenames. Record the actual palette
and transparent index/key, source hashes, frame order, durations, native scale, canvas dimensions, actor pivot,
anchor flags, pixel aliases, stored directions and mirror/reuse bindings. Preserve repeated or held steps.
Decode native frames to RGBA, removing the actual transparency key while leaving visible foreground RGB untouched.
Do not add contrast, sharpening, smoothing or muscle lines to the colour reference.

The Goblin has five stored walking views, each with six steps. The remaining three views mirror stored views;
they do not require three more generated sheets. Walk views 0–4 are front, front oblique, profile, rear oblique
and back. Other native actions have their own view/reuse rules; discover those rather than inventing every view.
The final worked package replaced **30 walking frames**, retaining **29 non-walk frames** from the preceding
detailed candidate. Those retained actions were not regenerated with this method.

## 2. Pack for detail while preserving native coordinates

1. Place every frame of the target action/view in one shared native actor-coordinate canvas using its verified
   anchor. Preserve fractional offsets. For bottom-center anchoring, use
   `offsetX = (sharedWidth - frameWidth) / 2`, not integer division, and the appropriate bottom offset.
   A 2× preparation canvas can represent half native pixels exactly.
2. Measure the **union of visible bounds across the whole animation**, including swords, ears, fingers, toes,
   tails, wings and motion extremes. The largest single sprite is insufficient when different steps extend in
   different directions. Remove only the common empty exterior.
3. Add the smallest safe transparent border to this common crop. The selected Goblin run used **six native
   pixels**; the earlier tight run used two. A two-pixel border is an option to measure and inspect, not the
   defining setting of the successful final run. State whether padding is native or enlarged-input pixels.
   Padding may extend beyond the original canvas; fill that exterior with transparency and record it. Extra
   blank space cannot restore a feature already clipped in the original.
   If a returned sheet clips a tip, increase the shared cell padding for that complete animation and version both
   native and outline references together. Preserve the previous input files, prompt, crop and return hashes.
   A padding sentence alone may be insufficient: the wider margins must appear in the submitted reference grid.
   Recheck native foreground reconstruction and actual returned alpha boundaries. Do not split the cycle or stretch
   the new return to compensate for the additional margin's pixel cost.
4. Use **exactly the same crop origin, dimensions, scale and padding for every step**. Do not independently trim,
   center, zoom or fit poses. Save the crop-to-original transform and verify reconstruction of native alpha and
   visible RGB. This common coordinate system preserves movement and makes the result referencable to the BMPs.
5. Enumerate compact grids for the complete pose count and cell shape. Account for empty cells, gutters and exterior
   margins. Choose the layout with the best estimated generated sampling under actually observed output shapes.
   Six Goblin poses used a **3-column × 2-row** grid, chronological order left-to-right then top-to-bottom.
   Keep labels and guides in separate review contacts.
6. If enlarging references, use nearest-neighbor so native pixels stay explicit. The selected Goblin references
   were enlarged **2×**. This is input presentation, not newly generated detail.

For `C` columns, `R` rows, padded native cell size `cw × ch` and delivered raster `W × H`, the nominal budget is:

```text
sampling = min(W / (C * cw), H / (R * ch))
```

Include any extra gutters/margins in the sheet dimensions. Optimize within the whole-cycle constraint: tighter
safe shared cropping, a better aspect ratio, fewer unused cells and a larger requested master.
Aim for ≥2 actual generated pixels per native pixel in both axes, preferably ≥2.2; requesting ≥2.5 gives useful
headroom when possible. **User decision, 2026-10-01:** keeping every original step of one animation at one stored
rotation on one submitted sheet and one returned sheet takes priority over reaching 2×. Some monsters therefore
have less than 2× generated detail. Accept those complete sheets after the normal visual and technical review,
with their actual measured sampling and the resolution tradeoff recorded. The physical 2× export remains separate.

**Do not silently split the animation or generate individual poses.** The shared `sheet_checks.py plan` helper can
reduce the pose count to meet its target and suggest overlapping batches. In this method, that suggestion is a
budget diagnostic, not the selected submission scope. Preserve the full cycle unless the user changes that scope.
Do not split or regenerate solely because a complete sheet measures below 2×. Report that shortfall accurately;
interpolation adds no generated detail. Anatomy, original animation steps, detailed materials, alpha and placement
still require review. A user request for a strict minimum in a particular run overrides this default.

Generation-sheet packing and final runtime-atlas packing are different operations. The first preserves a shared
cell/pose coordinate system for imagegen; the latter can trim frames individually because metadata preserves offsets.

## 3. Prepare the separate outline-only input

Derive the guide from native **alpha geometry**, not luminance or colour contrast:

```text
inside = native_alpha > 0
outline = inside AND NOT erode(inside, 3×3 all-ones neighbourhood)
```

For the selected Goblin run, this produces a **one-native-pixel inward silhouette boundary**, including contours
around transparent holes and gaps between limbs. Draw it black on a white sheet; both the interior and exterior
stay white. Enlarge with the same 2× nearest-neighbor transform, yielding a two-input-pixel line.
Use the same common crop, grid, order and cell positions as the colour sheet. Inspect the pair for matching geometry.

There is no filled silhouette, grayscale anatomy shading, crease detection, ridge highlighting, interior hatching
or strengthened muscle contrast. Native colour remains a separate untouched input. The default
[native_guides.py](native_guides.py) contrast-enhancing output is the historical Dragon experiment and is **not**
this outline-only recipe.

The outline is a prompting reference for silhouette, limb ownership and animation steps. It is not a hard model
constraint, an exported material mask, or a stencil for clipping the generated sprite back to low-resolution alpha.
Keep genuine generated alpha and refined contours, then review native-relative anatomy independently.

## 4. Give the three inputs distinct authority

| Input | Controls | Does not control |
| --- | --- | --- |
| 1. Untouched packed native colour animation | Every step's pose, proportions, camera, placement, equipment coverage/ownership and native base colours | Low-resolution pixel blocks or a compulsory blocky rendering style |
| 2. Identically packed outline-only animation | Silhouette boundaries, transparent gaps, overlapping limbs and native motion geometry | Lighting, texture, muscle shading, black output strokes or flat white fill |
| 3. Selected detailed enhanced appearance | Fine skin/face detail, material finish, leather grain, seams, rivets, metal wear and coherent painted shading | Pose, gait, larger muscles, broader proportions or equipment absent from the native art |

Use the same creature's selected detailed appearance, preferably a corresponding view. The final Goblin run used
the previous detailed first walk pose for each view from `tight_front_20260930`, copied into
`redo_2x/references/walk_<view>_previous_detail.png`. It did not use the washed-out trial as the appearance target.
Reuse adequate identity art. If none exists, let the first useful complete animation/view sheet establish it from
the native colour and outline inputs, then inspect it and carry that selected appearance as the third input in
subsequent sheets. No extra disposable identity call or new approval pause is needed.

If the appearance reference makes imagegen copy its pose or bulk, use a relevant crop from that selected art and
reinforce native geometry authority. Do not compensate by removing its fine-detail guidance.
Submit explicit local image paths in a known order and retain their hashes; do not depend on incidental recent
conversation images.

## 5. Generate the complete animation in one request

Submit all three inputs together and request exactly one RGBA output containing the **entire** target animation
for **one stored view**. Generate the base palette once; derive other native palette variants deterministically.
Different views/actions are separate complete-sheet jobs. Retain original frame counts and native timing;
state the exact sprite count in the prompt. A one-bitmap standing/corpse animation needs one sprite on its sheet,
not an invented cycle. Keep alternative palette colours out of the base-generation request; describe those in the
mask/recolour metadata instead.
do not invent in-between steps or use one all-actions/all-directions monster sheet.

Adapt this prompt to the actual creature and action; the native filenames, dimensions and visible limb structures
must come from the inventory:

```text
TASK CONTEXT — [MM6/MM7/MM8] FANTASY-GAME ASSET RESTORATION: This is an upscale and
faithful restoration of an EXISTING Might and Magic [VI/VII/VIII] fantasy role-playing
game sprite asset, using the supplied original animation bitmaps. Restore the existing
fantasy-game character and its original animation; preserve its native costume,
material coverage, anatomy and poses. The request is game-art restoration.

Generate exactly ONE COMPLETE [creature, action, stored view] animation sprite sheet:
all [N] original steps together, in a [C]-column by [R]-row grid.

Image 1 is the untouched original complete animation. It is the authority for each
cell's pose, proportions, anatomy, camera, placement, equipment ownership/coverage
and base colours.

Image 2 is the separate matching OUTLINE-ONLY sheet. Thin silhouette boundaries and
transparent gaps guide geometry and animation steps ONLY. Black lines and white
interior/exterior convey no lighting, texture or shading and must not appear in
the result. There are no internal contrast guides.

Image 3 is the selected DETAILED enhanced appearance reference. Preserve its fine
facial planes, expressive eyes/mouth/teeth, wrinkles and skin texture, natural
small-scale muscle shading, leather grain/seams, crisp rivets, metal wear and
weapon detail. Carry that detailed finish coherently through the entire animation.
Do not copy its pose, broader muscles, altered proportions or equipment absent
from native art; Images 1 and 2 remain geometry authority.

Keep detailed painted/pre-rendered fantasy game rendering, native material colours
and consistent [selected lighting]. Preserve natural contrast and light/shadow
modelling. Avoid only artificial large blotchy shading bands, exaggerated black
muscle grooves and copied guide strokes. Preserve fine detail: no low-contrast
flattening, smoothing away texture, waxy/plastic skin, blur, flat untextured surfaces,
pixel blocks, dithering, sharpening halos or noisy pseudo-detail.

Match the original anatomy and animation in EVERY cell: shoulder–elbow–wrist–finger
and hip–knee–ankle–toe chains, lengths, widths, joint locations/bends, near/far limb
ownership, crossings, foreshortening and weapon grip. Keep exactly which foot is
lifted/planted, torso lean, head angle and body bob at each step. No fused/swapped/
extra limbs, invented joints, duplicated poses, new gait or added muscle bulk.
Anatomy fidelity has priority over decorative additions.

Native chronological order is [ordered frame IDs], left-to-right then top-to-bottom.
Every cell uses common native crop [left, top, right, bottom], cell size [cw × ch],
on actor canvas [native dimensions/pivot]. Preserve native position and scale;
never independently center or zoom frames. Keep [padding] native-pixel safety
padding and all tips visible. Fill the planned grid without oversized empty margins.
Request a large [target W × H] master at [target] actual generated pixels per native
pixel; detail must be reconstructed, not obtained by interpolated enlargement.
Exactly one complete-animation RGBA image with genuine transparent background
and gaps. No grid, labels, paper, painted checkerboard, ground or cast shadows.
```

For wings, tails, quadrupeds or unusual anatomy, replace the humanoid chains with the native structures and name
the confusing overlaps explicitly. For standing/attack/hit/fidget, describe those actual steps rather than a gait.
The [exact successful front-walk prompt](mm6_goblin/outline_walk_detail_v2/redo_2x/prompts/walk_0_sheet_v1.txt)
is retained unchanged, including its requested master size and correction wording.

Two preceding failures explain the crucial distinction:

- **Strong internal contrast guides:** strengthened creases/ridges encouraged odd interior bands and heavy muscle
  shading. Replacing that guide with pure alpha-boundary outlines separates geometry from appearance.
- **Washed-out correction:** requesting minimal texture, low contrast or even untextured skin suppressed desired
  detail. The final batch restored the previous detailed appearance input and explicitly preserved wrinkles,
  material texture and natural shading while excluding the specific artificial bands.

If a returned sheet fails pose or appearance review, correct the affected complete-sheet job and preserve failed
raw returns, prompts and references. A sheet-level retry should retain the same native crop/order and selected
appearance rather than restarting unrelated accepted actions.

## 6. Check delivered detail, transparency and every animation step

Compare every generated step to the matching native step in compact sequence contacts, and inspect representative
faces/materials at 100% and at final export size. Check joint bends, limb length/thickness/ownership, fingers/toes,
weapon hand/grip, equipment coverage, planted versus raised feet, body bob and the last-to-first transition.
Native reference plus outline improves guidance; it does not prove exact anatomy. Use timed playback for unresolved
motion questions or requested playback review, and record whether contacts or playback were actually inspected.

Separate **requested master size**, **delivered raw pixels**, **registered generated sampling**, and **physical
export tier**. A 2× reference or a 2× PNG export is not evidence of 2× newly generated detail. Measure sampling
after the complete uniform registration, including integer resize rounding.

The five selected Goblin returns illustrate that distinction:

| Stored walk view | Common native crop, exclusive right/bottom | Native padded cell | Delivered full sheet | Minimum registered sampling |
| --- | --- | --- | --- | --- |
| 0, front | [54, 31, 297, 295] | 243×264 | 1472×1069 | 2.017× |
| 1, front oblique | [94, 31, 326, 295] | 232×264 | 1440×1092 | 2.066× |
| 2, profile | [89, 32, 361, 295] | 272×263 | 1560×1008 | 1.910× |
| 3, rear oblique | [85, 31, 343, 295] | 258×264 | 1516×1038 | 1.957× |
| 4, back | [85, 31, 327, 295] | 242×264 | 1470×1070 | 2.023× |

These were 3×2 sheets with 2× nearest-neighbor reference enlargement and six-native-pixel padding. All source
Goblin canvases were 355×289, with bottom-center pivot (177.5, 289). The front prompt requested 3056×2224 and
≥2.5× detail; the tool delivered 1472×1069. All five returned approximately 1.5 megapixels. This is an observation
of these calls, not a declared tool limit. Profile and rear-oblique returns fell below the then-required detail gate.
Under the later complete-animation policy they can be accepted after the normal review, with their sampling reported;
this document change does not itself freeze or replace the worked Goblin package's acceptance record.
The selected visual technique does not erase that recorded shortfall or imply completed placement acceptance.

Inspect real PNG alpha rather than its displayed background. Preserve clean supplied RGBA; do not recover magenta
or repaint the interior unnecessarily. In this Goblin run, reviewed near-transparent scatter at alpha ≤4 was removed;
that setting is recorded in [processing.json](mm6_goblin/outline_walk_detail_v2/redo_2x/processing.json) and is not a
universal threshold for thin features, translucent creatures or effects.

Tight returned poses may cross nominal cell boundaries. The selected run used shared connected-body extraction to
retain complete bodies and attach detached foreground details to the appropriate pose. Check the expected body
count/order and ensure every foreground component is assigned once, including sword tips and spikes.
Preserve raw extraction rectangles for registration. Multiple disconnected bodies/effects need an appropriate
existing extraction mode; do not blindly assume one component per pose or cut at a grid line through visible art.

Inspect cleaned and atlas-extracted contours on both light and dark backgrounds. Use the pipeline's automatic
residual-spill diagnostic, then correct only visually confirmed fringe RGB before resizing/masks. Protect intended
purple/grey metal, warm skin, gold, leather and legitimate translucent colours; a chroma flag is not a removal rule.
Do not blur interior texture to fix an edge.

## 7. Preserve registration, timing and variants on export

Map extracted cells back through the shared sheet transform into native actor coordinates, using one uniform scale
for the coherent animation/view. Never equalize individual pose bounding-box heights, stretch axes independently
or warp limbs to conceal generated anatomy changes.

The worked Goblin sheet-coordinate registration, with a 2× export tier, uses:

```text
s = min(raw_width / (C * cw), raw_height / (R * ch))
raw_to_2x = 2 / s
cell_origin(i) = ((i % C) * raw_width / C, floor(i / C) * raw_height / R)
translation(i) = round(
    2 * native_common_crop_origin
    + raw_to_2x * (extracted_raw_rectangle_origin(i) - cell_origin(i))
)
```

This is the saved run's nominal sheet mapping, not proof that imagegen kept every anatomical landmark in place.
Inspect corresponding landmarks at native logical size or larger; independently check a second feature that did
not determine the transform. Keep one anatomical scale, preserve actual native foot lifts/bob and record reviewed
translation corrections instead of normalizing all feet onto one ground line.

Resize premultiplied colour and alpha together, e.g. `RGBA → RGBa → Lanczos resize → RGBA`. Keep expanded storage
canvases when refined contours extend outside the Goblin's 710×578 physical canvas at the 2× tier, recording origins
even when negative. Do not silently clip or clamp offsets. Derive effective sampling from the actual raw-to-export
resize, including rounding; preserve cleaned high-resolution masters separately.

Use the matching existing family exporter/schema and the shared packer:

- Keep aligned masters, trimmed rectangles, logical canvas/pivot, crop origins, physical tier, mirrors and identical
  base/material-mask atlas rectangles. Verify exact crop reconstruction and atlas extraction.
- Preserve native frame order, per-frame durations and scales, held/reused frames, no-image actions and all stored/
  mirrored view bindings for **every palette**. The Goblin's native variants have timing differences.
  Retain the native corpse pixel alias `gobdyf0 → gobdyd0`.
- Author soft recolorable-region coverage on the enhanced pixels. The input outline guide is unrelated to these
  output material masks. Derive other palette appearances with fixed documented colour ramps/operations; protect
  detail and alpha, keep the base preset an exact bypass and verify matching mask coverage.
- Run the pipeline's exact native-anchor and animation-binding checks on registration and exported metadata,
  including half pixels and mirrors. Arithmetic fidelity and anatomical acceptance are separate checks.

The legacy Goblin exporter requires its project root to be explicitly redirected to the new project; running its
historical default would target older artifacts. Its exported action-level scale also needed each animation step's
native scale copied from the saved per-palette group binding. The generic MM6 `export_run.py` is not an unmodified
drop-in for this retained-frame Goblin schema. Reuse the applicable exporter and validate its real output rather
than treating all worked examples as interchangeable commands.

When replacing only walking, retain the other actions and their provenance unchanged. Load the new package in the
existing MM6 reviewer for offset calibration, size calibration and acceptance. Save adjustments through its existing
mechanism, rebuild/apply them through the authoritative export path when required, and verify mirrored views and
palette bindings. Bind acceptance to the current artifact hashes; changed art or placement needs fresh affected
review. Selecting a technique does not copy an older package's acceptance to the new result.
Stage artwork without installing it into gameplay unless that scope is requested.

## Saved evidence and reusable tools

The reference project retains the exact inputs and outputs needed to reproduce or resume this method:

- [Native inventory](mm6_goblin/outline_walk_detail_v2/sources.json) and
  [run ledger](mm6_goblin/outline_walk_detail_v2/redo_2x/run.json): source/pose mapping, reference roles,
  crop/grid, prompts, input/output hashes, selected raw versions, measured limitations and retained actions.
- Front submission inputs:
  [native colour sheet](mm6_goblin/outline_walk_detail_v2/redo_2x/references/walk_0_native_sheet.png),
  [outline-only sheet](mm6_goblin/outline_walk_detail_v2/redo_2x/references/walk_0_outline_only_sheet.png),
  [previous detailed appearance](mm6_goblin/outline_walk_detail_v2/redo_2x/references/walk_0_previous_detail.png);
  [exact prompt](mm6_goblin/outline_walk_detail_v2/redo_2x/prompts/walk_0_sheet_v1.txt) and
  [raw returned sheet](mm6_goblin/outline_walk_detail_v2/redo_2x/raw/walk_0_sheet_v1.png).
- [Processing](mm6_goblin/outline_walk_detail_v2/redo_2x/processing.json),
  [registration](mm6_goblin/outline_walk_detail_v2/redo_2x/registration.json),
  [runtime/reviewer manifest](mm6_goblin/outline_walk_detail_v2/redo_2x/manifest.json) and
  [validation](mm6_goblin/outline_walk_detail_v2/redo_2x/validation.json).
- Compact review evidence:
  [front/profile sequences](mm6_goblin/outline_walk_detail_v2/redo_2x/review/assembled_sequences_2.png),
  [rear/back sequences](mm6_goblin/outline_walk_detail_v2/redo_2x/review/assembled_sequences_3.png) and
  [edge contacts](mm6_goblin/outline_walk_detail_v2/redo_2x/review/edge_current.png).

Shared commands from repository root, replacing `PROJECT` and `RAW.png` with the actual existing paths:

```sh
python3 level_generation/creatures/sheet_checks.py plan --poses 6 --cell 243 264 --target 2.2
python3 level_generation/creatures/sheet_checks.py check RAW.png --cell 243 264 --grid 3 2 --poses 6
python3 level_generation/creatures/mm6_remaining/redo_2x/stage_result.py PROJECT walk_0_sheet RAW.png
python3 level_generation/creatures/mm6_remaining/redo_2x/extract_run.py PROJECT
# Register/export using the matching existing family/schema, then:
python3 level_generation/creatures/mm6_remaining/redo_2x/review_sequences.py PROJECT
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py --check \
  --package PROJECT/redo_2x/manifest.json --state-dir PROJECT/acceptance_state
```

Recheck planner pose count: keep the complete animation even if its suggested batch is smaller. The planner's
historical envelopes are observations, not service limits; use current output evidence. Record resolution shortfalls
as measured limitations under the complete-animation policy, never as fabricated ≥2× detail.
Reuse project metadata, shared preparation/extraction/packing tools and the existing reviewer. A new creature
does not need its own Python suite, viewer, duplicate audit format or separate per-frame prose.
