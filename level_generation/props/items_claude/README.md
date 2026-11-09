# Ground item models (2026-10-16)

**Restored as isolated WIP (2026-10-18):** all 911 icons are available under `engine/world_items/` in source/runtime
assets. Local `[rendering] item_models=true` enables them; releases exclude them. See the
[six-worker handoff](parallel_20261018/README.md) before installing or generating; it supersedes old redo notes.
The original rollback archive remains intact. Dated sections below describe earlier production.

**Weapon follow-up:** the [five-session weapon rebuild](weapons_parallel_20261018/README.md) now owns all 296
weapons/wands, with unlimited Meshy credits authorized. Earlier weapon-relief acceptance is superseded.

3D models of items lying on the ground, generated from their restored x2 inventory icons. Plan, audit and next waves:
[GROUND_ITEMS_3D_PLAN.md](../../../GROUND_ITEMS_3D_PLAN.md). Pilot: the 68 swords (MM6-MM8, item table skill group
`Sword`), installed and bound.

## Engine binding

`assets_dev/engine/world_items/items.yml` (schema `openyamm.itemModels.v1`, written by `install_family.py`) binds a model
to an inventory icon (`items.txt` `Pic File`, lowercase), so items sharing an icon share a model:

```yaml
items:
  - {icon: 2hsword1, model: engine/world_items/models/item_2hsword1.glb, length: 156.2}   # Claymore
```

