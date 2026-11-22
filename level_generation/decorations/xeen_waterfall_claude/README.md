# XD-17's white fall (D-50 Q7), 2026-11-21

Lane S. No Meshy, no Codex. The sand-fall's builder (`../xeen_sandfall_claude/`) copied and extended
(`scripts/build_fall.py`: a core `bottom`, per-layer textures and normals, `core_first`, foam and mist layers).

| Decoration | Row / sprite | Model | Binding (`worlds/xeen/models/indoor_decorations.yml`) |
|---|---|---|---|
| `xeen_waterfall` "waterfall" | 4016 / 27016 | `worlds/xeen/models/xeen_deco_waterfall.glb` (5,376 triangles, session 11) | height 2229.46 (1:1), `yaw: facing`, `yaw_offset` -90 deg |

## The fall fits XD-17's rock

The first build (preset `waterfall`, session 7) was a free fall from a sheer face: the drop of 1,760 from a notch at
1,728, as the L1 layout (`places.py` `FALL`) had it. A5's L4 has no sheer face there. The east cliff under the
notch is a slope of triangulated rock at 49 to 56 degrees: from the notch's crest point (7664, 2815, 1941) through the
mid ring (7005, 2573, 906) to the cliff foot (6272, 2304, 0), then about 140 of grass to the pool (surface -40). A
free fall would hang inside that rock (`review/s9/sheet.jpg`: the cliff and the notch from the pool).

So the installed model is preset `waterfall_xd17`: a **cascade** that slides down that slope.
- Its centre line is the measured rock profile. The core sits 26 off the rock along its normal, frays into strands from
  900 to 1,400 below the lip, and every strand runs into the pool.
- Two spray veils sit 40 and 80 off the rock. A foam ring and two mist cones stand at the foot, on the pool.
- `scripts/fit_xd17.py` places the model as the game will. It triangulates `room:valley`'s floor points from
  `devdocs/xeen/briefs/xd17/L4/rooms.yml` and lifts every core and veil vertex that sits within 16 / 34 / 56 of the
  rock (413 of 1,323 core vertices, at most 121). The pool's ellipse is left out, because the water goes under it.
- Then it moves the origin to the foot point.

```
python3 scripts/build_fall.py waterfall_xd17          # work/waterfall_xd17/xeen_deco_waterfall.glb (origin at the lip)
python3 scripts/fit_xd17.py work/waterfall_xd17/xeen_deco_waterfall.glb work/waterfall_xd17/xeen_deco_waterfall_fit.glb
python3 tools/install_model.py --world xeen --name xeen_deco_waterfall.glb <the _fit.glb>
```

If A5 moves the notch, the cliff foot or the pool, change `_SLOPE` in `scripts/presets.py` and `FOOT`, `FACING`,
`LIP_OUT`, `LIP_Z`, `POOL` in `fit_xd17.py`, then rebuild and reinstall.

## Placement (A5)

- Place it at **(6272, 2304)**, the cliff-foot point under the notch, on the floor (z 0), at **facing 200**. With the
  binding's `yaw_offset`, facing is the direction the water pours: west-south-west, along the ray from the notch to the
  foot.
- `gen.py` today adds `deco:falls` at `FALL_AT` (6208, 2304) facing 180. Both values must change: 64 west the model
  would float off the rock, and at 180 it would pour across the slope.
- About 300 wide at the notch, 560 at the foot, 640 in the pool. The mist reaches 600 round the foot and 900 up.
- No collision, no light, no shadow. AU's `sound:falls` belongs at the foot.

## Checks

- Winding: 0 inverted closed parts.
- In game, XD-17 (`build-xeen`), the installed model as a debug spawn at the foot, facing 200
  (`review/s9/fit/sheet.jpg`, tour `work/s9/fit.yml`):
  - the cascade follows the slope from the notch into the pool, with no rock showing through the sheet;
  - the side view (`lipview`) shows the sheet lying on the rock.
- A debug spawn draws the additive spray, foam and mist as plain blended sheets, so the mist cones look like glass
  cups in these captures. Placed as a decoration they add softly, as the sand-fall and lava fall from the same builder
  do on X5 and X7.
- A placed check in XD-17 waits on A5's rebuild.

## Files

