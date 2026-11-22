# The Sleeper on his couch (D-58 C7), 2026-11-21

Lane S sub-agent. The sleeper of each elemental plane P1-P4: a shipped giant asleep on an Ancient-steel couch, four
static indoor (BLV) decoration models, one per element. No Meshy, no Codex, nothing spent.

| Decoration | Row / sprite | Model | Height | Radius | LOD triangles |
|---|---|---|---|---|---|
| `xeen_sleeper_fire` (P1) | 4023 / 27023 | `worlds/xeen/models/xeen_deco_sleeper_fire.glb` | 206.4 | 290 | 11,132 / 5,764 / 2,800 / 1,367 |
| `xeen_sleeper_air` (P2) | 4024 / 27024 | `worlds/xeen/models/xeen_deco_sleeper_air.glb` | 206.4 | 290 | same |
| `xeen_sleeper_earth` (P3) | 4025 / 27025 | `worlds/xeen/models/xeen_deco_sleeper_earth.glb` | 206.4 | 290 | same |
| `xeen_sleeper_water` (P4) | 4026 / 27026 | `worlds/xeen/models/xeen_deco_sleeper_water.glb` | 206.4 | 290 | same |

Installed with `tools/install_model.py --world xeen` (sources in `assets_source/worlds/xeen/models/`, cooked runtime
copies in `assets_dev`). The bindings and row values are fragments for the lane to merge:
`integration/indoor_decorations.yml` (`yaw: facing`, `yaw_offset: -1.570796327`, `height: 206.4`) and
`integration/rows.txt` (radius 290, height 206). Nothing in `assets_dev`'s tables or manifests was edited here.

## Models