`length` is the world length of the model's longest horizontal side. `game/fx/ItemModelBindings.*` parses it;
`WorldFxSystem::loadItemModels` (outdoor view and indoor renderer, at map load) reads the bindings and loads a model
the first time a bound item shows (`m_loadedItemModels`). `syncItemModels` (in `syncProjectileFx`) keeps one static
stand-in model per item from `IGameplayWorldRuntime::collectWorldItemPresentationStates` (outdoor world items without
gold, indoor map-delta sprite objects carrying a pickable item), in its baked resting pose, turned by a yaw hashed from its key.
Outdoors the item sampler (`OutdoorGameView`) puts it on the drawn terrain (`OutdoorTerrainMaterials::renderedHeight`:
the mesh vertices' heights, with the beach and seabed shaping; not the collision height) half a unit up, tilted to the
drawn slope, when the item rests on the terrain (within 16 units); on a bmodel or indoors it lies level at its
position. Indoors the models follow the portal-revealed sectors (`setObjectModelVisibility`). The renderers skip a bound
item's billboard and send the hover outline to the model (`setItemModelOutline`); picking keeps the sprite-sized area.

Model contract: resting pose baked in (the engine adds only a yaw and the ground's slope), icon up along +Y
(Blender), thickness along Z, lowest point at 0, origin at the centre of the footprint, 1 Blender unit = 100 x2 icon
pixels (the binding's length sets the world size of the longest horizontal side).

## Generator (`scripts/`)

1. `python3 -I make_icon_textures.py <family>`: the family's real items from the merged item table, per distinct
   icon its x2 icon on a power-of-two canvas with colours dilated outward (`textures/<icon>.png`) and the manifest
   `work/<family>_manifest.json` (items, canvas, opaque box, length = opaque height / 2 x 0.9: 1.25 x the swords'
   ground sprites, at the user's request for readability; longsword about 165 units, claymore 195, cutlass 116).
2. `blender --background --python build_icon_relief.py -- <family> [icon ...]`: the icon relief. Outline from the
   alpha (marching squares at 0.5, every loop including holes such as knuckle bows), simplified (RDP 1 px), constrained
   Delaunay with interior points every 10 px; each vertex rises by its distance d to the outline (x2 px):
   z = 3.5 (1 - e^(-d/3.5)) + 0.1 d, so edges bevel at about 45 degrees, grips and guards come out nearly round and
   blades a low ridge. Front and back mirror each other and meet at the outline (closed). UVs straight onto the icon,
   which is the base colour (its painted light stays); roughness per family template (`TEMPLATES`). Propped
   (template `prop`: pitch, roll; swords 9 and 7 degrees): the piece rests on its tip with the hilt end raised (the
   end whose outer third is wider, the guard) and turned a little about its length, dropped onto 0.
   Output `work/<family>/<icon>_export.glb`.
3. `blender --background --python review_items.py -- <family> [icon ...]`: renders from above, three-quarter and low
   (`review/<family>/`).
4. `python3 -I install_family.py <family> [--bindings-only]`: winding check (0 inverted closed parts), install as
   `engine/world_items/models/item_<icon>.glb` (`tools/install_model.py --world-items`; flat names because the model cook needs the
   files directly in `models/`), rewrite `items.yml` from every installed family's manifest.

Swords: 68 models, 93-478 triangles (median 218), 8-16 KB each cooked, 644 KB together.

Installed (2026-10-16): every MM6-MM8 inventory icon, 911 icons for 1894 items, 21 MB of cooked models, in 25
families. `contact_sheet.py <family> [view view]` puts each icon beside two review renders
(`review/<family>_sheet_<n>.png`; `front` and `back` look from the painting's own view, for the solids below).
`make_icon_textures.py` gives each icon to the first family that took it (scroll and quest items share icons).

Relief families (`build_icon_relief.py`):

| Family (`make_icon_textures.py` predicate) | Icons | Thickness (round, slope) | Prop (pitch, roll, raised end) | Median length |
|---|---|---|---|---|
| swords (skill Sword) | 68 | 3.5, 0.1 | 9, 7, guard | 161 |
| daggers (Dagger) | 31 | 3.5, 0.1 | 9, 7, guard | 98 |
| spears (Spear: spears, tridents, halberds) | 45 | 3.5, 0.12 | 6, 6, butt (head on the ground) | 253 |
| axes (Axe) | 38 | 3.5, 0.06 (thin blades) | 8, 6, handle | 141 |
| maces (Mace, Club; flails, hammers) | 43 | 4, 0.35 (round heads) | 8, 6, handle | 127 |
| staves (Staff) | 15 | 4, 0.2 | 6, 6, narrow end | 254 |
| bows (Bow: bows, crossbows) | 36 | 3, 0.1 | 3, 5 | 178 |
| blasters (Blaster) | 5 | 4, 0.2 | 4, 6 | 112 |
| wands (equip WeaponW) | 15 | 3.5, 0.2 | 8, 6 | 72 (family scale 0.6: wand icons are drawn as tall as swords) |
| shields (equip Shield) | 38 | 2.5, 0.02, dome 0.18 | 0, 4 | 106 |
| armour (equip Armor: leather, chain, plate) | 54 | 2.5, 0.02, dome 0.22 | 0, 3 | 106 |
| scrolls (equip Sscroll, Mscroll) | 17 | 9, 0 (rolls come out round) | 0, 4 | |
| amulets (Amulet) | 20 | 2.5, 0.05, dome 0.08 | flat | family scale 0.8 |
| gauntlets (Gauntlets) | 18 | 3, 0.15, dome 0.2 | 0, 5 | |
| gems (Gem) | 32 | 3, 0.3, dome 0.3 | flat | family scale 0.7 |
| lumps (Ore, Reagent, Herb, food) | 59 | 3, 0.25, dome 0.25 | flat | |
| misc (equip N / A: quest items, keys, letters, tools) | 182 | 3, 0.12, dome 0.1 | flat | |

Solid families (`build_oblique.py`, for icons painted as an oblique view of the item; their length is the icon's
width, `WIDTH_LENGTH`, since the icon's height becomes the item's height):

| Family | Icons | Shape | Template |
|---|---|---|---|
| cloaks (Cloak) | 24 | pile | elevation 20, depth 0.75 x width, superellipse power 4; family scale 1.4 |
| belts (Belt) | 18 | loop | depth 0.85, band 0.55 x icon height, wall 3 px |
| books (Book) | 13 | pile | elevation 30, depth 0.7, power 10 (boxy) |
| helms (Helm) | 40 | pile | elevation 15, depth 0.8, power 2.5 |
| boots (Boots) | 19 | pile | elevation 10, depth 0.45, power 3 |
| rings (Ring) | 41 | pile | elevation 30, depth 0.7, power 2.5; family scale 0.55 (a loop smeared the gem away) |
| gold (gold heaps) | 9 | pile | elevation 30, depth 0.8, power 1.6 |
| bottles (Bottle) | 31 | lathe | standing, a ring per painted row |

A pile's footprint front follows only the broad slope of the painted bottom edge (capped at half the depth): at a low
elevation every pixel of a detailed edge (cheek guards, soles) would otherwise push its column far back.

Plates (`build_icon_relief.py` template key `dome`) curve the mid-surface (front and back alike) by that fraction of
the deepest outline distance, so a shield or cuirass is a plate with a concave back resting on its rim.

`install_family.py` re-installs an icon whose runtime copy is missing after its pass: a model cook started by another
session at the same moment dropped a few freshly cooked copies as "without a source".

## Real 3D families (second round, 2026-10-16)

After the user's review of the test map (gold heaps, spellbooks, potions, helmets, boots, rings and cloaks read as
paintings on guessed shapes, "not really 3D"), the user chose: three helmets and three boots in Meshy, gold heaps and
books built in Blender. The other families stay as they are until reviewed.

- **Gold heaps** (`scripts/build_gold.py`, all 9 gold icons): real coins. Octagonal discs (radius 1, thickness 0.16,
  no bottom face) on a low dark mound, lying on its slope with a random tilt and spin, count from the icon's painted
  area (about 60 to 140 coins), short stacks on the larger heaps; one shared embossed coin texture made by the script
  (`textures/gold_coin_*`), metallic 1, roughness 0.32; COLOR_0 darkens coins low in the heap. 1,100-3,600 triangles.
  Gold heaps on the ground now show their model too (the outdoor presentation used to skip gold).
- **Books** (`scripts/build_books.py`, all 13 book icons): cover boards overhanging a page block on three sides, a
  rounded spine, cream page edges with page lines; 46 triangles. The texture atlas (`textures/<icon>_book_basecolor`)
  is built from flat, straight-on cover and spine paintings by Codex from each icon (`books_hd/`, briefs
  `CODEX_BRIEF_a.md`, `CODEX_BRIEF_b2.md`; batch b moved to b2 while a ran). Every book is 50 units long
  (`work/length_overrides.json`): the icons' sizes do not mean different books.
- **Meshy helmets and boots** (`meshy/`, project claimed as `engine:ground-items`, receipts
  `meshy/creature_3d_progress.json`, requests `meshy/requests/`): Codex HD three-quarter reference per design from
  its icon (`meshy/<design>/references_hd/`, `CODEX_BRIEF.md`; binary-alpha `00_three_quarter_meshy.png` sent), then
  Meshy image-to-3D (`ai_model` latest, PBR, remeshed to 30k triangles), 30 credits each, **180 in total**.
  `scripts/meshy_item.py` welds, drops crumbs, decimates to 2,000-3,000 triangles keeping Meshy's UVs and maps (scaled
  to 1K, copied into new images so they export as PNG for the cook) and grounds the model.
  `install_family.py meshy` installs each design of `designs.json` for its icons:

  | Design | Icon (item) | Triangles | Length |
  |---|---|---|---|
  | helm_full | item111 (Full Helm) | 2,500 | 42 |
  | helm_horned | 7item089 (Horned Helm) | 2,500 | 42 |
  | hat_peasant | 7item094 (Peasant Hat) | 2,000 | 50 |
  | boots_leather | 7item115 (Leather Boots) | 3,000 | 52 |
  | boots_knight | 7item118 (Knight's Boots) | 3,000 | 52 |
  | boots_ranger | 7item117 (Ranger Boots) | 3,000 | 52 |

  To use a design for more icons, add them to its `icons` in `designs.json` and rerun `install_family.py meshy`.
  These five Meshy-textured designs are KEEP by the user’s 2026-10-18 decision.
- **Armour** is drawn 1.3x larger (family scale), at the user's suggestion that it looked small next to shields.

### Cheaper route: Smart Topology + Codex-painted PBR (trial on the Full Helm, 2026-10-16)

At the user's request: Meshy Smart Topology without texture (**5 credits**, `requests/helm_full_st_v1.json`, 3,154
triangles, from the same reference) and textures painted by Codex. `scripts/codex_texture.py`:
1. `prep helm_full`: weld, ground, Smart UV unwrap, plain grey orthographic guide renders of that exact mesh from
   front, back, left, right and top (`codex_tex/helm_full/guide_*.png`, framing in `views.json`).
2. Codex paints each view over its guide (`codex_tex/helm_full/CODEX_BRIEF_{1,2,3}.md`, three parallel sessions,
   about 15 minutes): the design reference's materials on the guide's exact silhouette, flat shadowless light.
   The paintings matched the guides within 1-4 % (registered by silhouette box per view).
3. `bake helm_full`: each texel takes the views that see it (ray cast toward the camera), weighted (n . view)^4 by
   the painting's eroded alpha; unseen texels (the shell's inner wall) dark; gutters filled. PBR from the painting:
   metallic per design (0.85 here), roughness lower where the painting is bright, a tangent normal from its fine
   luminance detail. 1024 maps (base colour, metallic-roughness, normal). `work/codex_tex/helm_full_export.glb`.
Installed for item111 (`designs.json` route `codex`); the Meshy-textured version stays in
`work/meshy/helm_full_export.glb`. Comparison: `review/helm_meshy_vs_codex_renders.png` (Meshy texture left),
`review/helm_meshy_vs_codex_ingame.png`. The Codex paint reads as hammered dark steel with brass trim and rivets; the
Meshy texture as glossy black plastic.

## In-game checks

Test map: `saves/Ground items test.oysav` (git-ignored, local) holds every installed item model, one item per icon,
on the open plain of MM7 `out10.odm` (monsters killed), in family rows from the start southward (the `ORDER` of
`scripts/make_testmap.py`); the plain lies well inside the map's travel bounds (+-23143: the first layout, on the flat
south of Ravenshore, ran past them into the edge transition). To rebuild it (a model reinstall alone already shows in
the existing save, which stores items, not models): `python3 -I scripts/make_testmap.py`, start out10 at -4608 17700
facing south, run `exec <absolute path>/testmap/out10_all_items.cfg` in the debug console, then quick-save (F9).
`exec <file>` runs a file of console commands at once (one per line, `;` chains, `#` comments); drops this many at
once used to stall the game (each falling item's floor probe built every b-model face of the map: about 1 fps for
911 items in Ravenshore, and the long frames kept the items bouncing); `sampleOutdoorSupportFloor` now skips b-models
whose vertices do not span the point, and the same drop runs at 300-580 fps while the items settle.

Debug console: `item drop <id> [x y z]` drops a new item (it is thrown a little along the camera's yaw). Scripted
menu-input tours drop all 68 swords in a grid on the New Sorpigal beach (`oute3.odm`, from -3718.493 3245.946 1, yaw
3.359, pitch -24) and capture; the sprite comparison runs the same tour with `items.yml` moved aside. Indoors: Agar's
Laboratory (`6d19.blv`, from 1350 -3150 10 looking +Y). Captures: `review/swords_ingame_oute3.png` (sprites above,
models below), `review/swords_ingame_6d19.png`.
Later waves: `review/weapons_ingame_oute3.png` (every weapon family), `review/flat_ingame_oute3.png` (shields, armour,
cloaks, belts).

Fixed during the pilot: items on the beach sank under the drawn ground (the item sampler used the smoothed native
surface, but the terrain mesh lowers and shapes the beach after smoothing); it now reads the mesh's own heights.

Observations (2026-10-16): every sword is distinct and faithful to its icon (knuckle bows, wavy blades, coloured
grips) where the sprites showed about four shapes. Lying flat at the sprites' size they were foreshortened from the
player's eye height, read less at a distance than the upright sprites, and tall grass hid part of them. The user then
asked for both remedies: scaled up 1.25 and propped (hilt raised). `swords_ingame_oute3.png` shows sprites, flat
models and the propped, larger models top to bottom; `swords_ingame_oute3_near.png` the propped ones close up.
