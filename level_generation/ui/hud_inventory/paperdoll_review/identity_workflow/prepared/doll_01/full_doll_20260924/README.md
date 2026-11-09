# PC01 restoration from the assembled original

This trial uses the **original** `pc01bod`, `pc01rhd`, and `pc01lhu` sprites assembled in the
empty-hand pose at their `character_data.txt` and `doll_types.txt` coordinates. The assigned
original avatar portrait is the facial reference. Open [review.html](review.html) to compare
the source, restored full figure, and exact-canvas diagnostic.

`make_original_assembly.py` writes `original_assembled_empty_x2.png` and its nearest-neighbor
4× presentation copy. `original_assembly.json` records the source hashes and x2 placements.
The original assembly was the edit target for `raw_original_assembly_v2.png`. V3 and v4
refined that result, but v4 still retained visibly enlarged source-pixel detail. V5
(`raw_detail_repaint_v5.png`) is a new high-detail repaint. It uses the sharper v1 figure as
its edit target, v4 only as the seamless arm/geometry reference, and the assigned portrait
for identity. V1 alone is rejected because of the bracer mismatch in `test_img/2040.png`.
The built-in imagegen tool made all returns with genuine transparent alpha. The exact prompts
are in [submitted_prompts.md](submitted_prompts.md),
[submitted_prompt_v4.txt](submitted_prompt_v4.txt), and
[submitted_prompt_v5.txt](submitted_prompt_v5.txt); `HASHES.sha256` records the input and
output hashes.

**Status: unapproved full-doll reference.** V5 has finer face, skin and leather detail,
complete visible fingers, and continuous forearm bracers. It is not split into game sprites,
selected by the main browser, accepted by `queue.py`, or installed. The original `pc01lhu`
and `pc01rhd` source sprites touch their bottom canvas edges. After fitting v5 to the
original stage silhouette, v5 also has visible alpha on the bottom row of both existing limb
rectangles; `pc01rhd` also reaches the right edge. Cropping it to the frozen 52×108 and
84×170 x2 canvases would cut visible art. `fit_original_vs_v5_boxes.png` shows the geometry.
The aligned image is a diagnostic nonuniform fit, not an approved registration transform.
Do not paste the original alpha masks over displaced generated limbs to hide this mismatch.

The next step is a targeted in-place fit of the two open arms against the exact rectangles,
or an explicit canvas/placement contract change if complete fingers cannot fit there. Only
after the empty-hand pose fits should the one-hand, shield, and two-hand limb states be made
from the same body and bracer material.

## Two-pose sheet requested after the full-doll trial

The [two-pose review](two_pose_review.html) follows the simpler proposed sequence: assemble
the naked and `pc01rhu` held poses from native parts at their original game-table offsets,
place them in one row of two equal transparent cells, and supply the original avatar as a
separate identity reference. `make_two_pose_sheet.py` makes the 700×756 x2 source sheet;
the held cell intentionally omits `pc01rhb`, which is a later foreground layer. Three
imagegen returns were preserved as `raw_two_pose_sheet_v1.png` through `v3.png`, then split
exactly in half by `split_and_check_two_pose.py`. V1 and V2 had odd widths; the processor
adds one transparent pixel at the far right to obtain equal halves without changing art.

The proposed mask gate fails for all three returns. Whole-pose alpha-128 IoU for a direct
split/resizing to the original 350×756 x2 cell is V1 **0.555 / 0.636**, V2 **0.739 / 0.628**,
and V3 **0.623 / 0.608** (empty / held). Even a *diagnostic*, single shared nonuniform fit
derived from the empty cell only gives V1 **0.804 / 0.730**, V2 **0.818 / 0.705**, and V3
**0.773 / 0.560**. None reaches the 0.85 IoU guard. V2 also has only three distinguishable
fingers plus a thumb in the held hand; V3 restores four fingers plus thumb but worsens the
grip mask. The item test draws sword #1 at its unchanged x2 position (42, -8), without the
finger-over-sword layer, to expose rather than conceal the location mismatch.

**No surgical extraction is justified yet.** The raw sheets, exact split halves, mask maps,
item-placement previews, source hashes, and reports are retained. No `pc01bod`, `pc01lhu`,
`pc01rhd`, `pc01rhu`, or `pc01rhb` target was accepted, selected or installed from them.

## Five-digit grip correction

The right figure in V2 had a thumb and only three distinguishable fingers. A full-sheet
imagegen correction twice repeated that error. A close-up generation produced a proper compact
grip with a thumb and four curled fingers. `place_corrected_grip.py` places those generated
hand pixels into the original V2 sheet at its existing cuff/wrist position, preserving the
rest of V2 byte-for-byte. The output is
`two_pose_v2_five_digit_grip_composite.png`; `five_digit_grip_before_x4.png` and
`five_digit_grip_after_x4.png` show the anatomy correction. The placement report confirms
that no pixel outside the local hand rectangle changed. This is a **visual anatomy repair**,
not an equipment-fit acceptance: direct held-pose mask IoU remains about 0.628, below the
0.85 guard. No x/y item offsets or game assets were changed.

`make_browser_trial.py` prepares the two 350×756 transparent x2 full-stage images from
that corrected sheet using one shared transform. The main
[interactive paperdoll browser](../../../../index.html?doll=1&trial=1) can show them under
the existing equipment layers through its **Use PC01 five-digit full-doll trial** toggle.
The browser keeps item coordinates and layering from the game tables. This is an experimental
placement preview, not a per-sprite extraction or queue acceptance.
