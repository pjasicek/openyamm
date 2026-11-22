# Xeen Town Portal pages, new-game card and loading pages (2026-11-20)

Art for the Xeen world (lane A4, towns): the two Town Portal pages (one per face of the flat world), the twelve towns'
hover pictures and boxes, the new-game continent card, and four loading pages. Codex painted every image (one
`codex exec` per image through `gen.py`, the worker of `mm9_town_portal_20261108`); the scripts here compose them.
Seven Codex calls in all, no regeneration was needed.

## What is installed

All in the git-ignored world folder:

- `assets_dev/worlds/xeen/icons_x2/tpcloudside.png`, `tpdarkside.png`: the pages, 1280x960 RGB (`final/`).
- `assets_dev/worlds/xeen/icons_x2/tp<town>.png`: the twelve hover pictures (`tpvertigo`, `tprivercity`,
  `tpcastleburlock`, `tpwinterkill`, `tpnightshadow`, `tpnewcastle`; `tpcastleview`, `tpcastlekalindra`,
  `tpsandcaster`, `tplakeside`, `tpnecropolis`, `tpolympus`).
- `assets_dev/worlds/xeen/ui/hud_x2/menus/omenu_continent_xeen.png`: the new-game card, 444x444 RGB like
  `omenu_continent_chedian.png`.
- `assets_dev/worlds/xeen/icons_x2/xeenloadc1.png`, `xeenloadc2.png` (Cloudside), `xeenloadd1.png`, `xeenloadd2.png`
  (Darkside): loading pages, 1280x960 RGBA with full alpha, like `7load1.png`.

Nothing outside the world folder was changed: the boxes still have to be copied into
`assets_dev/worlds/xeen/source/towns/town_portal.yml` (`icon`) by the lane, and the card and loading pages still have
to be named in the world's tables (`continent_selection.yml` card group, the world's loading-page list).

## Boxes

`final/boxes.yml`, 640x480 units (x, y, w, h; the hit area is the same box), in `town_portal.yml`'s order:

| Cloudside | name | x | y | w | h | Darkside | name | x | y | w | h |
| --- | --- | --: | --: | --: | --: | --- | --- | --: | --: | --: | --: |
| Vertigo | tpvertigo | 400 | 281 | 83 | 50 | Castleview | tpcastleview | 77 | 248 | 98 | 55 |
| Rivercity | tprivercity | 310 | 232 | 108 | 48 | Castle Kalindra | tpcastlekalindra | 85 | 307 | 45 | 44 |
| Castle Burlock | tpcastleburlock | 220 | 113 | 84 | 61 | Sandcaster | tpsandcaster | 375 | 217 | 89 | 58 |
| Winterkill | tpwinterkill | 100 | 283 | 72 | 60 | Lakeside | tplakeside | 382 | 163 | 64 | 40 |
| Nightshadow | tpnightshadow | 205 | 327 | 80 | 51 | Necropolis | tpnecropolis | 121 | 136 | 84 | 59 |
| Newcastle | tpnewcastle | 222 | 276 | 82 | 49 | Olympus | tpolympus | 327 | 53 | 91 | 43 |

No two boxes of a page overlap (`compose.py boxes` refuses to write the file if they do), and none reaches the
destination label (`town_portal.yml`: 340..580 x 402..430) or the buttons below y 447.

## How it is made

1. `make_refs.py` writes the references into `refs/` (deleted after the run to save disk; rerun it before `gen.py`):
   `layout_<face>.png`, MM9's page (`tpchedian.png`: frame, mat, borders, the right-hand tile strip) on MM9's empty
   table at the image size 1536x1024, with its map replaced by the face's world board painting
   (`level_generation/xeen_art/mu1_world/raw/<face>_v2.png`, the MU-1 boards: the 3x2 region grid of WORLD_DESIGN §3.1
   with the rim and the starfield); the continent cards; MM7's `7load1.png` as the loading pages' style.
2. `python3 gen.py tp_cloudside 1 layout_cloudside.png`, `gen.py tp_darkside 1 layout_darkside.png`
   (`prompts/tp_<face>.txt`): the framed map repainted with the board's land, the boards' floating cloud islands
   removed, the six destination towns as separate, prominent miniatures, Olympus on a cloud bank in Darkside's amber
   sky band above the north rim. Codex kept the frame exactly where the layout put it (outer edge 154..1241 x
   40..912), so the page is the painting at 1:1.
