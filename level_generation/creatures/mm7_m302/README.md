# MM7 dwarf male peasant — validated staged restoration

All 84 family-owned native frames are restored: five standing views, 40 walk poses,
30 reaction poses, four fidget poses, four collapse poses and one corpse. This includes
four unreferenced reaction frames m302nf1..4. Native descriptor actions, including attack
and shoot aliases to walking, remain unchanged. The nine descriptor bindings 322..330
retain their native durations, mirrors and scale 0.799988.

Open viewer.html offline to compare native and restored animations, palettes and placement.
The native logical canvas is 256×256 with bottom-center pivot (128,256). Every enhanced
frame is registered at 2× with one scale calibration per generated batch and native
baseline translation. The atlas is 2048×2898, with matching RGB8 material masks, four-pixel
crop padding and three-pixel invisible RGB extrusion. Base RGBA8 plus shared RGB8 mask
occupy 41,545,728 bytes (39.62 MiB); derived preview pages are offline review artifacts.

The base retains green clothes, brown beard and leather, pale fleece, beige-gray trousers
and a rough wooden club. Thirteen accepted sheets supply all base artwork. Fifteen
successful generations are preserved: rear walk v1 was rejected for a clipped boot;
collapse v1 was rejected for its first beard pose. Their v2 corrections are accepted.
One failed rear-walk v2 call and its exact retry are recorded in generation.json.

Palettes 58,303,304,305,307,308,309,310,311 share this base. Mask R selects enhanced green
cloth; G selects enhanced brown hair; B is zero. Hair selection uses cap-adjacent enhanced
material components and 24 reviewed pose polygons, including hands crossing the beard
and hair behind the club. Native palette entries calibrate separate deterministic RGB
matrices for cloth and hair. Palette 58 bypasses recoloring exactly. Skin, club, fleece,
leather and alpha remain unchanged outside the masks. No palette artwork was generated.

All 84 native/base pairs, all 756 frame/palette combinations and cleaned/packed light/dark
edge closeups were inspected. Corrected boots, backward-fall beard, rear napes and fidget
hand exclusions pass review. Offline browser captures verify white-hair fidget placement
and the mirrored blue-cloth walk. Timeline/flag checks preserve all native animations;
source hashes, uncut raw poses, crop reconstruction, atlas extraction, masks and variant
alpha checks pass validation.json. The edge audit reports zero residual candidates above
32. Acceptance hashes are in review/acceptance.json.

Prompts, references, original raw outputs, rejected versions, selected checkpoints and
processing settings remain in this directory. Fine generated detail and single-background
alpha are interpretations of the native art; the original BMP files are untouched.
Nothing is installed into gameplay.

To reproduce after a demonstrated defect, run from the repository root:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m302 --tone 0.80
python3 level_generation/creatures/mm7_m302/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m302
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m302
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m302
```

Changes to alignment require retracing affected hair polygons. Reinspect affected poses,
all derived variants and edges, then renew acceptance hashes and refresh the inventory.