- **Body**: MM6's Titan, `assets_source/worlds/mm6/models/mm6_ttn.glb`, skin `ttn_b` (black armour, gold trim, red
  crest; it reads the calmest and most regal against the teal steel: A's lavender clashed with it, C's cyan crest
  competed with the water glow; `review/skins/skins_sheet.png`). The clip `Standing` frame 0, then world-axis bone turns
  (`scripts/sleeper.json`): legs closed 5 deg each, upper arms down at the sides, forearms folded across the belly
  (left under right), neck and head bent 16 + 14 deg forward so the head rides on the headrest. Each of the titan's
  four LOD meshes is posed and baked (its own LODs, so the chain keeps the creature's own reductions), laid on its
  back (body up -> -X, face up) and scaled 3.318, the creature's own game scale: 529 long, twice a man.
- **Eyes closed**: the white of the eyes (white texels inside the eye polygons' UV triangles, `build_body.py` ->
  `eyes_lod<n>.npz`) are filled from the surrounding skin (a diffusion fill from skin texels only), 12 % darker, with
  a dark lid line along each eye (`scripts/body_textures.py`). LOD0/1 and LOD2 done; LOD3's 256 map has no eye texels.
  The brow keeps the titan's stern furrow: the face reads as a stern sleep, not a smile.
- **Body textures**: the skin's region ramps are baked into the base colour with the shader's maths
  (`claude_shared/tier_textures.py`): a decoration has no tiers. The titan's normal and metallic-roughness maps are
  kept, metallic factor 0, double-sided as on the creature. Three sets: 2080 x 1024 (LOD0/1), 512 (LOD2), 256 (LOD3).
- **Couch** (built, `scripts/build_export.py`): 644 x 324 overall (deck 640 x 320, the posts 2 proud), square-edged
  and machined: a trim base course (10), a hull-steel body with chamfered corners, a deck slab at 76 (hull top, trim
  edge band), a raised hull headrest platform at the head end (top 90, 160 wide, from the couch's end to 162 from its
  centre), four square trim posts with pyramid caps (92). Glow windows framed in trim on both long sides
  (490 x 26) and both ends (190 x 26), the glass set 3 behind the frame. Flat shading, hard edges everywhere; UVs
  world-scale box projection (hull 256 units per `xahull` tile = 1 texel per unit at x2, trim 128).
- **Materials** (per GLB): body x3 (one per texture set), hull (`xahull` 512 + a normal map from its luminance;
  roughness 0.35-0.7, metallic 0.3), trim (the element's metal, brushed 256 tile, worn by `xahullbn`'s broad tone),
  glow (the only emissive material). Trims: fire warm bronze (190,122,64), air silver (206,210,218), earth dark
  bronze (118,94,58), water verdigris over bronze (86,150,126, metallic 0.25 with bronze at worn spots).
- **Glow**: each element's XD-19 core (`xcorefire`, `xcoreair`, `xcoreearth`, `xcorewater`, the planes' L1 notes name
  them as the couch's glow panel): the core window cropped, laid on its side and mirror-tiled into a seamless 1024 x
  128 strip. Air's violet is moved to a pale white-blue and earth's green to amber (only those hues; the rock keeps
  its own); fire and water as shipped. Emissive factor 0.70 / 0.55 / 0.55 / 0.65 (fire / air / earth / water), below 1
  so the bloom keeps the hue (at 1.0 earth's glow bloomed to white in game).
- LODs: LOD0/1 carry the full couch (396 triangles), LOD2 drops chamfers and frames, LOD3 also the posts.
  Winding: 0 inverted closed parts (all four). The chain is linked by `tools/link_static_model_lods.py`; no normal map
  needed a flip.

## Facing and placement (for A6)

- **Origin** at the couch's bottom centre; z 0 = the floor it stands on (P4: the shelf's top).
- **Facing**: the couch's open long side is its front; with the binding's `yaw_offset` the map's `facing` is the
  direction that front looks. **The head lies at facing - 90 deg**: on the left of someone standing in front
  (facing 90 = front north: head east, feet west). glTF +Z is the front, as on the P5 hands.
- **Footprint** 644 along the couch, 324 across; the giant 529 x 187 (elbows), the top 206 (the crest and feet).
- **Collision radius 290** (the lane's provisional 200 changed): a decoration collides as a cylinder; at 290 the party
  (radius ~37) stops just outside the couch's 322 half-length, so the camera never enters the headrest or the feet,
  and stands ~165 off the long sides. At 200 the party could walk ~85 into either end.
- In game at the L1 spots (debug `model spawn`, each checked): P1 (-4352, 4864) floor 384, facing se (315): fits
  the hall. P2 (4864, 3840) floor 768, facing sw (225): fits under the dome between its pillars. P3 (-2048, -5504)
  floor -768, facing n (90): fits the Hollow. **P4 (-4480, -4608) on the 768 x 512 shelf (top 232), facing ne (45):
  does not fit**: turned 45 deg the couch needs ~684 x 684 and overhangs the shelf's 512 side (seen in
  `review/ingame/water_far.png`). Facing n or s (the couch along the shelf's 768) fits with 62 / 94 to spare;
  otherwise the shelf must turn with the couch.

## Checks

- Review renders (Cycles, eye height 170, dim hall light): `review/final/<element>_sheet.png` (front, three-quarter,
  head end, back, face close-up, far), `review/final/all_q.png` (the four side by side), the skin comparison
  `review/skins/skins_sheet.png`.
- In game (`build-xeen`, isolated runs, debug `model spawn` at each plane's L1 spot with its facing, tours
  `work/ingame/tour_<element>.yml` from `scripts/make_tour.py`, queue `work/ingame/queue.sh`):
  `review/ingame/<element>_sheet.jpg` (front, three-quarter, head end, face, far) and the PNGs beside them. Facing and
  head side as intended on all four; floors meet; the glow reads in its colour; no model warnings or errors in the
  run logs.

## Rebuild

```sh
level_generation/decorations/xeen_sleeper_claude/build.sh [fire] [air] [earth] [water] [--review]
python3 tools/install_model.py level_generation/decorations/xeen_sleeper_claude/export/xeen_deco_sleeper_<element>.glb \
    --world xeen --name xeen_deco_sleeper_<element>.glb
```

Stages: `scripts/expose_lods.py` (the titan's linked LOD meshes as scene nodes for Blender's importer),
`scripts/build_body.py` (pose, bake, lay, scale; `work/body.blend`, `body.json`, eye UVs), `scripts/body_textures.py`
(skin ramps, closed eyes), `scripts/couch_textures.py` (hull, trims, glow strips), `scripts/build_export.py <element>`
(couch, materials, LODs, GLB), `tools/link_static_model_lods.py`, winding. Config `scripts/sleeper.json`. Survey and
review tools: `probe.py`, `pose_preview.py`, `face_probe.py`, `face_check.py`, `review_render.py`, `make_tour.py`.

## Known limits

- The face looks up at about 178 above the floor: from the party's eye height it is seen edge-on, so in game the
  helmet and crest read and the closed eyes show only from above or near the head (`review/final/*_face.png`).
- The crest sweeps over the headrest and dips into it a little at the crown; the back of the skull sinks 1-4 into
  the headrest top (a cushion's give).
- The trims are flat-shaded bars with a brushed grain; in Cycles' grey light the bronzes can read like wood, in the
  engine's light they read as metal (fire copper-bright, earth darker).
- One body for all four planes (D-58 C7); the element is carried by the trims and the glow only.
- Sprites 27023-27026 stay the engine's `pending` texture (never drawn).
