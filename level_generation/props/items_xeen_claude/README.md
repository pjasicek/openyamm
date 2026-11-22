# Xeen ground items in 3D (2026-11-20)

The Xeen world's own item icons (`xeen_item_*`, the [Xeen icon project](../../ui/xeen_item_icons/)) as 3D models
lying on the ground, so no Xeen item draws the missing-model placeholder
([behaviour](../../../devdocs/GROUND_ITEMS_3D_BEHAVIOUR.md) §2). Owner: lane A2 (data and balance). The route is
MM9's ([items_mm9_claude](../items_mm9_claude/README.md)): Blender components, Codex paint + material mask over grey
guides, registration and a mask-driven PBR bake; no Meshy.

## Status

**Done (2026-11-20): 39 designs built, textured and installed, 41 icons bound** in
`assets_dev/worlds/xeen/world_items/items.yml` (39 models in `assets_source/worlds/xeen/world_items/models/`, every
one 0 inverted closed parts, `ledger.json`; 2 icons reuse engine models; 7 of the models are lane S's Meshy statuettes
and dolls, below). Every Codex painting registered (six with one view left out by the bake's tolerance: the widget's
top mask, the bridles' front and back, the top view of the Might, Endurance and Lord Xeen Dolls).

**Scope change (the user, 2026-11-20): ground models only for quest items.** The new weapon bases (katana, scimitar,
flamberge, naginata, glaive, great axe, flail) and the artifacts (12500-12506, 12510, 12511, 12522, 12524-12528,
12530) are dropped or reskinned onto MM6-MM8 items with engine models: route `dropped`, not bound (the katana, already
installed, was removed again). Their builds and paintings stay in `work/` and `codex_tex/` (23 designs, all painted),
should one come back. Barok's Pendant (x12523) stays: it is now quest item 12152.

In game (X1 Vertigo Meadows, `scripts/ingame_check.py`, 60 quest items, one per icon the quest items use, on the
meadow east of the town; `review/ingame/0*.png`, `review/ingame/game.log`): no load error; placeholders only for the 7
Meshy items below and for 12524-12527 (Holy Book, Chalice, Songbird, Jewel of Ages), which items.txt still flags Quest
with their own icons until A2's reskin lands. Rerun after the Meshy installs (`review/ingame_meshy7/0*.png`, close
shots of the seven, HUD off; `review/ingame_meshy7/game.log`): no placeholder at all, the seven stand on their feet or
plinths beside the bell, the chalice and the raven.

## Routes (routes.tsv, classification.json)

64 icons, one design each (`x<file suffix>`); the seven base icons (katana, scimitar, flamberge, naginata, glaive,
great axe, flail) serve every tier of their weapon.

| Route | Designs | What |
|---|---:|---|
| blender | 32 | `build_xeen.py`: `auto_weapon` from the icon silhouette (wand, whistle, emerald handle), `rock` (10: stones, rocks, melon, tribble, scarab), `outline_slab` (3: sigil, golem stone, root), sphere, disc, book, amulet, upright vessels (jar, bell), custom builders (coin, crystals, widget, magnifying glass, two soul boxes, cube, two bridles, scepter) |
| reuse | 2 | Ligono's Skull -> `engine/world_items/models/item_skull.glb`, Golden Dragon Statuette -> `item_statuet5.glb` (the engine bindings' lengths) |
| meshy | 7 | Sculptural, lane S's (below): Meshy Smart Topology shapes stood up by `stand_meshy.py`, then the same paint + mask bake |
| dropped | 23 | Not quest items (scope change above): built and painted, not installed or bound |

Binding length: the icon's longest opaque side in logical pixels x 0.9 (MM9's rule); the standing items (jar, bell,
the Meshy statuettes and dolls) take the icon's width, so they stand about as tall as the icon shows them.

### Meshy designs (lane S), installed and bound

x12349 Golden Pegasus Statuette, x12351 Golden Griffin Statuette, x12367 Might Doll, x12368 Speed Doll, x12369
Endurance Doll, x12370 Accuracy Doll, x12371 Lord Xeen Doll: installed 2026-11-20 like the Blender designs (ledger
route `meshy`, builder `stand_meshy`).

