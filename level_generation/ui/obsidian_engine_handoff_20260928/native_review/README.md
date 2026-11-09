# Native capture review

Open [index.html](index.html) for the final native screenshot gallery. Images are original engine PNGs, copied without
retouching. `captures.json` lists dimensions, hashes, captions and the source run for each image. `validation.json`
also records the final installed asset hashes and test result; `runs/` preserves launcher receipts and `tours/` the
native input steps. Renderer/GPU/window metadata is included in the validation record.

The gameplay group includes the final 2127 placement: 10% larger portraits moved down, an extra gap above HP/SP,
no portrait name/condition text, and the slightly smaller minimap. The unchanged fullscreen pages were captured
before that gameplay-only spacing adjustment. Fixtures deliberately include crowded buffs and skill lists.

## Reproduce

Build the normal development target from the repository root, then use the already-authorized native launcher:

```sh
cmake --build build --target openyamm -j25
./tools/run_game.sh --isolated obsidian-review --world mm6 \
  --save /home/pjasicek/github/OpenYAMM/level_generation/ui/obsidian_engine_handoff_20260928/native_review/fixtures/mm6-crowded.oysav \
  --warmup 0 --seconds 60 --set video.resolution=1600x900 \
  --set debug.menu_input_tour_path=/home/pjasicek/github/OpenYAMM/level_generation/ui/obsidian_engine_handoff_20260928/native_review/tours/hud.yml
```

Tours contain absolute output directories under `/tmp`; copy a tour and change `output_dir` if a separate result is
needed. `pages.yml`, `journal.yml`, `hud.yml` and `ratio.yml` use the crowded MM6 fixture. `details.yml` and `recovery.yml`
use `mm6-recovering.oysav`. Use `video.resolution=1280x960` for `ratio.yml`; most other input coordinates assume
1600×900. MM8 uses 2100×900. The house, bank, monster and other-world launch positions/maps are in their run receipts.
The launcher creates a separate working directory; these checks do not modify the normal save files.

Both saves are review fixtures, not normal campaign saves: five PCs, boosted skills, numerous awards/quest/autonote
unlocks and all buff types. Members two and four are Knights with no maximum mana. Mistform tints the portraits;
the large skill bonuses change effective HP/SP maximums. The recovering save temporarily removes all ready actions.

The focused suite passed 64 cases and 12,498 assertions; after the final YAML spacing edit, the three Obsidian cases
were rerun and passed all 40 assertions. Android extra controls remain deferred; no Android device, Vulkan build or
release archive validation is represented by these desktop screenshots.
