# Dimension Door with five doors (Xeen, 2026-11-20)

Lane A4 (`devdocs/xeen/lanes/A4.md`). The four-portal screen of
[the MM9 world menu study](../mm9_world_menu_study_20261106/README.md) (`tpglobal4`) redrawn with five portals for
Jadame, Enroth, Antagarich, Chedian and Xeen, in the same grey-sepia painted style.

- `raw/door_base5_v1.png`: the five-portal base (Codex, `prompts/door_base5.txt`, references
  `refs/door_layout5.png` (the layout guide) and `refs/door_style4.png` (today's `tpglobal4`)).
- `raw/xeen_vista_v1.png`: the view through Xeen's door (Codex, `prompts/xeen_vista.txt`, the three original portal
  views as style references): Vertigo's meadows, a river falling off the world's edge into the stars, cloud islands.
- `door_compose5.py` builds `final/`: `tpglobal5.png` (1280x960, all portals misty), `tp<door>5.png` (each portal lit
  with its view, x2 art drawn at its native rect), `all_lit5.png`, `places.json`, and `review/door5_hover_zones.png`.
  Jadame, Enroth and Antagarich reuse the original views, Chedian the four-portal study's vista.
  `--install` copies the backdrop and the five lit doors into `assets_dev/worlds/xeen/ui/gameplay/dimensional_travel/`.

The five-door screen for `dimension_doors.yml` (native 640x480 rects; A1 adds it with Xeen's door):

```yaml
screens:
  - backdrop: ui/gameplay/dimensional_travel/tpglobal5
    places:
      - {picture: [17, 100, 107, 136], hover: [0, 0, 128, 480]}
      - {picture: [146, 99, 107, 136], hover: [128, 0, 128, 480]}
      - {picture: [266, 99, 107, 136], hover: [256, 0, 128, 480]}
      - {picture: [386, 99, 107, 136], hover: [384, 0, 128, 480]}
      - {picture: [516, 99, 107, 136], hover: [512, 0, 128, 480]}
doors:   # each door's picture on the five-door screen
  jadame: ui/gameplay/dimensional_travel/tpjadame5
  enroth: ui/gameplay/dimensional_travel/tpenroth5
  antagarich: ui/gameplay/dimensional_travel/tpantagarich5
  chedian: ui/gameplay/dimensional_travel/tpchedian5
  xeen: ui/gameplay/dimensional_travel/tpxeen5      # place 5
```
