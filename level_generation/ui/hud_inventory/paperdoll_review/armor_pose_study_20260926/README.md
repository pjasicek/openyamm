# Accepted-base armor pose study — 2026-09-26

The accepted empty-hand armor can be the immutable base for every weapon-held variant. The character's
right arm is normally on the **left of the image**. Preservation must be enforced by copying the accepted
RGBA outside an explicitly bounded arm region, including all partially transparent contour pixels.
An image-generation prompt alone cannot guarantee that invariant.

This is a feasibility audit and isolated compositing experiment, not a new active review pass. No imagegen
calls were made. No approved file, approval, placement, ledger or active browser overlay was changed.
Inputs are frozen by hash against `acceptance_snapshot_20260926_1322`.

## Measured scope

All 270 native pairs exist and have matching dimensions. All 270 empty-hand bases are approved/staged.

| Body type | Native pairs identical | Native pairs different | Total |
| --- | ---: | ---: | ---: |
| Male | 18 | 36 | 54 |
| Female | 29 | 25 | 54 |
| Minotaur | 47 | 7 | 54 |
| Troll | 47 | 7 | 54 |
| Dwarf | 47 | 7 | 54 |
| Total | 188 | 82 | 270 |

Of the **256 still-pending held variants**, **177** can reuse the accepted empty-hand file exactly; **79**
need an arm-pose assessment/edit. The other 14 held variants already have approvals (5 staged, 9 ledger).
Those historical approvals and exact files remain intact. Future consistency replacements for them must be
explicitly tracked rather than silently treated as the same approved image.

Existing restored held candidates differ outside the provisional arm region in **264/270** pairs, including
alpha differences. Whole-image reuse of those independently restored held candidates therefore fails the
requested preservation rule, even when both pictures look similar. Their arm portions remain possible donors.

Some native pairs contain palette/dither differences well outside the right arm (notably `6chain3v1`), so a
raw RGB-difference bounding box is not a safe edit mask. The native alpha changes, local arm geometry and
visually checked shoulder/forearm boundaries must define the editable region.

## Runtime and reusable tooling

- `game/gameplay/GameplayScreenRuntime.cpp`, `resolveEquippedItemHudTextureName`: `vNa` is preferred without
  a main-hand weapon and `vN` with one. The browser resolver agrees.
- `resolveCharacterEquipmentRenderRect` and the browser's `itemLayer` both use the same item/body-type point
  from `complex_item_pictures.txt` for either armor pose. Saved armor adjustments already use that shared key.
  Keeping the original canvas and origin preserves those offsets; no whole-image resizing or recentering is needed.
- `tools/mm9_import_discovery/audit_mm9_armor_pose_pairs.py` already derives local arm masks from native pairs.
  Its derivation/validation functions are useful for this audit. Its MM9 promotion and `lock_common_region`
  functions must not be run on these assets: they can reapply native binary alpha, which would change the
  approved restored contour. Here the accepted restored image, not the native alpha, owns every protected pixel.

## Proposed implementation

1. Pin each accepted `vNa` file, hash, dimensions and saved placement as the base. Never modify this source.
2. Where the native poses are identical, prepare `vN` as the exact accepted file (or a source alias to it).
   There is no artwork edit or generation step for those pairs.
3. For changed poses, define one small mask covering the old and new right-arm coverage plus the necessary
   shoulder/elbow join. This mask includes the area where the lowered sleeve must be removed. Keep chest,
   opposite arm, waist, legs and their complete alpha contours outside it. Check native-derived masks visually
   and enlarge/refine them only where the accepted arm geometry and its actual attachment require it.
4. First recover the complete existing held-arm artwork from its retained master if the prepared crop is poor.
   Align only that arm at the shoulder/elbow/cuff anchors, matching the accepted material at the join. Prefer
   reusing or locally deforming the accepted sleeve if the donor design differs. Clear the old sleeve inside
   the allowed region; simply alpha-compositing another arm over it would leave a double arm or dangling pixels.
5. If local imagegen is necessary, supply the accepted armor as the material reference and the native held pose
   as the geometry guide. Use only the returned arm patch. Discard every returned pixel outside the fixed edit
   region, even if the tool appears to have preserved the body. Keep any feathering entirely inside the region.
6. Build the output as an exact copy of the accepted base and replace only the masked patch. Assert byte-for-byte
   RGBA equality outside the mask, zero alpha differences outside it, and unchanged canvas, origin and offsets.
7. Review the arm join/cuff and grip on the actual doll, toggling empty/one-hand/two-hand poses. Pixel equality
   proves preservation; it does not prove the arm anatomy, seam or fit. Publish only the new held candidates for
   review; the accepted empty-hand images remain approved throughout.

## What the probes show

[audit.json](audit.json) records all source/candidate hashes and measurements; [pairs.csv](pairs.csv) lists each
pair's exact-reuse versus local-edit route. `audit.py` can reproduce the audit and nine isolated comparison images.
The orange region in each comparison is the provisional allowed edit mask. The third column is an intentionally
simple donor-arm splice, not approved production artwork. For all 270 computed composites, RGBA outside that
region is exactly identical to the accepted base.

- [Identical native pose: Crude Leather, male](probes/7item066v1/comparison.png): copying the accepted base avoids
  unnecessary changes in chest shading and silhouette present in the separately restored held image.
- [Noble Plate, male](probes/7item078v1/comparison.png): the local transfer changes the forearm direction while
  retaining the accepted torso, opposite arm and lower armor. It still needs equipped-pose review.
- [Noble Plate, female](probes/7item078v2/comparison.png): the arm is small and local; donor cuff/interior and join
  need checking on the doll.
- [Noble Plate, minotaur](probes/7item078v3/comparison.png),
  [troll](probes/7item078v4/comparison.png), and [dwarf](probes/7item078v5/comparison.png): a naive splice leaves
  visible silver wedges/irregular joins at the arm attachment. Refine the mask and align the donor before use.
- [Wetsuit, dwarf](probes/7item299v5/comparison.png): accepted head/body/legs stay fixed, but the undersleeve seam
  needs cleanup. The independently restored held donor also changes the feet, demonstrating why it cannot own
  the complete output.
- [Plate Armor, male](probes/7item076v1/comparison.png) and
  [Chain Mail, male](probes/6chain3v1/comparison.png): small shoulder/sleeve changes; distant native palette noise
  must not become permission to change the torso or skirt.

Conclusion: exact preservation outside the right-arm region is straightforward and testable. Most pending
variants require no generation at all. The remaining 79 can be attempted with existing art first; this study
does not claim that every one will reach acceptable arm/seam quality without a targeted generation fallback.
