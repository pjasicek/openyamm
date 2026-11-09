# Complete MM6 packed-outline review collection

This is the single selected review namespace for all **60 MM6 families, 3,486 native bitmaps and
174 family palette appearances**, exported at **2× physical resolution**. It explicitly references
the chosen packages instead of copying several gigabytes or rediscovering historical attempts.
There are no automatic fallback packages in this queue. The collection pins each manifest and
all displayed native/restored pixels with SHA-256; changed artwork fails visibly at startup.

## Open the acceptance app

From the repository root:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm6_packed_outline_collection_20261001/collection.json \
  --port 8767
```

Open <http://127.0.0.1:8767/>. To check the selection without serving, use the same command with `--check`.

The live reviewer runs in the transient user service `openyamm-mm6-review-8767.service`, so it stays
available after the launching chat session ends. To start it again after a reboot or an intentional stop:

```sh
systemd-run --user --unit=openyamm-mm6-review-8767 --collect \
  --property=WorkingDirectory=/home/pjasicek/github/OpenYAMM \
  /usr/bin/python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm6_packed_outline_collection_20261001/collection.json \
  --port 8767
```

Use `systemctl --user stop openyamm-mm6-review-8767.service` to stop this service.

The existing app provides every native animation/view, unused-master browsing, palette selection,
offset dragging/nudging, fixed guides, uniform size trials, color previews, frame flags and family
acceptance. It opens paused. Use Play to inspect motion. Size and placement controls save proposals;
they do not resample or rewrite the source PNGs. For body proportions, prefer your manual anatomical
review; the optional Match family height & bottom button fits silhouettes including weapons/wings.

This collection's fresh manual decisions and edits live only in:

- `review_state/frame_fixups.json` — per-frame offsets, size factors/anchors, guides and color trials.
- `review_state/decisions.json` — your artifact-bound family decisions and saved edit snapshots.

The files appear on first save. Earlier reviewer decisions are not imported. Export checkpoints
and decisions from the app when needed. No runtime installation is performed.

## Exactly which art is selected

`collection.json` is authoritative. Paths are relative to this directory. Each family has exactly
one selected `manifest`, with hashes, frame/palette counts, source status and preserved rebuild metadata.
The existing default reviewer queue and `selected_packages.json` are not consulted.

The nine video-processed families are Cockatrice, Flying Demon, Flying Dragon (`drg1`;
native descriptor `BDragonFly`), Harpy, Gargoyle, DragonCover, Demon Queen, Reactor and Cactus.
Together they retain **90 complete sheets, 486 native bitmaps and 21 palette appearances**.
The first seven select finished `mm6_packed_outline_video_x3_20261001` packages, whose
`*_video.png` sheets and finished atlases are selected. Their `*_baseline.png` and `cleaned/`
files remain pre-ESRGAN references.

**Reactor follows the user's direct-native override:** all 31 original bitmaps, decoded with palette
835 and index-0 transparency, were processed with `realesr-animevideov3` at x3. No imagegen
artwork or old generated silhouettes/placement are used. Its package is
`mm6_reactor_native_video_x3_20261003/redo_2x/`, with per-bitmap `masters_3x/`, native-coordinate
2× masters/atlases and five complete animation sheets. Model output at x3 is distinct from native
source sampling (1×). The whole review collection remains at 2× physical export resolution.

**Cactus follows the same direct-native override:** all 89 original bitmaps, decoded with palette
955 and index-0 transparency, were processed with `realesr-animevideov3` at x3. Its package is
`mm6_cactus_native_video_x3_20261003/redo_2x/`, retaining `masters_3x/` and exporting 2× review
masters/atlases. Six complete playback sheets and one unused-art sheet cover every native bitmap.
The native Center anchor, 13 pixel aliases, five unused frames, sparse particle endings and two
empty bitmaps are preserved. No imagegen artwork supplies this package. Static visual screening
is complete; manual animation, placement, size and family acceptance remain pending.

All other families select the appropriate latest packed-outline project. The original complete
animation at one stored rotation was submitted together with untouched native colour, separate
outline-only geometry and detailed appearance references. Actual generated sampling, including
reviewed values below 2×, remains separate from export enlargement and ESRGAN reconstruction.

## Preserved masters for a later rebuild

Every entry retains the selected high-resolution `selected_raw_sheets` and their hashes,
`rebuild_metadata` paths/hashes (registration, source, processing, calibration and generation
records where present), final `aligned_masters_2x` and `material_masks_2x`. The video entries also
retain their `upscale.json` and pre-finishing source ledgers, crop/frame-order mapping and final
complete sheets. Raw-sheet `registered_frames` is membership, not a replacement for chronological
order in the native run/animation metadata.

Keep these referenced source directories. Later, apply your saved size/offset choices from these
masters, preserving alpha, masks, timing and native anchors; validate generated sampling and
independent anatomy before accepting a rebuilt package. Current app edits remain reversible.
Changing a selected package requires updating its collection hashes and reviewing that new artifact;
old decisions are never silently transferred.

Goblin now selects all 59 bitmaps from the latest method: 30 unchanged outline-only walking frames
and 29 regenerated non-walk bitmaps from nine complete animation/view submissions, including the
native corpse pixel alias. Every new submission attached native colour, separate outline-only geometry
and detailed appearance art. Its new poses await user offset, size and animation acceptance. Exact
prompts, input hashes and selected returns are retained in [its run ledger](../mm6_goblin/outline_complete_20261001/redo_2x/run.json).

## Explicit retained-art exceptions

This is complete selected coverage, rather than a claim that every bitmap was regenerated by the
newest method. The following earlier poses are intentionally retained in the chosen packages:

- **Druidess:** one unused fidget bitmap (`dru1fib0`) retains the user-authorized earlier 2× restoration.
- **Earth Elemental:** six walk-view-2 and five death bitmaps retain the user-authorized older composite art.
- **Male peasant 4:** rear standing (`natmsta4`) retains the explicitly selected earlier detailed pose.

These 13 retained earlier bitmaps are recorded per family; failed or rejected alternate sheets are
not selected as final coverage. The other families' pipeline visual acceptance and the video finishes'
static screening remain provenance. Manual decisions are recorded per artifact in `review_state`; generated coverage does not itself accept a family.
Goblin's residual-spill diagnostics remain in its package for review. The two demon families retain palette 496 for shared
native fire/death effects within their three family appearances, not a fourth whole-family variant.

## Selected family packages

| Family | Native bitmaps | Palette appearances | Selected finish | Package |
| --- | ---: | ---: | --- | --- |
| MM6 Archer | 58 | 3 | Packed outline → 2× | [mm6:arc1](../mm6_packed_outline_20260930/mm6_arc1/redo_2x/manifest.json) |
| MM6 Barbarian | 57 | 3 | Packed outline → 2× | [mm6:bar1](../mm6_packed_outline_20261001_batch15/mm6_bar1/redo_2x/manifest.json) |
| MM6 Bat | 78 | 3 | Packed outline → 2× | [mm6:bat](../mm6_packed_outline_remaining8/session_02/mm6_bat/redo_2x/manifest.json) |
| MM6 Beholder | 48 | 3 | Packed outline → 2× | [mm6:bh](../mm6_packed_outline_20261001_batch15/mm6_bh/redo_2x/manifest.json) |
| MM6 Bloodsucker | 78 | 3 | Packed outline → 2× | [mm6:bld](../mm6_packed_outline_remaining8/session_02/mm6_bld/redo_2x/manifest.json) |
| MM6 Cleric | 59 | 3 | Packed outline → 2× | [mm6:cle](../mm6_packed_outline_20260930/mm6_cle/redo_2x/manifest.json) |
| MM6 Cobra | 59 | 3 | Packed outline → 2× | [mm6:cob](../mm6_packed_outline_20261001_batch15/mm6_cob/redo_2x/manifest.json) |
| MM6 Cockatrice | 59 | 3 | Video ESRGAN x3 → 2× | [mm6:ckt](../mm6_packed_outline_video_x3_20261001/mm6_ckt/redo_2x/manifest.json) |
| MM6 Flying Demon | 54 | 3 | Video ESRGAN x3 → 2× | [mm6:wdm](../mm6_packed_outline_video_x3_20261001/mm6_wdm/redo_2x/manifest.json) |
| MM6 Demon | 67 | 3 | Packed outline → 2× | [mm6:dmn](../mm6_packed_outline_remaining8/session_08/mm6_dmn/redo_2x/manifest.json) |
| MM6 Cave Dragon | 59 | 3 | Packed outline → 2× | [mm6:drag](../mm6_packed_outline_remaining8/session_01/mm6_drag/redo_2x/manifest.json) |
| MM6 Flying Dragon | 78 | 3 | Video ESRGAN x3 → 2× | [mm6:drg1](../mm6_packed_outline_video_x3_20261001/mm6_drg1/redo_2x/manifest.json) |
| MM6 Land Dragon | 59 | 3 | Packed outline → 2× | [mm6:drr1](../mm6_packed_outline_20260930/mm6_drr1/redo_2x/manifest.json) |
| MM6 Dragon Cover | 55 | 3 | Video ESRGAN x3 → 2× | [mm6:cdr1](../mm6_packed_outline_video_x3_20261001/mm6_cdr1/redo_2x/manifest.json) |
| MM6 Druidess | 59 | 3 | Packed outline → 2× | [mm6:dru1](../mm6_packed_outline_20261001_batch15/mm6_dru1/redo_2x/manifest.json) |
| MM6 Dwarf | 59 | 3 | Packed outline → 2× | [mm6:dwa1](../mm6_packed_outline_20261001_batch15/mm6_dwa1/redo_2x/manifest.json) |
| MM6 Air Elemental | 24 | 3 | Packed outline → 2× | [mm6:aie1](../mm6_packed_outline_remaining8/session_05/mm6_aie1/redo_2x/manifest.json) |
| MM6 Earth Elemental | 59 | 3 | Packed outline → 2× | [mm6:ert](../mm6_packed_outline_20261001_batch15/mm6_ert/redo_2x/manifest.json) |
| MM6 Fire Elemental | 47 | 3 | Packed outline → 2× | [mm6:fie1](../mm6_packed_outline_20261001_batch15/mm6_fie1/redo_2x/manifest.json) |
| MM6 Water Elemental | 71 | 3 | Packed outline → 2× | [mm6:wel](../mm6_packed_outline_remaining8/session_05/mm6_wel/redo_2x/manifest.json) |
| MM6 Chain Fighter | 59 | 3 | Packed outline → 2× | [mm6:figc](../mm6_packed_outline_20261001_batch15/mm6_figc/redo_2x/manifest.json) |
| MM6 Leather Fighter | 59 | 3 | Packed outline → 2× | [mm6:fgt](../mm6_packed_outline_remaining8/session_03/mm6_fgt/redo_2x/manifest.json) |
| MM6 Gargoyle | 48 | 3 | Video ESRGAN x3 → 2× | [mm6:gar](../mm6_packed_outline_video_x3_20261001/mm6_gar/redo_2x/manifest.json) |
| MM6 Genie | 60 | 3 | Packed outline → 2× | [mm6:djn](../mm6_packed_outline_20261001_batch15/mm6_djn/redo_2x/manifest.json) |
| MM6 Ghost | 48 | 3 | Packed outline → 2× | [mm6:gst](../mm6_packed_outline_remaining8/session_01/mm6_gst/redo_2x/manifest.json) |
| MM6 Goblin | 59 | 3 | Packed outline → 2× | [mm6:goblin](../mm6_goblin/outline_complete_20261001/redo_2x/manifest.json) |
| MM6 Guard | 59 | 3 | Packed outline → 2× | [mm6:gua](../mm6_packed_outline_remaining8/session_03/mm6_gua/redo_2x/manifest.json) |
| MM6 Harpy | 48 | 3 | Video ESRGAN x3 → 2× | [mm6:hrp](../mm6_packed_outline_video_x3_20261001/mm6_hrp/redo_2x/manifest.json) |
| MM6 Hydra | 59 | 3 | Packed outline → 2× | [mm6:hyd](../mm6_packed_outline_remaining8/session_05/mm6_hyd/redo_2x/manifest.json) |
| MM6 Jackalman | 59 | 3 | Packed outline → 2× | [mm6:jak1](../mm6_packed_outline_remaining8/session_03/mm6_jak1/redo_2x/manifest.json) |
| MM6 Plate Knight | 59 | 3 | Packed outline → 2× | [mm6:kni](../mm6_packed_outline_20261001_batch15/mm6_kni/redo_2x/manifest.json) |
| MM6 Lich | 59 | 3 | Packed outline → 2× | [mm6:lch](../mm6_packed_outline_20261001_batch15/mm6_lch/redo_2x/manifest.json) |
| MM6 Lizard Archer | 65 | 3 | Packed outline → 2× | [mm6:lzd](../mm6_packed_outline_remaining8/session_04/mm6_lzd_fidget_stability_20261003/redo_2x/manifest.json) |
| MM6 Medusa | 59 | 3 | Packed outline → 2× | [mm6:med](../mm6_packed_outline_remaining8/session_04/mm6_med/redo_2x/manifest.json) |
| MM6 Merchant | 58 | 3 | Packed outline → 2× | [mm6:mer1](../mm6_packed_outline_remaining8/session_06/mm6_mer1/redo_2x/manifest.json) |
| MM6 Minotaur | 51 | 3 | Packed outline → 2× | [mm6:min1](../mm6_packed_outline_20261001_batch15/mm6_min1/redo_2x/manifest.json) |
| MM6 Monk | 57 | 3 | Packed outline → 2× | [mm6:mnk1](../mm6_packed_outline_20261001_batch15/mm6_mnk1/redo_2x/manifest.json) |
| MM6 Nobleman | 71 | 3 | Packed outline → 2× | [mm6:nobl](../mm6_packed_outline_remaining8/session_06/mm6_nobl/redo_2x/manifest.json) |
| MM6 Ooze | 54 | 3 | Packed outline → 2× | [mm6:ooz](../mm6_packed_outline_remaining8/session_08/mm6_ooz/redo_2x/manifest.json) |
| MM6 Ogre | 60 | 3 | Packed outline → 2× | [mm6:ogr](../mm6_packed_outline_remaining8/session_03/mm6_ogr/redo_2x/manifest.json) |
| MM6 female peasant 1 | 59 | 3 | Packed outline → 2× | [mm6:pfem](../mm6_packed_outline_remaining8/session_06/mm6_pfem/redo_2x/manifest.json) |
| MM6 female peasant 2 | 59 | 3 | Packed outline → 2× | [mm6:fmp](../mm6_packed_outline_remaining8/session_07/mm6_fmp/redo_2x/manifest.json) |
| MM6 female peasant 3 | 59 | 3 | Packed outline → 2× | [mm6:mfp](../mm6_packed_outline_remaining8/session_07/mm6_mfp/redo_2x/manifest.json) |
| MM6 female peasant 4 | 59 | 3 | Packed outline → 2× | [mm6:natf](../mm6_packed_outline_remaining8/session_07/mm6_natf/redo_2x/manifest.json) |
| MM6 male peasant 1 | 59 | 3 | Packed outline → 2× | [mm6:pman](../mm6_packed_outline_remaining8/session_06/mm6_pman/redo_2x/manifest.json) |
| MM6 male peasant 2 / town mage | 59 | 3 | Packed outline → 2× | [mm6:pmn2](../mm6_packed_outline_remaining8/session_07/mm6_pmn2/redo_2x/manifest.json) |
| MM6 male peasant 3 | 59 | 3 | Packed outline → 2× | [mm6:mep](../mm6_packed_outline_remaining8/session_08/mm6_mep/redo_2x/manifest.json) |
| MM6 male peasant 4 | 59 | 3 | Packed outline → 2× | [mm6:natm](../mm6_packed_outline_remaining8/session_08/mm6_natm/redo_2x/manifest.json) |
| MM6 Rat | 59 | 3 | Packed outline → 2× | [mm6:rat](../mm6_packed_outline_20261001_batch15/mm6_rat/redo_2x/manifest.json) |
| MM6 Robot | 54 | 3 | Packed outline → 2× | [mm6:rob1](../mm6_packed_outline_remaining8/session_01/mm6_rob1/redo_2x/manifest.json) |
| MM6 Sea Serpent | 59 | 3 | Packed outline → 2× | [mm6:seas](../mm6_packed_outline_remaining8/session_05/mm6_seas/redo_2x/manifest.json) |
| MM6 Skeleton | 59 | 3 | Packed outline → 2× | [mm6:ske](../mm6_packed_outline_20261001_batch15/mm6_ske/redo_2x/manifest.json) |
| MM6 Sorcerer | 59 | 3 | Packed outline → 2× | [mm6:sor1](../mm6_packed_outline_20261001_batch15/mm6_sor1/redo_2x/manifest.json) |
| MM6 Spider | 58 | 3 | Packed outline → 2× | [mm6:spi1](../mm6_packed_outline_20261001_batch15/mm6_spi1/redo_2x/manifest.json) |
| MM6 Thief | 59 | 3 | Packed outline → 2× | [mm6:thf](../mm6_packed_outline_20261001_batch15/mm6_thf/redo_2x/manifest.json) |
| MM6 Titan | 57 | 3 | Packed outline → 2× | [mm6:ttn1](../mm6_packed_outline_remaining8/session_04/mm6_ttn1/redo_2x/manifest.json) |
| MM6 Werewolf | 63 | 3 | Packed outline → 2× | [mm6:wfigt1](../mm6_packed_outline_remaining8/session_04/mm6_wfigt1/redo_2x/manifest.json) |
| MM6 Demon Queen | 24 | 1 | Video ESRGAN x3 → 2× | [mm6:qfi](../mm6_packed_outline_video_x3_20261001/mm6_qfi/redo_2x/manifest.json) |
| MM6 Reactor | 31 | 1 | Native → Video ESRGAN x3 → 2× | [mm6:rea](../mm6_reactor_native_video_x3_20261003/redo_2x/manifest.json) |
| MM6 Cactus | 89 | 1 | Native → Video ESRGAN x3 → 2× | [mm6:mcac](../mm6_cactus_native_video_x3_20261003/redo_2x/manifest.json) |