3. `python3 compose.py cloudside raw/tp_cloudside_v1.png` (and `darkside`): the frame laid on MM9's table
   (`mm9_town_portal_20261108/raw/table_wood_v2.png`) at (26, 8), 872 high, ending at y 880 of 960 like Chedian's.
   The towns' miniature extents (`FACES`, page pixels) were measured on gridded crops of the composed page. A hover
   picture is the page under the box, 8 % brighter, with a crisp 3-pixel orange ellipse a little outside the
   miniature and a soft golden glow outside it that fades before the box's edge. `python3 compose.py boxes` writes
   `final/boxes.yml`.
4. Card: `gen.py card_xeen 1 card_chedian.png card_jadame.png board_cloudside.png` (`prompts/card_xeen.txt`), the
   1254x1254 return downsampled to 444x444 with Lanczos. The flat slab of Cloudside seen from the south at an angle,
   rim cliffs and waterfalls dropping into the stars, inside the same gold frame and glass, labelled "Xeen" in the
   same white serif as the other cards' names.
5. Loading pages: `gen.py load_<c1|c2|d1|d2> 1 style_7load1.png` (`prompts/load_*.txt`, 1448x1086 returns), then
   `python3 build_loading.py xeenloadc1=raw/load_c1_v1.png ...`, which follows
   `level_generation/ui/hesper_loading/build_pages.py`: resized to 1280x960, `loading2.png`'s native bar frame
   (322..962 x 896..960, outer 8 pixels feathered) laid over the bottom, so the engine's `loadprog` fill at
   (346, 918), 598x28, sits in it. Subjects: c1 Vertigo's square with the money tree, slimes and Joe the
   Exterminator missing them; c2 the world rim, a meadow ending in a white cliff above the stars with a party and a
   cow at the brink; d1 Castleview under siege by an amber failing sun, gremlins sabotaging the catapult and the
   bridge; d2 the Necropolis gate with skeleton sentries and a crashed glowing pod on the lava field.

## Review

- `review/pages_beside_chedian.jpg`: both pages beside MM9's Chedian page.
- `review/boxes_<face>.jpg`: each page with all six hover pictures in place, the boxes (magenta), the label and the
  Close button areas (cyan).
- `review/mock_hover_rivercity.jpg`, `mock_hover_olympus.jpg`: one hovered town as the renderer composes it (a mock,
  the label is a stand-in).
- `review/hover_all.jpg`: the twelve hover pictures.
- `review/cards.jpg`: the Xeen card beside Enroth, Antagarich, Jadame and Chedian.
- `review/xeenload*_50.jpg`: the loading pages with the bar at 50 %.

## What is weak

- The hover outline is an ellipse round the measured extent, not the miniature's own silhouette (MM9 had its original
  highlight shapes): tall spires (Burlock's flags, Vertigo's tower, Kalindra's top spire) cross the outline a little.
- Nightshadow and Newcastle, and Castleview and Castle Kalindra, sit close together; their boxes touch but do not
  overlap. Castle Kalindra's box is the smallest (45x44).
- Olympus' dome touches the map's inner border at the top; its box reaches onto the frame's inner border.
- The card's glass dome is a little less glossy than the four older cards, and the land shows the MU-1 board's two
  floating cloud islands (fine on the card: they are Xeen's sky layer).
- `xeenloadd1` v1 had a large red dragon on a rock that the prompt did not ask for. Replaced on 2026-11-20 (A4,
  second session): `raw/load_d1_v2.png` from `prompts/load_d1.txt` (v1's prompt kept as `prompts/load_d1_v1.txt`, plus
  one sentence: only the gremlins, no dragons or large creatures), built with `build_loading.py` and installed; the
  gremlins sabotage the catapult and the bridge under Castleview's walls. `refs/style_7load1.png` was rebuilt from
  `7load1.png` (the refs folder was gone).
- The page's map is lavish but busier than MM9's; the six destinations are the largest miniatures, so they still read.
