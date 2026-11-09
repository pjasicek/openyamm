# Flame flipbooks for the dungeon (and outdoor) fire decorations

`flame02_basecolor.png` and `flame03_basecolor.png` are made by `../scripts/make_flames.py` from the CC0 Unity Labs
flipbooks in `../source/unity_labs_vfx/` (licence there). Both are 16 x 4 frames, a seamless 64-frame loop, recoloured
to the MM torch flame's brightness ramp, with the smoke faded out and the flame body's alpha strengthened.
- flame02: 2048 x 1024 (128 x 256 frames). Torches, braziers, flambeaux, campfires, cauldron fires.
- flame03: 1024 x 512 (64 x 128 frames). Candles, small sconce flames.

Material: Flame, BLEND, double-sided, unlit (finish table `FLAME`), extras `openyamm_billboard: true`,
`openyamm_flipbook: [16, 4, 30]` (30 fps: a 2.1 s loop), `openyamm_specular: 0.0`.

Card recipe (as in `../scripts/build_torch.py`): show the lower 80 % of each frame. The card's top vertices take
Blender texture v = 0.8 and its bottom v = 0; the glTF export flips v, so the top 20 % of the frame, empty above the
flame tips, is cut. In each frame the flame:
- spans about 0.2 to 0.9 of the frame width, so it is about 60 % of the card width;
- has its flat base at 0.98 of the frame height (about 2.5 % above the card's bottom edge);
- has its tips at 0.22 to 0.36 of the frame height (about 5 to 20 % below the card's top edge).

So for a native flame W units wide and H units tall, rising from a fixture top at Z, the card is about W / 0.6 wide
and H / 0.85 tall, with its bottom at about Z - 0.025 x card height, centred on the flame axis (x = y = 0).