**Lane S progress (session `xeen-s3`, 2026-11-20).** Route: the [3D ground item
playbook](../items_claude/GROUND_ITEM_3D_PLAYBOOK.md) (Codex master -> Meshy Smart Topology untextured 5 credits ->
this project's paint + mask bake). `scripts/meshy_masters.py` (lane S's) writes each design's keyed
`meshy/<d>/references_hd/design_painting.png` and `CODEX_BRIEF.md`; the masters were run with `xitem.py codex`.
- **Done:** the seven `00_three_quarter.png` masters (Codex, first renders, accepted: faithful to the HD paintings;
  the dolls stand with their arms clear of the body, the archer's bow clear of it).
- **Done: Meshy Smart Topology** (approved limit 45; 35 spent, 7 x 5, no retry; receipts in
  `meshy/creature_3d_progress.json`): `meshy/meshy/<d>_st_v1/model_urls_glb.glb`, 2,874-3,323 triangles each, plain
  renders `review/plain/<d>_meshy_*.png` checked: every shape right (the Speed Doll's yarn hair comes as shards; the
  paint must carry it). Lease released.
- **Done: stood, painted, baked, installed and bound (session `xeen-s3` sub-agent, 2026-11-20; no further Meshy).**
  `scripts/stand_meshy.py` stands each Smart Topology shape the jar's way (Z up, front -Y, lowest point 0, footprint
  centred, longest horizontal side = the length) and cleans it (welded, degenerate faces dissolved, closed parts with
  a negative signed volume reversed: the Speed Doll had 402 such faces). Lengths: `classify.py` treats the seven as
  standing items (icon width x 0.9: 34.2, the Speed Doll 31.5, the Endurance Doll 30.6), so they stand 43-52 units
  tall. `designs.py` now emits route `meshy` designs (`geometry: meshy_st`, `tris` 3,000, dolls `[cloth, leather,
  metal, horn]`, interior cloth); the statuettes are one material in `design_overrides.yml` (`surface_material:
  metal`). `pipeline.py` (`PREP_PARALLEL=1` from the environment), Codex paint 7/7 first try;
  `install_xeen.py` records the design's own route. Triangles as Meshy made them: 3,284 / 3,323 / 3,127 / 3,358 /
  3,199 / 3,197 / 3,127 (Pegasus ... Lord Xeen). Review: `review/final_meshy7.png`, `review/final/<d>_*.png`.
- **Speed Doll's hair:** Meshy's yarn hair was 780 faces of loose shards (slivers, some open sheets the engine would
  cull into holes). `stand_meshy.py` `hair_cap` (design_overrides.yml) removes them and caps the scalp they covered
  with one closed lumpy shell (the head's faces under the shards, subdivided once, lifted with noise, an inner copy
  under the scalp and a rim); the brief names it as the yarn, and Codex painted it as ginger yarn strands.
- **Lord Xeen Doll:** Codex returned an 887x1774 canvas (not 3:4), which the cell split rejects; the raw is kept in
  `codex_tex/x12371/superseded/`, and `paint_mask_raw_v2.png` is the same image resampled to 1536x2048 (registration's
  per-view box fit corrects the aspect; four views pass, the top view is left out).

## How to rerun (scripts/, copied from items_mm9_claude and adapted)

1. `python3 -I scripts/classify.py` (routes from the icon project's manifest.yml), `python3 -I scripts/designs.py`
   (designs.json with `design_overrides.yml`: rock and slab parameters, single-material designs, mask classes).
2. `blender --background --python scripts/build_xeen.py -- <design>...` -> `work/procedural/<d>.glb` (route meshy:
   `scripts/stand_meshy.py -- <design>...` from `meshy/meshy/<d>_st_v1/`); clay review
   `blender --background --python scripts/review_render.py -- work/procedural/<d>.glb review/plain/<d> plain`.
3. `python3 -I scripts/pipeline.py [<design>...]`: prep (guides), paint brief, Codex paint (4 sessions at once,
   `xitem.py codex`), registration, bake, `review/final/<d>_*.png`. At most two Blender processes (PREP_PARALLEL 2).
   Image-filter fallbacks: `python3 -I scripts/xitem.py neutral-brief <d>` then rerun, last `icon_paint.py`.
4. `SHEET_CELL=220 python3 -I scripts/sheet.py <out.png> final <d>...` (icon, painting, three renders per design).
5. `python3 scripts/install_xeen.py <d>...` (winding check, `tools/install_model.py --world-items --world xeen`,
   ledger.json, then the bindings file with the reuse lines and `tools/item_model_shapes.py`);
   `--bindings` rewrites the bindings only.
6. In game: `scripts/ingame_check.py` (its docstring has the commands).

## Known compromises

- Sandro's Heart: the jar is opaque (MM9's compromise), the heart painted on its front and back.
- Rocks, the scarab and the tribble are noise-displaced spheres: veins, crystals, the carved yak, the scarab's gold
  edging and legs are painted, not modelled. The scarab is a smooth dome.
- Flat items (sigil, golem stone, Phirna root) are the icon outline extruded; the sigil's loop is solid.
- The bridles are three strap loops, a standing headstall loop, a bit and buckles: a simplified coil, not the icon's
  exact harness.
- Xeen's Scepter lies flat with its clock face up (a disc, a ring and eight spikes in its plane).
- The cube, chests and coin are as large as the icon rule makes them (39.6 units across).
- Meshy statuettes and dolls: the Golden Pegasus and Griffin (43-45 units tall) stand lower than the reused Golden
  Dragon (`item_statuet5`, 64 tall), as the width rule makes them. The Speed Doll's hair is a smooth lumpy cap painted
  as yarn, not the icon's loose shaggy mop. Back faces of Meshy's open pleated skirts (Speed Doll's tunic hem) are
  culled in game, so a pleat gap shows the legs; small paint smears remain on the Speed Doll's boots and one upper arm
  and in the Might Doll's stripes (fine at game distance). Three dolls lack the top view's paint (registration
  tolerance): the heads' tops take the side views' colours.
