# Flying demon review and reproduction

Accepted 54/54 native source names, 50 unique restored tiles. Five identical shared m496Xa corpse images reuse one restored ash pile. All native fly/standing/walk/fidget, attack/attack2, hit, seven-frame disintegration, corpse, stored views, mirrors, timing, scale and logical anchoring are preserved. Source palette 496 is fixed for the shared corpse, independent of actor palette.

Reviewed every native and generated sheet, ordered base/mask contacts, all standing variants, light/dark magnified contours and the offline viewer at mirrored walk view 6 / palette 685 / frame 4 and death view 0 / palette 683 / frame 4. Corrected demonstrated green claw-tip contamination and the gray effect core in recolored death frames; final captures show the corrected contours and yellow-white burst center. Native dark wings and wiry body remain recognizable; enhanced carved folds/scales and clearer angular magical wisps are interpretations, not identical microtexture. Variant claws remain somewhat dimmer than native highlights.

Purple-safe local matte projection preserves intentional purple body and blue-violet effect details. The generic magenta audit flags these legitimate colors (20,945 cleaned and 38,021 exported/atlas candidates); visual edge contacts show internal body/effect detail rather than a surrounding matte halo. Alpha, crop, atlas extraction, provenance/source/palette hashes and sequence checks pass. Four enhanced-art coverage channels distinguish skin, wing/neutral dark structure, pale hard features and eyes/effect. Expanded death coverage includes the bright neutral effect core; ash masks are zero. Fixed native-used sigma=4 luminance LUTs are declared explicitly in manifest.json. A 0.78 body gain, preserved effect brightness, 0.42 ash gain and reduced warm ivory cast retain tonal weight.

Reproduce from the repository root:
```
python3 level_generation/creatures/mm6_wdm/process.py
python3 level_generation/creatures/mm6_wdm/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py wdm
```
Rebuild resets visual acceptance. Staged only; no gameplay installation. Viewer/contact checks do not establish GPU performance.

## User review 2026-09-24: full consistency regeneration

All actions and stored views require regeneration. Keep native skin color and fine mottling consistent; remove invented coarse scale plates. wdmflyf0 is an extreme example compared with wdmflye0 and its native counterpart. Variant A eyes must retain the original small blue appearance and native gaze rather than large turquoise irises or wandering pupils. Stage under consistency_repair_20260924; previous artwork and viewer edits remain preserved.

Full consistency regeneration completed in `consistency_repair_20260924/redo_2x/`: 50 new unique images, all 54 native names, all actions/stored views, 3 native palettes, 2x exports, measured minimum sampling 2.290x. Reviewed static native-size contacts, independent anatomical features, exact atlas placement, 100% faces/skin, every-pose variants and residual edges. Small blue eyes and fine plum skin are consistent across the selected living poses; back-facing eye inventions and missing early death flames were repaired. Ash retains fixed palette 496 via zero masks. See that package’s `review/decision.json` for artistic/measurement limitations and `review/acceptance.json` for bound artifact hashes. Built-in imagegen prompts and selected raw attempts are retained in the run ledger. Original accepted files and app fixups remain unchanged.

2026-09-24 targeted user follow-up: first flight frames wdmflya0/a1/a2 use conservative equal-channel brightness gains 1.12/1.10/1.08 against same-view neighbors. wdmatkd0 upper-mouth duplicate teeth repaired using only an 888-pixel RGB region from built-in imagegen; all other master pixels and alpha retained. All four geometry/placement/sampling measurements unchanged. Other 50 native names are byte-identical (cleaned/aligned/masks). Rebuilt all three palettes, reviewed affected native-size sequences, masks and edges; new acceptance hashes frozen in consistency_repair_20260924/redo_2x/review/acceptance.json. Prior state retained in checkpoints/before_walk_tone_teeth. Review app 8767 refreshed; saved guides/placement proposals carried because geometry is exact.

2026-09-24 consolidation: copied the validated consistency_repair_20260924/redo_2x package byte-for-byte into the canonical mm6_wdm/redo_2x used by the main review queue on 8765. Generation/edit provenance remains in the retained consistency_repair_20260924 project; use that project for subsequent source rebuilds, then explicitly promote reviewed outputs. Previous main package and viewer checkpoint snapshot are in archived_redo_2x_before_consistency_20260924. New-art review settings were copied by matching artifact digest. Old-art offsets remain in their historical checkpoint only. Dragon package and review settings were not changed.
