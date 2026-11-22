# D7's sky-barges and the celestial boat, 2026-11-21

Lane S, session 10. Hand-built in Blender from a script, with no Meshy and no Codex (0 credits). These are the set
pieces from the D-58 S list for D7, "The Skyroads":

- the four Merchants of the Elements' gilded sky-barges, one model per element tint;
- the celestial boat moored at Lucio's dock, the boat that brought the party up.

They replace A6's stand-in blocks: `platform:barge_<cargo>` and `_rail` in `output/studio_cal/d7/tools/gen.py`
`barges()`. The texture `xsbarge` is no longer needed.

| Row / sprite | Decoration | Model (`worlds/xeen/models/`) | Tint |
|---|---|---|---|
| 4051 / 27051 | `xeen_skybarge_fire` "sky-barge" | `xeen_deco_skybarge_fire.glb` | red-orange (the smoke merchant's) |
| 4052 / 27052 | `xeen_skybarge_air` "sky-barge" | `xeen_deco_skybarge_air.glb` | pale silver-white (dust) |
| 4053 / 27053 | `xeen_skybarge_earth` "sky-barge" | `xeen_deco_skybarge_earth.glb` | amber-bronze (mud) |
| 4054 / 27054 | `xeen_skybarge_water` "sky-barge" | `xeen_deco_skybarge_water.glb` | sea-green (steam) |
| 4055 / 27055 | `xeen_skyboat` "celestial boat" | `xeen_deco_skyboat.glb` | white with a pale-blue sail |

Each row has radius 0. The bindings are in `assets_dev/worlds/xeen/models/indoor_decorations.yml`: `yaw: facing`,
`yaw_offset` -90 deg, height 721.0 for the barges and 569.3 for the boat. That height is the model's own height, so
the scale is 1. Each binding has a comment block.

Which tint goes to which merchant is my choice, by the cargo's main element: smoke is fire, dust is air, steam is
water, mud is earth. A6 can swap the decoration names freely; the four models differ only in tint.

## What they are

**Sky-barge** (1024 long, 384 wide at the gunwale):
- **Hull:** a lofted plank hull. It has a curved keel with rocker, so the side view is a crescent, and a sheer that
  sweeps up from 56 over the deck amidships to 206 at the ends.
- **Gunwale:** a carved gilt frieze band (56 high) under a fluted gilt rail cap, plus a gilt wale 100 lower.
- **Ends:** gilt scroll posts at prow and stern. The prow curls forward and up; the stern curls back over the
  deck.
- **Deck:** a low plank deck at the origin.
- **Rig:** a mast 300 forward of the middle, a yard, and a bellied 300 x 236 sail with a glowing element sigil. A
  damask pennant and a glowing orb sit at the masthead.
- **Canopy:** a damask canopy on four gilt posts, centred over the port gangway (y -112 to +232). Its ridge has a
  glowing orb at each end.
- **Gangway:** a gap in the port bulwark, 96 wide, amidships. A gangplank reaches 160 beyond the hull's side, flat at
  deck height.
- **Dressing:** three carved crates forward of the canopy.
- **Glow:** a glowing runner along the keel (the hull floats on it) and four glowing medallions on each side.
- **Bounds:** x -191 to +352 (the gangplank), y -682 to +522 (prow scroll to stern scroll), z -196 to +525.

**Celestial boat** (736 long, 266 wide): the same family, smaller.
- The same hull, frieze, rail, wale and scroll posts.
- A mast at y -40 with a 230 x 196 sail, white with a pale-blue ground, and a glowing sigil.
- A pennant and a masthead orb.
- Two thwarts.
- The keel runner and three medallions a side.
- No canopy and no gangplank.
- **Bounds:** x +/-133, y -492 to +371, z -144 to +425.

**Origin:** the deck's centre at deck height (deck top = z 0) for every model.

**Facing:** the way the prow points (glTF +Z is the prow; Blender -Y). The port side, with the gangway and gangplank,
is to the left of the facing, at facing + 90 deg.

**Radius 0, no collision.** Decorations collide only as a cylinder, which is useless for a hull. The models are
clickable through their static model (picking), like the other radius-0 pieces.

## Look, textures, density

The colour lives only in the textures. The static shader draws no COLOR_0, so the keel-ward darkening and the gilt
lines are painted into the atlas. The glow is the glTF emissive (an emissive texture with bloom). Every material is
opaque, so a debug spawn shows the models exactly as a placed decoration would.

- `skybarge_trim` (2K, shared by all five models, so it is cooked once): hull planks, carved frieze, deck planks, the
  bulwark's inside, fluted gilt moulding, carved panel, plain gilt, plain wood. The sources are:
  - MM8's `t66floor` (x4 master), turned to run along the hull and graded per use;
  - the Throne of Legends' wood atlas, `../xeen_throne_claude/work/throne_img0.png` (the carved panel and plain
    wood);
  - its gilded copy, `../xeen_throne_claude/work/tex/gold_base.png` (the fluted moulding and plain gilt).
