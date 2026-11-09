# Where a street frame's time goes in Thjorgard City

MM9's Thjorgard City (`thjorgardcity.blv`, review root `output/mm9_rework/assets_dev`,
[project README](../../level_generation/projects/mm9r_thjorgardcity/README.md)) is a native BLV open to the sky. The
user saw about 1 000 FPS in its streets and 2 000–3 000 FPS inside houses. This note measures why, per pose, with the
new indoor portal view, and ranks changes that would close the gap. Proposals 2 and 3 were then done (2026-11-01): see
["Proposal 2: result"](#proposal-2-result) and ["Result of proposal 3"](#result-of-proposal-3).

**Tool.** The debug console's `portals` command ([tools/RUN_GAME.md "Indoor portal view"](../../tools/RUN_GAME.md)):
portal faces in translucent cyan, the drawn sectors outlined per sector with their ids, and a readout and log line of
counts (sectors, traversal nodes, portal tests, batches, faces, triangles, draw calls, per sector) and timings (CPU per
pass, GPU per bgfx view). It works on every BLV and costs one flag test per frame while off.

**Method.** 17 poses from the v03 review tour (`review_tour_v03.yml`) at 12:00: 12 streets, 2 on the hillside (its own
sector) and 3 interiors (tavern, magic shop, forge). The counts are exact and repeat to the face at every pose; they are
the basis of this note (two runs gave identical counts at every pose). The timings are secondary: three visible runs
per mode at 1600 × 900 (RTX 3060 Ti, OpenGL, the user's settings: bloom on, AO and anti-aliasing off), medians of the
1-second samples after each pose had settled, on a machine shared with other agents' games and builds (per-pose FPS
spread about ±20 %, see the ranges; this machine's FPS is about half the user's). The tour is
[city_street_cost/portal_tour.yml](city_street_cost/portal_tour.yml):

```sh
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated city_portals --world mm9 --map thjorgardcity.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 655 0 200 --yaw-radians 1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 150 --visible \
    --set debug.screenshot_tour_path=$PWD/devdocs/mm9_rework/city_street_cost/portal_tour.yml
grep '^\[PortalView\]' /tmp/openyamm-desktop-city_portals-*/game.log
```

## Summary

In one line: with a still camera the extra street time (the user's ~0.5–0.7 ms; about 1 ms on this busier machine) is
draw-call submission (about 80 % of it), then the world faces' GPU time (about 15 %); the open sky is about 1 %.
Walking adds the portal traversal, 0.4–3.3 ms per frame here, more than all of that.

1. **The streets draw 5–35 times the world batches of a room, and each draw call costs about 2 µs of submission.** A
   street frame submits 160–430 world-face batches (one draw call per texture per sector) and 290–680 draw calls in
   all; an interior 12–34 batches and 90–135 draw calls. bgfx's frame GPU span holds the render thread's and the
   driver's submission time on top of the GPU work, and that extra time follows the draw calls: **about 2.25 µs per
   draw call (r = 0.99 over the 17 poses)**. Of the street frame's extra ~1 ms here (GPU span 1.2–2.2 ms against
   0.25–0.64 ms inside), about 0.8 ms is this submission time and 0.1–0.2 ms the world faces' real GPU time.
2. **Faces and triangles are not the cost.** The hillside sector draws 1 802 faces in 13 batches (84 draw calls) and
   runs at 2 400–2 500 FPS, faster than the magic shop (560 faces, 2 000 FPS) and the tavern (896 faces in 34 batches,
   1 400 FPS).
3. **Walking adds the portal traversal, which explodes on the roof-line portals.** A still camera reuses its
   visibility; a moving one rebuilds it every frame. In the streets one build makes 48–256 traversal nodes and
   15 000–150 000 portal link tests (each node of a sector tests all its links: the roof air's 689, the main street's
   640) and takes 0.4–3.3 ms of CPU, against ≤ 10 tests and 3 µs inside. The sector entered most is the roof air, once
   per visible roof-line rectangle (up to 196 nodes). At three of the twelve street poses the traversal hits its
   256-node cap (a fourth reaches 252), after which it stops descending: sectors seen only through later portals could
   be missed.
4. **The roof air is drawn whole.** It is three sectors (60: 3 134 drawn faces and 689 portal links; 34: 664 and 352;
   14: 691 and 327; their 1 368 links are the roof-line portals). Whenever a street sees the sky, the reached ones are
   drawn whole: 1 355–4 489 faces (28–60 % of the street's faces) and 58–126 batches. 14–56 % of those faces lie inside
   the portal frustums they are seen through.
5. **The hill is already out of the roof air.** Since the cut over the north wall, the hillside and palace terrace are
   their own sector (87: 1 802 faces, 3 portals). From six of the twelve street poses it is drawn through the roof air
   and the archway: 13 batches, 3 884 triangles.
6. **The open sky costs nothing measurable:** one full-screen draw, 5–10 µs GPU (26 µs looking up at the roofs),
   4–6 µs CPU. Daylight and fog add no draw or pass (uniforms and a few instructions in the face shader), so their
   share is inside the world view's 150–390 µs; they were not timed separately.

## Counts per pose

Visibility and world faces. *Portal link tests* is each traversal node's sector's links summed (what the loop iterates;
at the 256-node cap the remaining links are still iterated and rejected). *Faces in portal frustums*: submitted faces
whose bounds meet a frustum their sector was seen through. *Textures*: distinct textures among the batches.

| Pose | Sectors | Nodes | Portal link tests | Traversed | World batches | Faces | Triangles | Faces in portal frustums | Textures | Frame draws |
| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| s01_docks_start | 12 | 74 | 23 187 | 73 | 369 | 11 955 | 38 179 | 2 933 | 100 | 537 |
| s02_main_street_north | 12 | 48 | 15 753 | 47 | 339 | 11 524 | 44 853 | 2 562 | 98 | 485 |
| s03_town_hall_plaza | 10 | 256 | 82 039 | 255 | 324 | 9 746 | 33 719 | 3 618 | 93 | 479 |
| s04_southwest_diagonal | 5 | 171 | 115 555 | 170 | 159 | 5 928 | 20 510 | 1 112 | 81 | 293 |
| s05_southeast_diagonal | 5 | 256 | 83 885 | 255 | 160 | 4 086 | 15 157 | 1 797 | 76 | 291 |
| s06_west_gate_start | 10 | 252 | 148 544 | 251 | 346 | 9 969 | 31 644 | 4 309 | 94 | 515 |
| s07_east_west_street | 9 | 106 | 40 362 | 105 | 331 | 9 881 | 31 915 | 3 550 | 93 | 493 |
| s09_market_street | 9 | 120 | 41 368 | 119 | 300 | 10 846 | 37 448 | 2 713 | 98 | 457 |
| s12_forge_street | 16 | 73 | 30 781 | 72 | 431 | 13 359 | 50 300 | 3 745 | 103 | 673 |
| s13_east_side | 7 | 137 | 52 300 | 136 | 260 | 9 144 | 25 693 | 2 979 | 93 | 377 |
| s16_training_hall_square | 9 | 53 | 25 250 | 52 | 284 | 10 115 | 33 067 | 2 560 | 95 | 405 |
| s22_roofs_from_street | 7 | 256 | 89 385 | 255 | 255 | 7 440 | 21 598 | 2 117 | 87 | 378 |
| s19_hill_path | 1 | 1 | 3 | 0 | 13 | 1 802 | 3 884 | 1 083 | 12 | 84 |
| s20_palace_terrace | 1 | 1 | 3 | 0 | 13 | 1 802 | 3 884 | 822 | 12 | 84 |
| i01_tavern | 3 | 3 | 10 | 2 | 34 | 896 | 7 250 | 214 | 16 | 133 |
| i04_magic_shop | 1 | 1 | 5 | 0 | 12 | 560 | 3 983 | 316 | 12 | 102 |
| i09_forge | 1 | 1 | 3 | 0 | 13 | 154 | 1 924 | 75 | 8 | 88 |

The roof air (sectors 60, 34, 14) and the hill (87):

| Pose | Roof air faces (60+34+14) | share | in portal frustums | roof batches | roof link tests | Hill faces (87) | hill in portals | hill batches | tile1024 draws/tris (all) |
| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| s01_docks_start | 4 489 | 38 % | 1 013 | 126 | 21 916 | 1 802 | 318 | 13 | 1 048 / 17 399 |
| s02_main_street_north | 3 798 | 33 % | 1 174 | 91 | 14 514 | 1 802 | 212 | 13 | 1 015 / 26 643 |
| s03_town_hall_plaza | 4 489 | 46 % | 1 312 | 126 | 80 789 | 0 | 0 | 0 | 1 007 / 17 531 |
| s04_southwest_diagonal | 3 134 | 53 % | 444 | 58 | 115 063 | 0 | 0 | 0 | 335 / 6 817 |
| s05_southeast_diagonal | 1 355 | 33 % | 756 | 68 | 83 227 | 0 | 0 | 0 | 419 / 8 334 |
| s06_west_gate_start | 4 489 | 45 % | 1 938 | 126 | 147 341 | 0 | 0 | 0 | 1 294 / 21 991 |
| s07_east_west_street | 4 489 | 45 % | 1 257 | 126 | 38 611 | 0 | 0 | 0 | 974 / 15 958 |
| s09_market_street | 3 798 | 35 % | 1 041 | 91 | 40 577 | 1 802 | 399 | 13 | 933 / 17 360 |
| s12_forge_street | 3 798 | 28 % | 1 219 | 91 | 29 642 | 1 802 | 531 | 13 | 1 145 / 26 168 |
| s13_east_side | 3 798 | 42 % | 951 | 91 | 51 436 | 1 802 | 1 237 | 13 | 1 084 / 12 220 |
| s16_training_hall_square | 3 798 | 38 % | 1 139 | 91 | 24 497 | 1 802 | 366 | 13 | 919 / 16 328 |
| s22_roofs_from_street | 4 489 | 60 % | 846 | 126 | 88 558 | 0 | 0 | 0 | 673 / 9 507 |
| s19_hill_path | 0 | 0 % | 0 | 0 | 0 | 1 802 | 1 083 | 13 | 352 / 2 663 |
| s20_palace_terrace | 0 | 0 % | 0 | 0 | 0 | 1 802 | 822 | 13 | 282 / 2 075 |
| i01_tavern | 0 | 0 % | 0 | 0 | 0 | 0 | 0 | 0 | 60 / 4 492 |
| i04_magic_shop | 0 | 0 % | 0 | 0 | 0 | 0 | 0 | 0 | 26 / 3 725 |
| i09_forge | 0 | 0 % | 0 | 0 | 0 | 0 | 0 | 0 | 18 / 1 831 |

## Timings (secondary, noisy)

Still camera (visibility cached) and walking (`portals rebuild on`: rebuilt every frame), medians of 3 runs; FPS ranges
are the 1-second samples. *GPU frame span* is bgfx's frame timer, first to last GPU command; *world view* is view 0
(world faces, opaque water, blood); decorations and actors are their own views with `portals gpu on`.

| Pose | FPS still (range) | GPU frame span µs | world view µs | open sky µs | decorations + actors µs | main-thread render µs | FPS walking (range) | visibility per frame µs, walking |
| --- | --: | --: | --: | --: | --: | --: | --: | --: |
| s01_docks_start | 580 (497–658) | 1455 | 244 | 9 | 94 | 260 | 444 (331–497) | 563 |
| s02_main_street_north | 557 (464–724) | 1408 | 239 | 5 | 51 | 430 | 524 (470–570) | 423 |
| s03_town_hall_plaza | 571 (482–660) | 1424 | 291 | 10 | 47 | 380 | 480 (421–508) | 571 |
| s04_southwest_diagonal | 437 (384–504) | 1155 | 273 | 10 | 30 | 188 | 208 (184–220) | 2308 |
| s05_southeast_diagonal | 1137 (868–1331) | 778 | 146 | 5 | 22 | 168 | 729 (586–777) | 538 |
| s06_west_gate_start | 290 (236–371) | 1565 | 284 | 6 | 38 | 317 | 148 (128–153) | 3319 |
| s07_east_west_street | 556 (441–692) | 1350 | 244 | 9 | 34 | 325 | 394 (361–430) | 866 |
| s09_market_street | 532 (435–699) | 1480 | 310 | 13 | 44 | 291 | 388 (371–431) | 780 |
| s12_forge_street | 348 (285–548) | 2192 | 390 | 8 | 74 | 486 | 324 (310–360) | 739 |
| s13_east_side | 457 (390–545) | 1194 | 217 | 8 | 30 | 194 | 282 (273–294) | 1222 |
| s16_training_hall_square | 549 (427–647) | 1204 | 250 | 10 | 52 | 344 | 376 (316–416) | 768 |
| s22_roofs_from_street | 504 (473–661) | 1303 | 268 | 26 | 61 | 297 | 426 (337–448) | 589 |
| s19_hill_path | 2529 (2324–2650) | 331 | 181 | 1 | 2 | 95 | 2478 (1993–2597) | 3 |
| s20_palace_terrace | 2371 (1917–2633) | 335 | 174 | 1 | 1 | 126 | 2572 (2099–2622) | 3 |
| i01_tavern | 1418 (1358–1584) | 636 | 170 | 1 | 171 | 191 | 1558 (1351–1584) | 4 |
| i04_magic_shop | 2030 (1450–2118) | 419 | 120 | 1 | 72 | 130 | 2094 (1763–2108) | 3 |
| i09_forge | 3282 (2277–3413) | 248 | 71 | 0 | 30 | 107 | 3210 (2849–3389) | 3 |

The frame span minus the sum of all views' GPU time against draw calls (still camera, 17 poses): **gap = −91 µs +
2.25 µs × draw calls, r = 0.988**. Streets: 530–1 580 µs of gap for 290–670 draws; interiors 100–210 µs for 88–133.

## Proposals, ranked by gain for the effort

Gains are in counts; the time per count is this machine's (2.25 µs per draw call, about 20 ns per portal link test).

1. **Engine: one traversal node per (node, target sector).** When several portals of one node lead to the same sector,
   traverse it once with the union of their clipped apertures (a conservative frustum, so nothing visible is lost),
   and keep each aperture's frustum for culling. Portal link tests fall from 15 000–150 000 to about the drawn
   sectors' links (1 200–2 400) per build, nodes from 48–256 to a few per drawn sector, and the 256-node cap is no
   longer reached. **Walking: 0.4–3.3 ms → under 0.1 ms per frame.** It also shortens the per-sector frustum lists
   that decorations and actors are culled against. Effort: small to medium (`IndoorPortalVisibility.cpp`); MM6–MM8
   traversal changes only where a node had two portals into one sector, which the indoor suite and a sector-mask
   comparison over the MM6–MM8 maps would check.
2. **Engine: fewer world-face draw calls.** Batches are keyed by texture, sector and back sector, so a texture used in
   ten visible sectors is ten draws. Merging the visible batches by texture each frame (one index list per texture,
   rebuilt when the visible set changes) brings the world draws from 160–430 to the distinct textures: 76–103 in the
   streets (12–16 inside). **83–328 fewer draw calls per street frame, 0.2–0.7 ms here: the largest gain with a still
   camera.** Cheaper per-draw state is the other half, not measured here: every face batch uploads 12 light positions
   and 12 colours (all zero for faces, which take their dynamic light from the grid), the clip plane, sky, pulse,
   grid, daylight and fog uniforms, and binds the light-grid textures. Effort: medium; it helps every BLV.
3. **Converter: fewer, larger roof-line portals.** The 1 373 rectangles (1 368 links) come from the diagonal streets'
   16-LT staircase edges. Polygon portals (one per street room footprint, split only where needed for convexity) or
   rectangles allowed to run over roof tops would cut the links to a few hundred or fewer: link tests per roof node
   from 689 to tens, roof nodes from up to 196 to a handful. The same walking gain as 1 without an engine change, and
   fewer portal faces to load; with 1 in place it adds little. Effort: medium (`city/structure.py`, then a rebuild of
   Thjorgard; Sturmford has 244 rectangles).
4. **Converter: split the roof air by street group.** Today any street that sees the sky draws all reached roof air
   (1 355–4 489 faces, 58–126 batches). Pieces over each street group, joined to each other by vertical portals, would
   draw only the pieces a street sees. The lower bound is the roof faces inside the portal frustums: 444–1 938 faces.
   A realistic split (two or three pieces seen per street) about halves the roof's 91–126 batches: **40–60 draw calls,
   0.1 ms per street frame** (less once 2 merges batches by texture). More sectors also mean more nodes: do it after
   1 or 3. Effort: medium to high (the roof room would be cut by plan, like the street cuts).
5. **Engine: cull whole batches against their sector's portal frustums.** The batches' bounds exist. Counted with one
   plan cell per batch: 0–20 % fewer world batches (s09 300 → 250, s13 260 → 218, s16 284 → 239). **About
   30–100 µs.** Effort: small. Finer cells cut triangles but add draws (1 024-unit cells: 900–1 300 draws for
   9 000–26 000 triangles), the wrong way while draw calls are the cost.
6. **The hill: nothing urgent.** It is one sector behind one archway portal (no traversal cost) and adds 13 draws
   (about 30 µs) at the poses that see it. Splitting the palace terrace from the slope would keep some of its 1 802
   faces out of the town's frames, but not draws.
7. **The open sky pass: no change.** 5–10 µs GPU, 1 draw.

## Proposal 2: result

Done 2026-11-01 for every BLV ([INDOOR_FACE_DRAW_GROUPS.md](../INDOOR_FACE_DRAW_GROUPS.md)). The batches stay the unit
of visibility; the visible ones are drawn merged by draw state (texture, lightmap page, liquid colour), with the
sectors and the daylight flag moved into the vertices. Batch order is kept only between batches whose faces cover the
same pixels at one depth (nearly parallel and overlapping), which costs some merging: the streets draw 1.4-1.7 times
their distinct textures, not exactly them.

Thjorgard City at 12:00 after its rebuild with the merged top portals (`output/mm9_rework/portals_1101/thjorgard/after`;
*frame draws before* are the 17 poses' figures above, from before both changes):

| Pose | World batches | Textures | World draws | Frame draws before | after |
| --- | --: | --: | --: | --: | --: |
| s01_docks_start | 369 | 100 | 155 | 537 | 322 |
| s02_main_street_north | 339 | 98 | 140 | 485 | 285 |
| s03_town_hall_plaza | 330 | 93 | 151 | 479 | 305 |
| s04_southwest_diagonal | 159 | 81 | 108 | 293 | 241 |
| s05_southeast_diagonal | 174 | 76 | 112 | 291 | 242 |
| s06_west_gate_start | 346 | 94 | 157 | 515 | 325 |
| s07_east_west_street | 331 | 93 | 151 | 493 | 312 |
| s09_market_street | 300 | 98 | 141 | 457 | 297 |
| s12_forge_street | 431 | 103 | 152 | 673 | 393 |
| s13_east_side | 260 | 93 | 127 | 377 | 243 |
| s16_training_hall_square | 284 | 95 | 132 | 405 | 252 |
| s22_roofs_from_street | 255 | 87 | 135 | 378 | 257 |
| s19_hill_path | 13 | 12 | 13 | 84 | 83 |
| s20_palace_terrace | 13 | 12 | 13 | 84 | 83 |
| i01_tavern | 34 | 16 | 16 | 133 | 114 |
| i04_magic_shop | 12 | 12 | 12 | 102 | 101 |
| i09_forge | 13 | 8 | 9 | 88 | 83 |

**Street world draws 108-157 instead of 159-431 (51-279 fewer draw calls per street frame; about 0.1-0.6 ms at the
2.25 µs per draw measured above).** Frame draw calls fall from 290-670 to 240-390. In MM6-MM8 the world draws equal
the distinct textures (6d02 s47: 41 batches, 25 draws; d06: 14-35 batches, 13-30 draws). FPS was not measured again:
the machine was shared, and the frame-rate check stays a single-session run on the user's side.

**Pictures.** Each pose was shot three times in one run with the world paused: merged, one draw per batch in batch
order (the old submission, through a temporary switch), merged again; a pixel counts when the two merged shots agree
and the per-batch one differs from both (8 maps: MM6 6d02, MM7 7d06, MM8 d06 and d12, Anskram Keep, Lich Lab,
Thjorgard City at 12:00 and 23:30; 62 poses). All of 7d06 and 30 of the 62 poses are identical. The rest differ
only in single pixels along lines where two faces meet: a face edge on another face's interior, faces sharing an edge (a pixel
covered by both at one depth goes to whichever draws later). Most poses: 0-75 pixels; the most, Thjorgard s12, a
one-pixel line along an eave (466 pixels) that the merged draw shows slightly darker, and Lich Lab u16, a one-pixel
seam line the old order drew and the merged one does not. No face is missing or covered.

**Checks.** `openyamm_unit_tests` 2 453/2 453 (new: which faces touch, the order of touching batches, keys without
the daylight); `openyamm_runtime_tests` 54/55 (the known New Sorpigal braziers case); `indoor` suite 174/174.

## Result of proposal 3

Done 2026-11-01: `merged_top_portals: true` in six cities' `overrides.yml` (`city/structure.py` "Merged top portals",
[CITY_PLAYBOOK.md](../../level_generation/projects/mm9r_common/CITY_PLAYBOOK.md) "The open air"); Frosgard has no
roof line, so the setting changes nothing there and it was not rebuilt. Each street room's roof-line rectangles are
merged into few convex polygons that may run on over walls, roofs and drawn eaves, never over another room's air, a
strip covered by a sky face or another top portal. All six cities were rebuilt with the final converter, 2026-11-01
evening (the first rebuilds that afternoon predated the sky-face rule; Arslegard's then had 405 top portals, more
than its plain cover).

Before: the 2026-10-31 builds (plain rectangles, `output/mm9_rework/portals_1101/root_before`); after: the evening
rebuilds. Each city's latest review tour at 12:00, every shot (streets and interiors), counts from the `[PortalView]`
lines (`city_street_cost/portal_counts.py`; `output/mm9_rework/portals_1101/<city>/before_oldtex` and `after`).

| City | Top portals | Portal faces | Faces | Vertices | Max nodes | Max portal link tests | 256-node cap hits | Street world draws (batches) |
| --- | --: | --: | --: | --: | --: | --: | --: | --: |
| Thjorgard | 139 | 1 470 → 237 | 27 911 → 26 678 | 37 979 → 34 479 | 256 → 60 | 148 544 → 3 066 | 3 → 0 | 13-157 (13-440) |
| Thronheim | 215 | 974 → 299 | 19 561 → 18 886 | 31 192 → 29 553 | 141 → 39 | 55 721 → 3 378 | 0 | 61-139 (91-273) |
| Drangheim | 141 | 744 → 206 | 11 258 → 10 720 | 16 202 → 14 840 | 256 → 87 | 96 913 → 9 195 | 1 → 0 | 88-142 (96-221) |
| Guberland | 180 | 631 → 271 | 15 326 → 14 966 | 19 823 → 19 019 | 101 → 45 | 11 721 → 1 734 | 0 | 20-63 (21-157) |
| Sturmford | 116 | 343 → 215 | 12 928 → 12 800 | 21 154 → 20 965 | 66 → 38 | 4 099 → 1 133 | 0 | 22-85 (28-255) |
| Arslegard | 158 | 224 → 213 | 11 830 → 11 792 | 16 017 → 16 261 | 76 → 69 | 9 872 → 8 001 | 0 | 49-132 (55-306) |

*Street world draws* are after both changes (proposal 2 merges the batches; the batches are the old draws).

- **Walking (the visibility rebuilt every frame):** the link tests per build fall 5-50 times where the staircase
  rectangles were (Thjorgard, Thronheim, Drangheim, Guberland), by this note's 20 ns per test from up to 3.0 ms to
  0.06 ms in Thjorgard. The cap is no longer hit anywhere.
- **Only the portal faces change** in five cities (the faces fall by exactly the portal faces removed). Arslegard is
  the exception: 27 non-portal faces fewer and 244 vertices more, not traced further; its scenarios and pictures show
  nothing else than the library below. Arslegard gains little otherwise: its plain cover was already small.
- **Pictures:** before and after shots compared per pose in 16 × 16 blocks (texture detail washes out; the x4 surface
  textures changed between the runs, so finer comparisons only show those): no hole in any city. The differences
  are the new textures, and three changes of the sectors drawn:
  - poses that hit the cap now draw sectors the cap had cut (Thjorgard s03 and s05, Drangheim s19);
  - Arslegard's library (i05) and Njam lane (s19) no longer reach the air over the roofs. The plain cover put roof-line
    rectangles over the library's high hall, so its sector counted as open to the sky: it took the daylight and drew the
    roof room behind its ceiling. Now it is an interior lit by its own lights, darker than before (mean brightness
    135 → 105 at i05). Its ceiling is solid, so this is a fix.
- **Scenarios after the rebuild:** every city's pass (Thjorgard 3, Guberland 3, Thronheim 4, Drangheim 5, Sturmford 4,
  Arslegard 4). The shared converter's other maps are unchanged: Lich Lab `--plan --scratch` is byte-identical.

## Checks of the debug view

- Builds `openyamm`, `openyamm_unit_tests` (2 444/2 444, with a new check that the pass views 220–223 sit between the
  world views 0 and 1), `openyamm_runtime_tests` 54/55 (the known New Sorpigal braziers case), `indoor` suite 174/174.
- MM8 `d12.blv`: a shot before the view was ever on and shots after `portals on` then `portals off` are pixel-identical;
  with the view on it draws and counts as in Thjorgard (1 sector, 13 batches).
- While off, the renderer tests the settings once per frame and records five traversal counters per visibility build;
  every other part runs only while on. The pass views 220–223 are in the view order but receive no draws while
  `portals gpu` is off.

## Screenshots

[city_street_cost/portal_view_sheet.jpg](city_street_cost/portal_view_sheet.jpg): per pose, left every portal face
(cyan; traversed brighter) with the drawn sectors outlined and labelled, right only the traversed portals with their
edges; the readout top left. The streets show the rows of roof-line rectangles each entered as a separate node (the
repeated `60`, `34` and `14` labels along the roof line); the interiors show one or three sectors.
