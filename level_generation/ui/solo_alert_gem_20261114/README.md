# Solo alert gem, 14 November 2026

The solo HUD's aggro indicator on the minimap's upper-left rim ([HUD.md](../../../devdocs/solo_action/HUD.md), "Alert
gem"): MM9's compass gem (`mm9/extracted/ART/ART/HUD/MAPGEM{BLUE,GREEN,YELLOW,RED}.pcx`, 35 px) remade in high
definition in the Obsidian HUD's brass.

- `refs.png`: MM9's four gems enlarged, our minimap rim, the portraits' aggro diamonds and the clock plate.
- `CODEX_BRIEF.md`: one green gem, two candidates (`raw/`, `raw/runs.json`); Codex chose candidate 2, the smoother
  domed glass (`masters/gem_green.png`, 256 px).
- `make_states.py`: the other states from that master by turning only the stone's hue band (the bezel, collar and
  highlight stay identical): yellow (amber), red, blue (turn-based combat) and unlit (smoky, for a member who cannot
  act). It writes `masters/gem_<state>.png`, the runtime sources
  `assets_source/engine/icons_x2/obsidian_solo_alert_<state>.png` (128 px) and `checks/states.png`; then
  `tools/cook_ui_textures.py` cooks them.
