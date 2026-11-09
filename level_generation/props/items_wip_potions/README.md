# Potions and vessels WIP — 2026-10-18

Inspected every assigned icon: **41 rebuilt and installed, 1 kept, 0 deferred**. This is a development art handoff for review, not release promotion. The nine quest-vessel size corrections in [handoff.json](handoff.json) are applied. Other binding entries were preserved byte for byte. [Before/after sizes](review/quest_scale_comparison.jpg).

[MM6 / plain potions](review/contact_01.png) · [decorated potions](review/contact_02.png) · [quest vessels / scroll](review/contact_03.png). Each cell shows the source icon, old low view, new above and new low view. [All source icons](references/assigned_icons.png).

Native captures: [MM6 filled](review/native_outdoor/01-mm6_filled.png), [MM6 empty](review/native_outdoor/02-mm6_empty.png), [plain MM7/8](review/native_outdoor/03-mm78_plain.png), [ornate MM7/8](review/native_outdoor/04-mm78_ornate.png), [MM7/8 empty](review/native_outdoor/05-mm78_empty.png), [quest left](review/native_outdoor/06-quest_left.png), [quest right](review/native_outdoor/07-quest_right.png). Indoors: [all](review/native_indoor/01-all_low.png), [near](review/native_indoor/02-near_low.png), [quest](review/native_indoor/03-quest_low.png). Run records and logs live in `receipts/`.

Blender profiles supply the volume, separate fittings, cradles, bands, loop stoppers, corks and handles. MM6 and MM7/8 bottles reuse their respective shape; the short Gog phial has separate proportions. The quest vessels retain their distinct silhouettes. Empty vessels omit the contents. The urn has a real open mouth and inner wall. Specimen anatomy is simplified into tissue lobes and coils.

One built-in imagegen material-atlas request supplied unlit artwork; the exact prompt and saved output are in [its receipt](receipts/imagegen_atlas.json). `prepare_atlas.py` makes padded PNG base colour, binary metal/roughness masks and shallow OpenGL normals. Metal, cork, soil, enamel and liquid are assigned through UV tiles. Thin bands and rods use arc-length UVs. Glass uses supported alpha blending without refraction; filled bottles have smoked glass necks, while empty vessels use stronger glass. Metal remains metallic 1 and can look dark in dim rooms.

Each GLB has one opaque painted mesh and, where needed, a separate glass mesh. All source images are embedded PNGs; desktop cooking deduplicates their textures. Geometry is centered on its footprint, lowest point zero, longest footprint direction Blender Y / glTF Z. Triangle counts are 520–2480. No LODs are needed at these counts.

Checks: every export has finite positions, normals and UVs, outward closed-part winding (glass included), no zero-area triangles, padded 0–1 UVs, centered grounding and valid embedded textures. All 41 exact-scope desktop cooked checks pass. Android textures are cooked and verified for all 42 assigned models, including the retained scroll (4 unique ETC2/EAC payloads); see [Android verification](receipts/android_verified.json) and [payload metadata](receipts/android_payloads.tsv). The retained scroll source is byte-identical to the baseline. Native checks use the existing coordinator build and isolated settings/saves. The corrected sizes were rechecked indoors and outdoors; binding tests passed 2 cases / 932 assertions, and the WIP cook-isolation and release-exclusion regressions passed. Authoring, baseline copies, GLBs, blends, guides, ledgers and receipts stay in this project. The only shared content change is nine owned lengths in `assets_dev/engine/world_items/items.yml`; shared scripts, tables, engine, settings and package rules were left alone.

Reproduce from repository root, sequentially:

```sh
python3 level_generation/props/items_wip_potions/scripts/prepare_atlas.py
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_potions/scripts/build_potions.py -- --render
python3 level_generation/props/items_wip_potions/scripts/check_assets.py
python3 level_generation/props/items_wip_potions/scripts/review_sheet.py
python3 level_generation/props/items_wip_potions/scripts/install_owned.py
```

Installation only accepts owned entries whose export hashes match validation and whose existing sources match the baseline or this worker's prior installation receipt. It invokes `tools/install_model.py --world-items` separately for each icon and uses the shared install lock.

No Meshy spend, global build/cook, Vulkan, Android device test, release promotion, lighting bake, staging or commits. Android validation covers cooked asset payloads; hardware/emulator rendering remains untested. No Android device was connected, and stock release packages exclude these WIP assets. This directory remains covered by the existing `/level_generation/` git-ignore rule.

## Per-icon ledger