- `scripts/presets.py`: `waterfall` (session 7, the free fall, not installed) and `waterfall_xd17` (installed).
- `scripts/build_fall.py`: the builder. `scripts/fit_xd17.py`: the fit to the rock and the origin move.
  `scripts/ingame_x7.py`: session 7's X7 overlay check of the free fall. Its swap never showed the fall
  (`review/ingame2` shows lava falls). `review/ingame1` is a debug spawn of the free fall on a cloud map.
- The session-7 hard-link scratch root `work/root` was removed (unlinked) on 2026-11-21.

## Session 10: the placed look (A5's `output/studio_cal/xd17/shots/s20_falls/`)

A5 placed the fall and reported four faults:
- the mist cones' top rim showed as a hard line across the sky (`03-foot`);
- the same rim showed as a bright band from the cliff top (`05`);
- the strands ended on the grass strip short of the pool (`01`);
- the lip was a thin V with dry grass behind it and no water above the notch (`06`).

**Cause.** The game's static model shader does not apply glTF COLOR_0. It carries placement lighting in that slot, as
the way-up columns' README says. So none of the builder's vertex fades reached the game.

**Fixes** (preset `waterfall_xd17`; the session-9 preset is kept as `waterfall_xd17_s9`, and the session-9 scripts are
in `work/*_s9.py`):
- **Fades.** They now live in the textures (`build_fall.bake_fades`).
  - The mist cones and the foam map v once over their height or radius (`baked`), with no v scroll; their u drift
    keeps the swirl. Their textures carry the old vertical or radial fade (`v_fade`).
  - The spray veils keep their downward scroll and carry a side fade across u (`u_fade`). They now start 250 and 500
    below the lip, so their top edges sit inside the white water.
- **The stream.** A stream now runs down the gully behind the notch. It wells up out of the ground 760 inland:
  `fit_xd17.py` lets the vertices inland of 690 stay buried. It is 110 wide there and 300 at the lip.
- **The foot.** The strands run on over the 140 of grass at the foot and drop over the pool's bank, which lies at
  out 1,623.
- **Sizes.** The mist is lower and narrower (520 / 700 high).
- **Model.** 4,648 triangles before the fit, height 2,279.28. The binding height and row 4016's height were updated
  to match (1:1).

Seen placed in XD-17 at A5's poses plus one above the stream (`review/s10/sheet.jpg`, tour `work/s10/tour.yml`): no
hard rims, soft mist at the foot, water above the notch, strands into the pool. A5's placement is unchanged:
(6272, 2304), facing 200.

## Session 11: the lip from the cliff top (A5's `output/studio_cal/xd17/shots/s22_falls/` 05, 06)

A5: the top of the fall was still a broad pale band with a straight near edge. Seen from the cliff top, the white core
ran the whole gully at 200-300 wide, the brink was one straight white edge across it, and the sheet's sides climbed
the gully walls (two "ears" at the notch).

Preset `waterfall_xd17` now (the session-10 preset is kept as `waterfall_xd17_s10`, its scripts as `work/*_s10.py`):
- **Stream layer** (`build_fall.build_stream`, material `Stream`, blended, drawn first): clear blue-green water
  (texture `stream`, soft sides through `u_fade`, ripples smooth across so no dark stripe runs down it), from where it
  wells up 760 inland to 700 below the brink, narrowing to a quarter under the white water.
- **Narrow, centred stream:** 10 wide where it wells up, 100-120 in the gully, 180 at the brink; `shift` moves it
  onto the gully's measured centre (up to 55 left of the fall's line), so its sides no longer ride the walls.
- **Glassy brink, ragged white:** the white core starts below the brink, each lane at its own drop between 20 and 190
  (middle lanes first) at 12 % of its width, widening over 220 (`core.start`, `start_bias`, `grow`, `start_width`).
  Tried and dropped: lanes starting at the brink as points (white spikes) and at 40 % width (blunt teeth).
- **Spring:** `fit_xd17.py` lets the stream's floor sink to 40 under the rock inland, rising to its clearance by 520
  inland, so the water breaks out of the gully floor along the gully's shape (the old fixed `BURY_BEYOND` row was a
  straight cut).
- Model 5,376 triangles, height 2,229.46; binding height and row 4016's height updated (1:1). Winding 0 inverted.

Seen placed in XD-17 at A5's poses plus three above the stream (`review/s11c/sheet.jpg`; tries in `review/s11`,
`review/s11b`; tour `work/s11/tour_c.yml`). A5's placement is unchanged: (6272, 2304), facing 200.