- `skybarge_cloth_<tint>` (1K, one per tint): the canopy damask, the sail weave, the glow medallion and the glow strip.
  The sources are:
  - MM8's `t66d01p2` damask, its red ground re-tinted per element with the gold swirls kept;
  - the grey weave of `gold_base.png`, re-tinted;
  - the medallion and strip, drawn in the script.
- Materials, each one draw per LOD: `skybarge_trim`, `skybarge_cloth_<tint>`, and `skybarge_glow_<tint>` (the same
  image, emissive).
- Texel density: 2 texels per game unit (200 per Blender metre) everywhere, rarely seen caps and posts aside. UVs stay
  inside 0–1 (long parts are squeezed into their row). Port and starboard share UVs on purpose (mirrored halves). Rows
  have an 8-texel dilated gutter.
- Base colour is clamped to sRGB 30–243. Metallic is 0 everywhere; the gilt reads from colour. Roughness is 0.6 for
  the trim and 0.85 for cloth.

## Triangles (after export)

| Model | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---|---|---|---|
| each sky-barge | 2,772 | 1,520 | 648 | 320 |
| celestial boat | 2,440 | 1,232 | 572 | 276 |

The LODs are rebuilt from the same parameters at lower detail, not decimated:
- fewer hull stations and girth rows;
- fewer post samples and sides;
- LOD2 drops the medallions, crates and gangway gap;
- LOD3 drops the glow, orbs and pennant.

`tools/link_static_model_lods.py` links them. Winding: 0 inverted closed parts for all five models.

## A6's placement (D7, `gen.py` / `gen_objects.py`)

`scripts/placement.py` computes these spots from `gen.py`'s own islands and jetty. It writes `work/placement.json`;
rerun it if the islands move. Each barge lies along its island's rim edge, fully over the void. Its port gunwale is
16 off the rim at the closest point, and the gangplank rests on the island. There is nothing walkable under any hull;
the script checks this. In the decorations, `floor_height` is the island floor, so the deck is level with the island.

| Barge | Decoration | `at` | `floor_height` | `facing` | Merchant stands at | Gangplank end |
|---|---|---|---|---|---|---|
| smoke | `xeen_skybarge_fire` | (-29277, 2797) | 1152 | 325 | (-29021, 3165) | (-29076, 3086) |
| dust | `xeen_skybarge_air` | (-1553, 20276) | 1280 | 184 | (-1518, 19830) | (-1526, 19926) |
| steam | `xeen_skybarge_water` | (6976, -19504) | 768 | 56 | (6606, -19252) | (6685, -19306) |
| mud | `xeen_skybarge_earth` | (29449, 4231) | 1152 | 22.5 | (29277, 4645) | (29314, 4556) |

1. **Remove** both stand-in blocks, `platform:barge_<cargo>` and `platform:barge_<cargo>_rail`, and add the
   decoration as `deco:barge_<cargo>`, for example from `barges()` or `gen_objects.decorations()`.
   - The facing follows the rim edge, not the stand-in's `deg + 87`. That differs by 8 to 20 deg.
   - Facing + 90 deg points at the island.
2. **Move the event source.** `evt:merchant_<cargo>` uses `source: platform:barge_<cargo>`. Change it to
   `deco:barge_<cargo>`, as the lamps do. Clicking the barge then runs `Xeen.merchantRiddle`.
3. **The dust merchant must move.** `poi:merchant_dust` (-1536, 17184) stands at the mouth of the Olympus causeway,
   which D-58 put there. The stand-in barge blocked the causeway's start; a model there would sit across the road.
   - The barge goes on the north crossing's north rim instead (the island's middle toward (-1536, 21000)), clear of
     every road.
   - Move the merchant to (-1518, 19830).
