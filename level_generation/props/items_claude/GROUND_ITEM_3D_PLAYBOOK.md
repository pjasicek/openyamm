# 3D ground item playbook

**Resumed as isolated WIP (2026-10-18):** source/runtime models are under `engine/world_items/models/`,
bindings under `engine/world_items/items.yml`, excluded from releases. See [six-worker handoff](parallel_20261018/README.md)
for ownership and install rules. Keep the six existing generated helmets/boots; no automatic texture-route redo.

How to make one MM6-MM8 item (or one design shared by several items) into a real 3D model lying on the ground. The
user chose this route on 2026-10-16 after comparing it on the Full Helm with a fully Meshy-textured helmet:

**HD master image (Codex) -> Meshy Smart Topology (untextured, 5 credits) -> reduce if worth it -> Codex paints the
views -> projection bake with PBR maps -> install.**

Overview, audit and status: [GROUND_ITEMS_3D_PLAN.md](../../../GROUND_ITEMS_3D_PLAN.md). Project, families and
history: [README.md](README.md). Engine binding: `assets_dev/engine/world_items/items.yml` (by inventory icon).

## 1. Which route for which item

**Weapon override (2026-10-18):** all 296 weapons/wands are assigned to the
[five-session rebuild](weapons_parallel_20261018/README.md). Use Blender, Meshy or a hybrid to build actual
components/cross-sections, with clean UVs and appropriate PBR. The user authorized unlimited Meshy credits,
imagegen and Blender for that scope, including retries; the batch-approval/retry limits below do not apply there.
These five sessions are explicitly authorized; do not create additional nested sessions. Other item scopes keep
their existing authorization. The weapon audit supersedes the previous acceptance of icon relief for weapons.

| Item kind | Route | Why |
|---|---|---|
| Volumetric items, or icons painted at an angle: helmets, hats, crowns, boots, gauntlets, potions, rings, cloaks, sacks, most quest objects | **This playbook** | One painting cannot define the shape; reliefs of these read as paintings on guessed shapes (user review, 2026-10-16) |
| Nearly flat non-weapon items painted face-on: shields, scrolls, letters, keys, amulets, gems | Icon relief (`build_icon_relief.py`, README) | Faithful, a few hundred triangles; user accepted |
| Body armour | Icon relief for now (scaled 1.3x) | "Mostly OK" (user) |
| Gold heaps, books | Blender builders (`build_gold.py`, `build_books.py`) | Simple regular geometry; covers painted by Codex |

One design may serve several items (a helmet shape for several helmets): give it every icon in `designs.json`. A
recolour of a design is a new paint pass (step 5) on the same mesh, not a new Meshy job.

## 2. Register the design

Add an entry to `designs.json` (the registry every script reads):

```json
"helm_full": {
  "title": "Full Helm (MM6)", "icons": ["item111"], "master_icon": "item111",
  "identity": "<what the icon shows: shape, parts, colours, how it rests on the ground>",
  "materials": "<the surface materials to paint: metals, leather, cloth, trim, wear, the interior>",
  "route": "codex", "tris": 3200, "metallic": 0.85, "rough": [0.55, 0.3], "normal": 2.0, "length": 42.0
}
```

- `length`: world units of the longest horizontal side (swords are about 160 for a real 1.2 m blade, drawn 1.25x
  for readability; helmets 42, boots 52, books 50).
- `tris`: the budget after step 4. `metallic`: 0 for leather, cloth and wood, 0.8-0.9 for metal pieces.
  `rough`: roughness where the painting is dark and where it is bright. `normal`: strength of the fine detail.
- Mixed materials (leather boot with steel plates): one `metallic` does not fit; see section 8.

## 3. HD master image (Codex)

```sh
python3 -I scripts/item3d.py master <design>            # meshy/<design>/references_hd/icon_x8.png + CODEX_BRIEF.md
python3 -I scripts/item3d.py codex meshy/<design>/references_hd/CODEX_BRIEF.md
```

One three-quarter view, transparent background, from the restored x2 icon (`assets_dev/engine/icons_x2`), faithful
to its design and colours. Review it next to the icon before spending credits; at most one corrective regeneration.
Codex returns 1254 x 1254 instead of 1024 (fine). At most four Codex sessions in parallel.

## 4. Meshy Smart Topology, then reduce

```sh
P=level_generation/props/items_claude/meshy
python3 tools/creature_workspace.py claim --project $P --identity engine:ground-items --owner "<session>" --budget <n>
python3 -I level_generation/props/items_claude/scripts/item3d.py st-request <design>
./tools/run_creature_meshy.sh --project $P --token <token> submit --job <design>_st_v1 --kind image-to-3d \
  --request requests/<design>_st_v1.json --credits 5
./tools/run_creature_meshy.sh --project $P --token <token> poll --job <design>_st_v1 --wait-seconds 30   # repeat
./tools/run_creature_meshy.sh --project $P --token <token> download --job <design>_st_v1
python3 tools/creature_workspace.py release --project $P --token <token>
```