Full machine-readable details: [ledger.json](ledger.json).

| Icon | Decision | Triangles | Inspected design |
|---|---|---:|---|
| bottle22 | replaced | 1548 | MM6 cradle bottles; black; separate stopper, supports and glass |
| bottle23 | replaced | 1548 | MM6 cradle bottles; blue; separate stopper, supports and glass |
| bottle24 | replaced | 1548 | MM6 cradle bottles; green; separate stopper, supports and glass |
| bottle25 | replaced | 1548 | MM6 cradle bottles; amber; separate stopper, supports and glass |
| bottle26 | replaced | 1548 | MM6 cradle bottles; red; separate stopper, supports and glass |
| bottle27 | replaced | 1548 | MM6 cradle bottles; ivory; separate stopper, supports and glass |
| bottle28 | replaced | 1548 | MM6 cradle bottles; yellow; separate stopper, supports and glass |
| bottle29 | replaced | 1548 | MM6 cradle bottles; violet; separate stopper, supports and glass |
| bottle30 | replaced | 1220 | MM6 cradle bottles; empty; separate stopper, supports and glass |
| item177 | replaced | 2124 | MM7/8 banded flasks; blue; separate stopper, supports and glass |
| item178 | replaced | 2124 | MM7/8 banded flasks; red; separate stopper, supports and glass |
| item179 | replaced | 2124 | MM7/8 banded flasks; yellow; separate stopper, supports and glass |
| item180 | replaced | 2124 | MM7/8 banded flasks; ivory; separate stopper, supports and glass |
| item181 | replaced | 2124 | MM7/8 banded flasks; grey; separate stopper, supports and glass |
| item182 | replaced | 2124 | MM7/8 banded flasks; black; separate stopper, supports and glass |
| item183 | replaced | 2124 | MM7/8 banded flasks; violet; separate stopper, supports and glass |
| item184 | replaced | 2124 | MM7/8 banded flasks; green; separate stopper, supports and glass |
| item185 | replaced | 2124 | MM7/8 banded flasks; amber; separate stopper, supports and glass |
| item186 | replaced | 2124 | MM7/8 banded flasks; red/gold; separate stopper, supports and glass |
| item187 | replaced | 2124 | MM7/8 banded flasks; red/violet; separate stopper, supports and glass |
| item188 | replaced | 2124 | MM7/8 banded flasks; green/red; separate stopper, supports and glass |
| item189 | replaced | 2124 | MM7/8 banded flasks; blue/gold; separate stopper, supports and glass |
| item190 | replaced | 2124 | MM7/8 banded flasks; violet/gold; separate stopper, supports and glass |
| item191 | replaced | 2124 | MM7/8 banded flasks; green/blue; separate stopper, supports and glass |
| item192 | replaced | 2124 | MM7/8 banded flasks; amber/gold; separate stopper, supports and glass |
| item193 | replaced | 2124 | MM7/8 banded flasks; magenta/gold; separate stopper, supports and glass |
| item194 | replaced | 2124 | MM7/8 banded flasks; green/gold; separate stopper, supports and glass |
| item195 | replaced | 2124 | MM7/8 banded flasks; red/magenta; separate stopper, supports and glass |
| item196 | replaced | 2124 | MM7/8 banded flasks; violet/green; separate stopper, supports and glass |
| item197 | replaced | 2124 | MM7/8 banded flasks; green/amber; separate stopper, supports and glass |
| item198 | replaced | 1796 | MM7/8 banded flasks; empty; separate stopper, supports and glass |
| 7item145 | replaced | 1712 | Long-neck red phial; gold rings and foot |
| 7item155 | replaced | 1704 | Double-bulb metal vessel; cage ribs and cork |
| 7item157 | replaced | 1892 | Round pewter vial; crossed copper braces |
| 7item259 | replaced | 2480 | Clear lidded jar; preserved purple tissue and coils |
| item162 | replaced | 2124 | Short banded red phial; its own profile proportions |
| 7item273 | replaced | 1480 | Elongated peacock enamel elixir; silver cage and faceted stopper |
| 7item294 | replaced | 520 | Empty clear lidded jar; no tissue or liquid core |
| item278 | replaced | 1232 | Corked clear flask; granular earth fill |
| item280 | replaced | 1520 | Corked green-blue herbal flask; gold shoulder trim |
| item294 | replaced | 1764 | Open bronze urn; swept handles, lip and inner wall |
| 7item182 | keep | — | KEEP: tied scroll reused by many letters and recipes; existing relief is appropriate |