4. **Recommended: not boardable, and no deck block.** The merchant stands on the island at the foot of the gangplank;
   the table gives the spot. The hull is fully over the void, so the party cannot walk into it, and no invisible
   geometry is needed.
5. **Optional: make the deck walkable.** Studio blocks cannot be invisible, so hide the block inside the hull.
   - Add a 512 x 288 block at the barge's `at` with the same facing, its top at `floor_height - 2` and at most 150
     thick. It then stays inside the hull and under the deck.
   - Add a 96-wide bridge block under the gangplank, from the deck block to the island. It shows only as a strip 2
     under the plank across the 16-unit gap.
   - The rails do not collide, so a party can walk off the starboard side into the void. That is why I recommend the
     first option.

**The celestial boat** goes alongside the jetty's north-east side, near its end:
- `deco:lucio_boat` `xeen_skyboat` at (1429, 2423), `floor_height` 1780, `facing` 327 (the jetty's own direction,
  -32.84 deg, so the prow points out to the void).
- The jetty (`platform:olympus_jetty`) runs from (-1984, 4064) to its end at (1536, 1792). It is 640 wide, its top is
  at 1804 and its facing is -32.84.
- The boat's centreline is 472 off the jetty's centreline: 24 clear of the jetty's edge.
- The stern is 800 back from the jetty's end, and the prow is 64 short of it.
- The deck is 24 under the jetty top, so the gunwale is 20 above it amidships.
- Mooring on the south-west side instead puts the boat at (917, 1630) with the same z and facing.
- **Optional:** the jetty's rail on that side, `platform:olympus_jetty_rail1` (96 high), hides the hull from someone
  on the jetty; only the sail and scroll posts show over it. To show the boat as docked, end `rail1` 832 short of the
  jetty's end, so the open stretch lies alongside the boat. The jetty's end is already open, so this adds no new kind
  of drop.

## Build

```
python3 scripts/textures.py                              # work/tex/*.png + layout.json
blender -b --factory-startup --python scripts/build.py -- all    # work/<name>_raw.glb (LOD0..LOD3 objects)
python3 <repo>/tools/link_static_model_lods.py work/<name>_raw.glb export/<name>.glb
python3 ../mm8_3d/animated/scripts/check_winding.py export/<name>.glb
python3 <repo>/tools/install_model.py export/<name>.glb --world xeen --name <name>.glb
python3 ../xeen_p5props_claude/scripts/append_rows.py rows.json --apply    # done once
python3 scripts/placement.py                             # A6's spots (work/placement.json)
python3 scripts/tour.py                                  # work/ingame/d7.yml (menu-input tour)
blender -b --factory-startup --python scripts/review.py -- review/renders export/*.glb
```

- Blender is the lane's wrapper, `../../creatures/xeen_tiers_claude/bin/blender`.
- `<name>` is `xeen_deco_skybarge_<fire|air|earth|water>` or `xeen_deco_skyboat`.
- `scripts/hulls.json` holds the hull dimensions shared by `build.py` and `placement.py`.
- `scripts/texscan.py` made the contact sheets used to pick the source textures (`work/scan_*.png`).

## Checks

- Winding: 0 inverted closed parts. `--headless-validate-actor-models --world xeen`: 0 refused.
- Renders: `review/renders/` has six views per model, the LOD ladders and `all_q.jpg`.
- In game, `review/ingame/`, with the sheets `ingame1_sheet.jpg` and `ingame2_sheet.jpg`:
  - Debug spawns at the spots above, on `build-xeen` with `xeen_d7.blv`. The tour is `work/ingame/d7.yml`, spawn
    scale 100, yaw = facing - 90 deg.
  - Shots from each island at eye height (`*_near`), and from 1,600 (barges) or 2,400 (boat, across the void) away
    (`*_far`).
  - The installed BLV still has the stand-in blocks. They overlap the fire, water and earth barges in those shots.
    The air barge's spot is new, so its near shot shows the clean result: gangplank on the island, gangway, canopy and
    sail.
  - The boat's shots look over the jetty's rail from its end, and across the void from the north-east road.
- Seen in game: the sails stand edge-on to most light, so they read darker than the canopies (fire deep red, earth
  brown-amber). The tint still carries through the canopy, pennant, glowing sigil, orbs, medallions and keel runner.
