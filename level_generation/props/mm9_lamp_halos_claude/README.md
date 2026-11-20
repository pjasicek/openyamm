# MM9 lamp halos (2026-11-04)

A soft warm halo round the flame of MM9's street lamps and lanterns: `lamppost1`-`lamppost4` (Arslegard, Thjorgard,
Thronheim and Sturmford City's street lamps), `lantern2` (Thjorgard's) and `lanternwall1` (Sturmford's wall lanterns).

- **Why.** The user (Thjorgard City at night): only a flame flipbook in the lantern, no light, no glow. MM9 draws a
  CandleProp's flame as a large additive sprite (`sprites/Fire/TorchFlame*.spr`, `torchflame_additive*.dtx`) that
  glows round the lantern by day and night (the user's MM9 screenshot), with the CandleProp's own dynamic light under
  it. The light: the converter's lamp lights (devdocs/INDOOR_OPEN_SKY.md "Static lights"). The glow: this halo.
- **What.** `add_halos.py`: one more primitive per LOD mesh, a camera-facing square card centred on the model's flame
  cards (`Fire`), 1.6 flame-card heights in radius, kept inside the model's height (the engine scales a decoration by
  its height). The material is the MM8 lantern's `Halo` as it is (blended, unlit, additive, `openyamm_billboard`,
  flickering warm emission `openyamm_flicker [0.35, 8]`, the soft radial `halo` texture, warm COLOR_0;
  `level_generation/decorations/mm8_3d/animated/`). Additive cards also draw into the bloom view.
- **Cost.** One quad per lamp, instanced with the lamp; with bloom one more draw into the glow view.
- **Route.** `python3 add_halos.py --install` reads the source GLBs in `assets_source/engine/models/`, writes
  `work/<model>.glb`, checks the winding and installs with `tools/install_model.py --engine`. A model that already has
  a `Halo` material is skipped. `mm9_skins_x4/skins.py install` starts from the same source GLBs, so it keeps them.