Untextured Smart Topology at a 3,000 target: **5 credits**, receipts in `meshy/creature_3d_progress.json`. Render it
plain before going on (the shape is what Meshy can get wrong; one retry costs 5 credits). Paid generation needs the
user's go-ahead for the batch; record the spend in the README.

Reduce only when it pays: Smart Topology already spends triangles where the shape needs them (the Full Helm came at
3,154 and kept all of them). Budgets: small rigid items 1,500-3,200, a pair of boots up to about 3,500; 15k is the
hard ceiling ([modelling guidelines](../../GAME_ASSET_MODELLING_GUIDELINES.md)). Set `tris` in the design and
`prep` collapse-reduces before unwrapping.

## 5. Codex paints the views

```sh
blender --background --python scripts/codex_texture.py -- prep <design>     # unwrap, guide_<view>.png, views.json
python3 -I scripts/item3d.py paint-briefs <design>                          # CODEX_BRIEF_{1,2,3}.md
for part in 1 2 3; do python3 -I scripts/item3d.py codex codex_tex/<design>/CODEX_BRIEF_$part.md & done; wait
```

`prep` renders plain grey orthographic guides of the exact mesh from front, back, left, right and top (1024, one
framing). Codex paints the design's materials over each guide, keeping its silhouette, with flat shadowless light
(an albedo source). Three parallel sessions, about 15 minutes. **Gate:** every `paint_<view>.png` shows the guide's
silhouette (the bake prints each view's registration scale; 0.95-1.05 is fine) and no shadows or hot highlights.

## 6. Bake and PBR

```sh
blender --background --python scripts/codex_texture.py -- bake <design>
```

Every texel takes the views that see it (ray cast toward each camera), weighted by how squarely it faces them and by
the painting's eroded alpha; texels no view sees (a shell's inner wall) are dark; gutters are filled. From the
painting: metallic per design, roughness from brightness, a tangent normal from its fine detail. Writes 1024 base
colour, metallic-roughness and normal maps into `work/codex_tex/<design>_export.glb`. **Gate:** render it from two
elevations next to the master (`review/`); no patches, streaks or seams on the faces players see.

## 7. Install and check in game

```sh
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py work/codex_tex/<design>_export.glb
python3 -I scripts/install_family.py meshy      # installs every design of designs.json for its icons, rewrites items.yml
```

Load `saves/Ground items test.oysav` (every item laid out on the MM7 out10 plain; README, "In-game checks") or drop
the item with `item drop <id> [x y z]`; for many, `exec <file>` runs a file of console commands at once. Check it
next to its neighbours: size, how it rests, colours under the map's light. `./build/tests/openyamm_unit_tests
--test-case='*Item model*'` checks the bindings.

## 8. Known limits and gotchas

- **Metallic is one value per design.** Mixed leather and metal needs a material mask; when that comes up, have
  Codex paint a mask view alongside each painting and extend the bake (not done yet).
- **Unseen surfaces** (overhangs no view reaches) come out dark like an interior; add a view in `VIEWS` if a visible
  part is affected.
- `codex exec -i` takes every following argument as an image: the prompt goes on stdin (`item3d.py codex` does).
- The model cook takes PNG textures only; Meshy ships JPEG (the Meshy-textured route copies them into new images).
- `tools/install_model.py` and `tools/cook_models.py` must run without `python3 -I` (the cook imports its sibling
  modules); `install_family.py` calls them that way.
- A model cook from another session at the same moment can drop fresh runtime copies; `install_family.py` reinstalls
  missing ones after its pass.
- `run_game.sh` reports "failed" when a screenshot tour exits the game before its warmup ends; the shots are saved.

## 9. Cost and weight (measured 2026-10-16)

| Route | Meshy | Triangles | Textures | Cooked texture memory |
|---|---|---|---|---|
| This playbook | 5 credits | 1,500-3,200 | base colour, metallic-roughness, normal at 1024 | about 1.7 MB per design |
| Meshy-textured (superseded) | 30 credits | 2,000-3,000 | Meshy's maps at 1024 | about 1.7 MB per design |
| Icon relief | none | median about 400 | icon-sized (64-512) | about 25 KB per item |

1024 maps are generous for an object this size; 512 is likely enough at game distance (an open check). A map loads
an item's model the first time it appears; even every one of the 911 icons at once drew in about 1.5 ms a frame.
