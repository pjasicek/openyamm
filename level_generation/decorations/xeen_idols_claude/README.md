# Xeen demon and devil idols (D-40, XD-16), 2026-11-20

Lane S (session 6). Two black basalt statues for the Volcano Cave's mouth on X7 Mount Firestone (`thing:idol_demon`,
`thing:idol_devil`, `poi:demon_idols`): installed creatures posed, baked into static meshes and stood on carved
plinths. No Meshy, no Codex.

| Decoration | Row / sprite | Model | Height | Collision radius |
|---|---|---|---|---|
| `xeen_idol_demon` ("demon idol") | 4008 / 27008 | `worlds/xeen/models/xeen_deco_idol_demon.glb` | 780 | 165 |
| `xeen_idol_devil` ("devil idol") | 4009 / 27009 | `worlds/xeen/models/xeen_deco_idol_devil.glb` | 820 | 165 |

Bound in `assets_dev/worlds/xeen/models/decorations.yml` (`yaw: facing`, default LOD switch sizes, no jitter).

## Models

- **Demon**: `assets_source/worlds/mm6/models/mm6_demon.glb`, clip `Cast_FireBolt` frame 9 (both hands raised and
  gathered before the chest), eyes (iris and pupil parts) removed so the sockets are empty (the "their skulls are not
  here" hook), the body widened 16 % / deepened 10 % to read hulking, and a pair of carved curved horns added
  (`idols.json` `horns`: a tapered NURBS sweep in the head bone's frame). Width 425, depth 433 (tail behind).
- **Devil**: `assets_source/worlds/mm9/models/mm9_greaterdemon.glb`, clip `Standing` frame 0 with the wing bones
  (`wing|warm`) from `Fidget` frame 29: wings raised in a symmetric V (bone-head asymmetry 0.08 m, `wing_scan.py`),
  claws spread. Wingspan 563, depth 394 (head forward, tail behind). The lesser demon was surveyed and not used (no
  wings; too close to the demon's horned silhouette).
- **Plinth**: stepped square, 320 wide, 96 high (base course, chamfered block, overhanging cap with a chamfered top,
  3 x 3 top grid, open bottom); feet sunk 2 units into it.
- One material each: 2048 base colour, 2048 normal (cooked to half), 1024 metallic-roughness. Base colour baked on the
  low mesh itself: `vlcwl3a` (MM6 volcanic stone x4) grain, box-projected at two scales, mapped onto a near-black
  ramp (linear 0.022-0.20), grey-brown weathering patches, AO (0.6 m) and cavity (0.08 m) darkening, pale ash in
  up-facing crevices and on top faces; sRGB luminance p1 29 / p50 43 / p99 66-71. Normal map projected from the posed
  source mesh with its own normal maps (carved muscle and scale detail); projection misses and wild hits (8-11 % of
  island texels) are flat. Roughness 0.80-0.95, rougher on top faces and in crevices. No emission.
- UVs `claude_shared/uv_atlas.py` (PartUV charts, sparrow pack), figure at 1.7x the plinth's density, 4-texel margin;
  atlas use 65 % / 68 %; nearest-texel gutter fill (`gutter_fill`) on every map.
- Triangles (after the LOD link): demon 4,467 / 2,218 / 1,004 / 372; devil 5,140 / 2,511 / 1,055 / 320 (collapse
  decimation of LOD0, 0.5 / 0.23 / 0.09). Hard edges above 60 degrees (plinth corners, spike ridges). Winding:
  0 inverted closed parts (both).
- Model space: 1 model metre = 100 units (binding heights = the LOD0 bounds), origin at the plinth's bottom centre,
  front toward glTF +Z, so **facing 0 faces +Y (north) and facing 90 faces west (-x)**.

## Placement (for A5)

Replace L3's blockout buildings with entities `decoration_list_id` 4007 (demon, row 4008) and 4008 (devil, row 4009)
at the blockouts' centres (demon ~[65.1, 43.75] north of the mouth, devil ~[65.1, 45.45] south), **facing 90** (both
look west, out of the cave's mouth), z = the ground at the plinth's centre minus ~10-20 on a slope (the plinth's
bottom is open and the base course is 17 high, so up to ~15 of float on the downhill side is hidden by sinking). The
devil's wings reach ±282 across (north-south when facing west): keep its centre at least ~350 from the mouth's
opening edge, the demon's ~250. Their centres ~870 apart (the blockouts' spacing) leave the 384-wide mouth clear.

## Checks

- Review renders (Cycles, eye height 170, sun and sky): `review/final/` (`<idol>_sheet.png` front | three-quarter |
  side | back, `<idol>_head.png`, `pair_front.png`, `pair_q.png`, `pair_far.png`).
- In game (`build-xeen`, X7, debug `model spawn` at the mouth in front of L3's blockouts, party at (-1100, 9725)
  below the slope): `review/ingame/pair.jpg` (both at their spots, yaw facing 90) and `sheet.jpg` (each idol turned
  front / three-quarter / side). The stone reads dark slate grey in the X7 light; facing 90 faces the party to the
  west as expected. Run log: no errors or warnings for the models (`review/ingame/run.log`; tour `work/tour.yml`).
  The bindings and rows loaded with the run (Xeen world mounted, no table or binding errors).

## Rebuild

```sh
cd level_generation/decorations/xeen_idols_claude
./build.sh [demon] [devil] [--review]     # high -> LOD0 + UVs + bakes -> maps -> LODs + export -> link + winding
python3 ../../../tools/install_model.py export/xeen_deco_idol_demon.glb --world xeen   # from the repo: tools/...
```

Stages: `scripts/build_high.py` (pose, static bake, horns, plinth, `work/<id>/high.blend` + previews),
`scripts/lowbake.py` (LOD0, UVs, normal / colour / roughness bakes), `scripts/finish_maps.py` (miss clean-up, gutter
fill, MR packing), `scripts/export_idol.py` (LODs, GLB), `tools/link_static_model_lods.py`. Config `scripts/idols.json`.
Survey tools: `pose_probe.py` / `sheet.py` (every clip at four frames), `pose_preview.py` / `rowsheet.py` (candidate
poses), `wing_scan.py` (symmetric wing frames), `bones.py`. Blender goes through lane S's serialising wrapper. The
sparrow packing is stochastic, so a rebuild changes the UV layout (rebake follows automatically).

## Known limits

- Collapse decimation of the 9k-triangle creatures leaves visible facets on the demon's arms and claws up close.
- The demon's raised hands cover the lower face from the front at close range; the horns and brow stay clear.
- The devil's tail hangs free behind the plinth (as carved stone it would need a support); it stays above the plinth
  top's level only near the body.
- AO is baked into the base colour (deliberate for a static statue).
