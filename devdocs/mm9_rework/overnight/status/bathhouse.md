# bathhouse — overnight status

- Phase: DONE after the orchestrator's fix round (2026-10-30 22:35)
- Locks held: none. Background processes: none.

## Fix round (orchestrator review of pages_v02 / lighting_v02)
1. Water: the non-solid surfaces (hall pool, tub) and the drained room's surface now opacity 1 x Water115's own alpha
   (mean 0.42, 52-255, DTX PREFER4444) for MM9's SurfaceAlpha 0.5: blue, rippled, reads as water (literal 0.5 x 0.42 =
   0.21 read as the tinted bed).
2. Switch shelf: the blue wall in the capture is the old import drawing BlueWater2's box side; MM9's 13 water volumes are
   `Visible 0` (only ShowSurface tops drawn). Native shows the propeller housing, as MM9. Explained in README Water.
3. Stair-foot blow-out: pale plaster under a light pile-up at max_lighting 1.5; gone with the lightmap-matched bake
   (max_lighting 1, levels at MM9's lightmaps). Also MM9's BrightScale now applied to BLV light colours (23 lights).
4. East corridor cast: Light108 (yellow) trimmed x0.45 (hue was 76 deg off MM9's teal there); corridor hue matches.
5. Calibration now against MM9's DAT lightmaps (new brief rule): zone luminance ours/MM9 0.90-1.31 (8 of 10 zones within
   0.9-1.16), hue matches in 7 of 8 coloured zones (median suggested x1.10, not applied).

## Final summary
- Faces 2462, rooms 25 (+sector 0), portal faces 22, movers 20, lights 73 BLV (+5 capped, +20 DirLights bake-only),
  decorations 63, chests 4, actors 20 (16 + 4 hidden spores), pads 10, 1 ladder.
- Scenarios doors_exits / chests / scripted: PASS on the final convert.py.
- Bake: 64 samples, direct 0.42, ambient 0.68, max_lighting 1, sky 0.1; current (stale_bakes --check: not listed).
- Capture (information): MM9 capture 132.0, unbaked 82.0, baked 55.1 (x0.42).
- Unmatched scripted objects: EboraCam1 cinema/LetterBox, OnFoundPlayer rollover + RolloverText strings (own words),
  Fatc MoveIt/EboraArrive, DP2waterdamage DamageOn, DP2steam FireOn/Off, ImpHenchman Help, EffectsMgr camera quake
  (sound only), BATHHOUSE.scr (unattached), concubine Siren skins.
- Sheets (looked at): review/pages_v02_01-04.jpg, review/lighting_v02_p1-6.jpg, work/fix_round2.jpg, review/water/.
- Not checked: dives and drain animation on the desktop; Fire1/4 with the valve open; Ebora/concubines have no model.
