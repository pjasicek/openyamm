# MM9 items on the ground in 3D: plan (2026-11-05)

Done (2026-11-05): every design built and installed; see [README.md](README.md) for the result. MM9 was out of scope of the
[ground item plan](../../../devdocs/GROUND_ITEMS_3D_PLAN.md); today an MM9 item lying on the ground draws the
missing-model placeholder ([behaviour](../../../devdocs/GROUND_ITEMS_3D_BEHAVIOUR.md) §2). This plan gives each MM9
design a model, following the [3D ground item playbook](../items_claude/GROUND_ITEM_3D_PLAYBOOK.md) as the 2026-10-18
item sessions, [MAW](../items_wip_maw/README.md) and [Hesper](../hesper_items_claude/README.md) actually ran it.

## How many models

391 MM9 items, **245 designs** (one per MM9 source PCX; the
[MM9 icon project](../../ui/mm9_item_icons_20261104/README.md)'s `designs.json`). Items of one design look the same, so
they share a model: scrolls are 114 items in 6 designs, books 30 in 8, keys 8 in 1. The engine binds a model by icon
(`Pic File`), and every MM9 item has an icon of its own (`mm9_item_<id>`), so the bindings are **391 lines pointing
at 245 models**. The 8 MM9 items the importer maps onto shared items (a potion, a spellbook, six scrolls) already
have MM6-MM8 models.

## Routes

Per design in [routes.tsv](routes.tsv) (`python3 -I scripts/classify.py` rebuilds it from the icon project):

| Route | Designs | Meshy | What |
|---|---:|---:|---|
| **meshy** | 87 | 435 | Meshy Smart Topology, untextured (5 credits); Codex paints the views and a material mask over grey guides; baked into PBR. Body armour 35, helms 15, boots 11, gauntlets 13, sculptural or soft misc 13 (Tree of Life, Saint's Relic, Golden Honk, Dolly, bag of herbs, basket of food, two basilisk skins, Crona Kiga, Dragon, the two slag extractors, Broken Jar) |
| **hybrid** | 28 | 140 | Weapons: Blender blade, haft, grip and shaft, plus a Smart Topology head or hilt where the shape is sculpted (maces, hammers, the cluster flails, ornate axes, three ornate sword hilts, Gungnir and two polearm heads, two staff heads, Kraftig Bage's stock) |
| **blender** | 115 | 0 | Built from components: the other 58 weapons (blades, hafts, bows, crossbows, Blackpowder), rings 12, amulets 12, belts 6, books 8 (book builder), scrolls 5 (scroll kit), bottles 3 (lathe), regular misc 11 (orbs, ores, keg, jar, runestone, plow, capstone, clover, lock of hair) |
| **plate** | 12 | 0 | Shields: the icon outline as a curved plate with real thickness, rim and boss in Blender, the face painted by Codex |
| **reuse?** | 3 | 0 | Victory Certificate (106 items), Accountant's Key (8), Jar: an existing MM6-MM8 model if it matches the MM9 icon beside it, else blender |
| **Total** | **245** | **575** | |

Precedent for the split: the weapon sessions used Meshy for 52 of 296 weapons (blunt heads, ornate axes, a few hilts
and spear heads) and Blender for the rest; the equipment, organic and sculpture sessions used Smart Topology for
helms, boots, gauntlets and sculptural objects; jewellery, belts, scrolls, letters, props, gems and herbs were redone
as Blender components (the user asked for real 3D in place of the flat icon reliefs).

## Cost and effort

- **Meshy: 575 credits** (115 Smart Topology jobs at 5), plus about one retry in ten: **ceiling 635**. The item
  sessions and Hesper ran without paid retries (Hesper 365 of 405, MAW 120). Paid generation needs the user's
  go-ahead for the batch.
- **Body armour is the one open choice.** MM6-MM8 armour is still the old icon relief, kept provisionally ("mostly
  OK"); Hesper modelled its armour in Meshy. Meshy for all 35 is 175 credits of the total; a relief keeps them at 0
  but looks flat next to real 3D helms and boots.
- **Codex image sessions, about 235**, up to 16 at once:
  - 39 new three-quarter masters for helms, boots and gauntlets, whose icon paintings are front or side views;
  - about 28 head or hilt references for the hybrids;
  - about 170 paint sessions, one per textured design (the MAW paint and mask atlas).

  Armour and misc use the icon project's HD paintings (`items/<design>/paint_a.png`) as masters.
- Weight, from the Hesper and item-session averages: about 1,800 triangles a model, about 440k in all, 20-30 MB of
  cooked GLBs with the ground-item texture caps (colour 512, normal and roughness 256).

## Where the bindings live: a world-owned file (proposal)

MM9 items are world content (`worlds/mm9/data_tables/items.txt`), so their models and bindings belong in the MM9
package, not in the engine's `world_items` (as MAW's block does). They cost nothing when MM9 is not mounted, as the
MM9 rules require. The engine reads only `engine/world_items/items.yml` today, so this needs three small changes:

1. **Engine:** `GameDataLoader` loads `worlds/<active world>/world_items/items.yml`, when it exists, after the
   engine's bindings and adds its icons. An icon bound in both is an error, so a world cannot silently replace an
   engine binding. A unit test goes beside the existing `*Item model*` cases.
2. **Installer:** `tools/install_model.py --world-items --world mm9` installs into `worlds/mm9/world_items/models/`
   (today `--world-items` means the engine folder only).
3. **Cook:** a `worlds/*/world_items/models/*.glb` class in `tools/cook/model_textures.yml` with the ground-item
   caps. Without it a world model falls under the creature class (2048 textures).

`tools/item_model_shapes.py --bindings assets_dev/worlds/mm9/world_items/items.yml` writes the bounds, as Hesper's
stage does. The alternative, an MM9 block in the engine file and models under `engine/world_items/models/`, needs no
code but puts world content in the engine package.

## Workflow

Project folder: `level_generation/props/items_mm9_claude/` (this one), with the MAW and Hesper scripts copied and
adapted (`designs.json`, master, paint brief, register, bake, review, install).

1. **Hook:** the three changes above, tested with one bound MM9 icon in an MM9 game.
2. **Pilots, one per route, for the user's review:** Dark Plate (meshy armour), Imperial Helm (meshy, new master),
   Dragon Hammer (hybrid), Imperial Sword (blender), Heater (plate), Regal Belt (blender), Golden Honk (meshy
   misc), and the Victory Certificate reuse check. 6 jobs, 30 credits.
3. **Batches by family** after the pilots are accepted. Each family gets a review sheet (icon, above, three-quarter,
   low) and a winding check before install.
4. **Install and bind:** 245 models and 391 bindings, with bounds from `item_model_shapes.py`.
5. **In-game check:** a new MM9 game, every item dropped with `item drop` (an `exec` file) on an outdoor map and in
   one dungeon. Native captures; no placeholder in the log; `*Item model*` unit tests.

## Decisions for the user

1. **Body armour:** Meshy (175 credits) or keep a flat relief like MM6-MM8 armour.
2. **Meshy budget:** 635 credits as the ceiling (575 planned plus retries), or a pilot-first approval (30 credits).
3. **Binding location:** the world-owned file (recommended; engine, installer and cook changes) or an MM9 block in
   the engine file.
