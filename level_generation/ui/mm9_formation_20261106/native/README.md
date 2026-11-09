# MM9 formation builder: native captures (2026-11-06)

Engine-native screenshots of the [accepted design](../README.md), as built in phase 10 of
`devdocs/mm9/MM9_HIRELINGS_PLAN.md`. Five-member party (`obsidian_curved_portraits_20260929/native/fixtures/
five.oysav`) in Sturmford City (`assets_dev`), with Forad Darre, Edina A'Mor and Hrolf Spearmaster added by the debug
console's `hireling add`. The builder is opened by a click on the button under the minimap.

| Image | Content |
| --- | --- |
| `hud_16x9.png` | the plain HUD: the formation button in the followers' place, above the hireling rail |
| `formation_16x9.png`, `formation_4x3.png` | the default formation (members 1-3 front, 4-5 and Forad middle, Edina and Hrolf rear), the pointer on Forad: his name |
| `formation_16x9_drag.png`, `formation_4x3_drag.png` | Hrolf dragged from the rear centre to the empty rear right: his cell dashed, the target gold |
| `formation_16x9_dropped.png` | after the drop |
| `formation_16x9_refused.png` | member 2 moved from the front centre to the rear centre: Accept refused, the refusal in the instruction line |
| `formation_16x9_reopened.png` | after Cancel, the Party Formation key reopens the old formation |

Compared with the study: the geometry and texts are the study's (`mm9_formation.yml`, checked by
`tests/Mm9FormationTests.cpp`); the faces are the installed x2 portraits (members) and `9npcNN` families (hirelings),
drawn through the party's portrait animation, so the drawing differs from the study's stills. The brass ring round each
face is the party's rim stroke. The screenshots have no cursor (the engine capture leaves out the system pointer).

Reproduce (tours in `tours/`; their `output_dir` is this folder):

```sh
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated form169 --world mm9 --map sturmfordcity.blv \
  --save level_generation/ui/obsidian_curved_portraits_20260929/native/fixtures/five.oysav \
  --warmup 0 --seconds 50 --set video.window_mode=windowed --set video.resolution=1920x1080 \
  --set controls.control_scheme=classic \
  --set debug.menu_input_tour_path=$PWD/level_generation/ui/mm9_formation_20261106/native/tours/formation_16x9.yml
```

For 4:3 use `--set video.resolution=1440x1080` and `tours/formation_4x3.yml`.
