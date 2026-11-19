# Tularean Forest dock repair, 2026-11-19

Map: `assets_dev/worlds/mm7/maps/7out04.odm`. Location: X -14272, Y -6444, deck Z 1344.

`Dock4c_E`, model 114, faces 57 and 58 overlapped on the same plane. Both had the correct
`7trimd` texture, but Cycles baked black pixels where the surfaces coincided. Face 58 now omits
its first vertex: the removed triangle is already covered by face 57. The remaining quad keeps
its native vertex UVs. No face ids, event bindings, model counts or file lengths change.

The focused repair producer writes a review copy and rejects unexpected source geometry:

```sh
python tools/lighting/fix_tularean_dock.py --output output/tularean_dock_repair/7out04.odm
```

After applying that review copy, rebake with the installed recipe's exact `profile` using
`bake_outdoor.py`; install its `.lighting` and `.bake.json` together. Geometry and lighting
must be delivered together. Do not apply the repair script again to an already repaired map.

The installed result uses Blender 5.3.0, CPU, 64 samples, the existing 315-degree sun and
unchanged sun/sky strengths. Native BMP materials were obtained from the source-assets
submodule at the parent repository's recorded commit, not reconstructed from cooked textures.

Verification:

- Only model 114, face 58 changed in the parsed map.
- Triangle intersection area decreased from 458752 to zero native square units; union area
  is unchanged, so the repair introduces no hole in the deck.
- Interior barycentric illumination samples on faces 57/58: black samples decreased from
  38/56 and 47/84 to 0/56 and 0/56 respectively.
- Geometry identity and all 148 lighting dependency hashes match the installed files.
- The existing executable's headless map-load command returned zero. No desktop visual
  capture was made and no game build was run.

Local review files, original backups, bake intermediates and numerical audit are retained in
`output/tularean_dock_repair/` (not committed).
