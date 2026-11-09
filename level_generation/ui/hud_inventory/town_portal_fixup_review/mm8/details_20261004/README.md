# MM8 marked-detail corrections — 2026-10-04

[Corrected map](townport.png) · [detail comparison](detail_comparison.png) · [game size](game_size.png)

The original Town Portal artwork and the colored Jadame map in `test_img/2063.png` supply the motif references.
Native MM8 creature frames supply supporting anatomy. The marked details are the Murmurwoods unicorn,
Garrote Gorge red dragon, Balthazar's Lair minotaur with a double-bladed axe, pale aquatic spirit,
Ironsand Desert cyclops and Blood Drop temple. The sea figure is interpreted as a flowing watery humanoid
from its original silhouette; the source image does not name it.

Built-in imagegen performed the redraw: [exact prompt](prompt.txt), [tool arguments](tool_args.json),
and [untouched generated master](raw.png). The master is 1448 × 1086. The export is opaque RGB at
1280 × 960, retaining the original 640 × 480 logical canvas.

Only the six recorded local regions are composited into the retained map. Every pixel outside them is unchanged.
The [manifest](manifest.json) records hashes, repair bounds and masks. Six matching destination crops and hover
images are under [buttons](buttons/); native hit rectangles, dimensions and four-pixel seam borders are preserved.

Inspected the full master, extracted details and game-size export. The horn, dragon wings/tail, minotaur head/axe,
cyclops body/central eye, watery torso/tail and temple wall/roof perspective are coherent at miniature map scale.
Static locality and button checks pass. The user approved deployment in the follow-up. Both backgrounds and all twelve destination highlights are
accepted and installed in `assets_dev/engine/icons_x2/`; [acceptance.json](acceptance.json) records this revision.
