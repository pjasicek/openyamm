# Ground item WIP handoff — 2026-10-18

The 911-icon MM6–MM8 baseline has been restored from `assets_legacy/rollback_3d_20261016/items/`.
The archive is unchanged. MM9 is out of scope. This is preparation, not acceptance of every old model.

## Locations and switch

- Source GLBs: `assets_source/engine/world_items/models/item_<icon>.glb` (source-assets repository).
- Runtime: `assets_dev/engine/world_items/models/`, with local `textures/`.
- Bindings: `assets_dev/engine/world_items/items.yml`.
- Original projects/references: `level_generation/props/items_claude/`.
- Individual worker projects: `level_generation/props/items_wip_<worker>/`.
- `[rendering] item_models=true` enables 3D on the next map load; false uses sprites.
  Root development settings enable it. Code and release defaults remain false.
- Release packaging excludes the whole `world_items/` subtree, including Android texture profile checks.
- Default model cooks/verification leave engine/world_items alone; explicitly select it with `--only`
  when cooking or validating WIP. Never run global cooks concurrently with workers.

Install only a reviewed replacement, keeping its existing icon filename and binding length:

```sh
python3 tools/install_model.py <unprocessed-export.glb> --world-items --name item_<icon>.glb
```

The installer serializes writes/cooking with the existing install lock. Workers must not rewrite shared bindings.
Propose necessary length changes in each worker’s handoff.json; the coordinator applies those separately.
The old family installer now targets this subtree, but remains coordinator-only: blanket reinstalling a family can
replace accepted/generated pieces with its original rough models. The six selected generated pieces stay KEEP.

## Six workers

Recommended model: GPT-6.1 Sol, high reasoning. This is a workflow recommendation based on its coding/vision balance;
availability depends on the Codex model picker. Official model guidance: https://developers.openai.com/api/docs/models
Use the six numbered .txt files here as complete session prompts. Each project also has TASK.txt and ownership.json.
All 911 icons have exactly one owner in inventory.json. The subsequent five weapon workers are recorded there too. Workers inspect before choosing replacements; assignments
are candidate work, not an instruction to discard satisfactory models.

| Worker | Icons | Prompt |
|---|---:|---|
| Equipment | 95 | [01_equipment.txt](01_equipment.txt) |
| Potions and vessels | 42 | [02_potions.txt](02_potions.txt) |
| Gems, rings and belts | 91 | [03_jewellery.txt](03_jewellery.txt) |
| Simple props and inorganic materials | 142 | [04_props.txt](04_props.txt) |
| Organic materials and soft objects | 39 | [05_organic.txt](05_organic.txt) |
| Sculptural quest objects | 27 | [06_sculpture.txt](06_sculpture.txt) |
| Weapons: five additional sessions | 296 | [weapon handoff](../weapons_parallel_20261018/README.md) |
| KEEP / later visual review | 179 | inventory.json, owner=keep |

KEEP: armour, shields, amulets provisionally, 13 Blender books, 9 coin heaps,
and the six generated designs (Full Helm uses its Codex-painted Smart Topology version). Suitable flat letters,
keys, maps and paintings remain keep pending review. Do not follow old notes demanding a redo of the five
Meshy-textured retained designs just to change their production route.

Each worker owns its script copies, designs.json, art, receipts and listed icon models only. The main project’s
scripts/designs.json, shared engine code, settings, packaging and items.yml are coordinator-owned. Use individual
Blender processes and Meshy projects/claims. Do not fan out nested Codex sessions; there are already six workers.
For these six non-weapon sessions, no paid Meshy budget is set by this handoff. The five additional weapon sessions
have unlimited authorization under their own handoff. Prepare a concrete batch and credit total before seeking approval;
continue independent Blender/image work meanwhile. No new images or paid jobs were started by preparation.

## Review and release

Keep per-icon keep/replaced/deferred records and comparison sheets in each worker project. Validate winding,
texture references, footprint/grounding and silhouette before installing. Check representative results both
indoors and outdoors with isolated saves/settings. The original all-items save remains available:

```sh
./tools/run_game.sh --isolated world_items_review --world mm7 --save 'saves/Ground items test.oysav' \
  --set rendering.item_models=true --warmup 3 --seconds 15
```

Keep the old archived baseline until final acceptance. Promoting this feature to releases is a separate decision.
Source and runtime assets can be committed independently of unrelated work; never stage/commit automatically.

## Preparation validation

- Development game and unit-test targets built successfully (no Vulkan build).
- Focused settings/binding tests: 2 cases, 932 assertions passed.
- Release packaging and default-cook isolation regression scripts passed.
- Explicit desktop WIP verification: 911 models, 853 textures, zero problems.
- Default desktop verification: 551 non-WIP models, 1875 textures, zero problems.
- Initial inventory check: 911 icons covered exactly once; 436 assigned to six workers, 475 KEEP/review.
  After the weapon follow-up: 296 of those KEEP entries moved to five weapon workers; 179 remain KEEP/review.
- The six retained generated designs have source bytes identical to the archive.
- Installer exercised on Full Helm; invalid path-containing output names rejected.
- NVIDIA/OpenGL native captures: [outdoor 3D](review/outdoor_3d.png),
  [same save with sprites](review/outdoor_sprites.png), [indoor 3D](review/indoor_3d.png).
  No model-load errors in these runs. This is a setup smoke check, not acceptance of every icon.

No new artwork generation, Meshy spending, full release build, Android device test or git staging/commit.

Weapon-only follow-up: [five production sessions](../weapons_parallel_20261018/README.md). The six non-weapon
ownership lists are unchanged; do not take over weapons from those five sessions.
