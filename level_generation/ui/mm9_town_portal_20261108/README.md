# MM9 Town Portal screen (2026-11-08)

The Town Portal screen on MM9's maps (`town_portal_switch.txt` group `TPChedian`) redrawn: the user found the old one
blurry (MM9's 800x600 `TOWNPORTALBG.pcx` scaled up) and its lower right still held MM9's parchment note and check
button under our Close button. Codex repainted MM9's own picture (Claude driving, `gen.py`); `compose.py` builds the
installed art from it.

## What is installed

- `assets_dev/worlds/mm9/icons_x2/tpchedian.png` (1280x960, the x2 of the 640x480 screen): `final/tpchedian.png`.
- `assets_dev/worlds/mm9/icons_x2/tp{thjorgard,sturmford,drangheim,guberland,frosgard,thronheim}.png`: the hover
  pictures, `final/tp<city>.png`.
- `assets_dev/engine/data_tables/town_portal_switch.txt`: the six TPChedian rows' Icon X/Y/Width/Height
  (`final/rows.txt`, 640x480 units; the hit area is the same box).
- Also copied into the review root `output/mm9_rework/assets_dev`. The old files are in `backup/`.

## How it is made

1. `prompts/townportal_bg.txt` with `refs/townportalbg_mm9_wide.png` (MM9's picture widened to 3:2 with its own table)
   and `refs/townportalbg_mm9.png`: a faithful sharp remaster with the lower-right note and button removed. Two runs;
   `raw/townportal_bg_v2.png` was chosen (v1 is a little softer).
2. `prompts/table_wood.txt`: an empty table of the same planks, `raw/table_wood_v2.png` (v1 failed: its reference was
   not in `refs/`).
3. `python3 compose.py raw/townportal_bg_v2.png raw/table_wood_v2.png`: the framed map from the repaint laid on the
   empty table at 96 % so that it ends at y 880 of 960, above the continent buttons and the Close button
   (`engine/ui/gameplay/town_portal.yml`, from y 447 of 480); the destination label is printed over the frame's lower
   margin, as on the other continents' maps. (Enlarged on 2026-11-09 at the user's request: the first layout, at 86 % and
   ending at y 796 above the label, left a wide band of empty table.) The repaint keeps MM9's map at one uniform
   scale (its inner red border, 71..624 x 78..514 of the original, is 204..1151 x 132..878 in the repaint), so MM9's
   city buttons (`TOWNPORTAL-COORDS.txt`) give each box's size; each box is centred on its repainted city
   (`CENTRES`, measured on `review/city_centres.png`) with 6 units of room for the outline.
4. Hover pictures: the background under the box, a little brighter, with MM9's own highlight outline
   (`<CITY>-HIGHLIGHTA.pcx` against `-NORMAL.pcx`) filled, scaled to the repaint, smoothed and drawn as a crisp orange
   stroke with a soft golden glow, 4 pixels clear of the miniature. MM9's name plates (`-HIGHLIGHTB.pcx`) are not used:
   the engine prints the destination below the map.

Review: `review/boxes.png` (boxes, label and Close areas), `review/hover_new.png` (the six hover pictures),
`review/mock_hover_sturmford.png` (the screen as the renderer composes it: background, the hovered city at its box,
label and Close; a mock, not an in-game capture: no debug command opens the screen).

Cities on the map (MM9's buttons): Frosgard the ice city in the north, Thronheim at the river mouth, Thjorgard the
green-roofed city on the south coast, Sturmford and Drangheim on the eastern island (north and south), Guberland on
the small southern island. The town in the west is Arslegard (no portal).
