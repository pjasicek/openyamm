# Weapons: five production sessions — 2026-10-18

The user requested five sessions to improve all **296 weapon/wand models**, with **unlimited Meshy credits**,
imagegen and Blender authorized. This handoff prepares those sessions; no new generation has started here.
The existing six non-weapon sessions keep their assignments. These five are additional and have no overlapping icons.

## Session prompts

Paste each complete .txt prompt into a separate Codex session in this checkout. The existing recommended
GPT-6.1 Sol/high setup is suitable; choosing a different capable model does not change the asset requirements.

| Session | Scope | Icons | Prompt | Workspace |
|---|---|---:|---|---|
| 1 | Swords | 68 | [01_swords.txt](01_swords.txt) | `level_generation/props/weapons_wip_swords/` |
| 2 | Daggers (31), axes (38) | 69 | [02_daggers_axes.txt](02_daggers_axes.txt) | `level_generation/props/weapons_wip_daggers_axes/` |
| 3 | Spears/polearms (45), staves (15) | 60 | [03_polearms_staves.txt](03_polearms_staves.txt) | `level_generation/props/weapons_wip_polearms_staves/` |
| 4 | Maces, hammers, clubs, flails | 43 | [04_blunt.txt](04_blunt.txt) | `level_generation/props/weapons_wip_blunt/` |
| 5 | Bows/crossbows (36), blasters (5), wands (15) | 56 | [05_ranged_magic.txt](05_ranged_magic.txt) | `level_generation/props/weapons_wip_ranged_magic/` |

Each workspace has TASK.txt, exact ownership.json (item IDs, names, icon reference, current binding and audit),
filtered family manifests, an empty designs.json, a separate Meshy directory, and copies of the existing reference,
paint/bake and review helpers to adapt. The copied bake is a starting point, not acceptance of its material limits.
The old whole-family installer and flawed relief generator were deliberately not copied.

`inventory.json` covers all 296 exactly once. Master ownership in `../parallel_20261018/inventory.json` now assigns
these weapons to the five new workers: 436 non-weapon assignments + 296 weapon assignments + 179 KEEP/review = 911.
Always use icon ownership rather than name/type guesses; e.g. axes-family poleaxes belong to session 2,
while spear-family halberds belong to session 3. Do not move work between sessions without coordination.

## Authorization

The exact authorization is recorded in authorization.json and every prompt. Unlimited Meshy spending and required
retries are approved for this weapon scope. Do not repeat the earlier per-batch approval request. Old limits such
as one corrective generation or a default 100-credit tool allowance do not supersede the user's instruction.
The wrapper requires a positive integer ledger ceiling; workers may set/extend that operational ceiling under
this authorization. Keep receipts and avoid duplicate submissions. No need to use Meshy when Blender suffices.
This is not a new spending grant for unrelated work or the six non-weapon assignments.

## Required outcome

The [audit](../review/weapon_audit_20261018/FINDINGS.txt) found icon-based reliefs, all-dielectric materials,
painted lighting and zero-thickness patches. The Iron Two-Handed Sword has 52% flat triangle area;
the Warhammer has 59%. Merely raising thickness/subdivision, adding a normal map or tilting the whole mesh is not
an adequate repair. Preserve the design, not those construction defects.

Choose the route per design: Blender for precise regular components; Meshy Smart Topology, textured Meshy, or a
hybrid for complex/sculptural forms; imagegen for HD references and clean texture artwork/material masks.
Reuse geometry for genuine variants, not for unrelated items. Cost is not a reason to accept weak results.
Triangle and texture budgets still follow game visibility/performance and GAME_ASSET_MODELLING_GUIDELINES.md.

Each session first proves its approach on representative pilots, self-reviews, then continues through its entire
assignment without stopping for another approval. Every design needs sensible cross-sections, material separation,
clean UVs/normals, plausible ground contact and review from above and low angles. Validate representative designs
from each construction/material type both indoors and outdoors; metal needs particular care in dim interiors.
Do not trade the old flattened look for inflated blades, generic shapes, excess geometry or unsupported effects.

## Shared workspace and installation

Workers own their own project and only their listed icon models. Keep shared engine code, settings, data tables,
installer/cooker, the original project's scripts/designs.json, and runtime items.yml coordinator-owned.
Use separate Blender processes and Meshy project identities. Do not create further nested Codex sessions.
Preserve the old model until its reviewed replacement is ready. Never stage or commit automatically.

```sh
python3 tools/install_model.py <unprocessed-export.glb> --world-items --name item_<icon>.glb
python3 tools/cook_models.py --verify --profile desktop --only engine/world_items/models/item_<icon>.glb
```

The existing installer locks and cooks each selected model. No concurrent full builds/cooks or whole-family
reinstalls. Source models stay in `assets_source/engine/world_items/models/`, runtime models/textures in
`assets_dev/engine/world_items/models/`. Binding length is recorded in ownership.json; proposed changes go into the
worker's handoff.json for the coordinator instead of overwriting shared items.yml. Releases remain on sprites and
exclude world_items; no release promotion is part of these prompts.

Record resumable per-icon status, route/design groups, exports, triangle/texture counts, credit receipts, reviews,
installed result and unresolved issues. A pilot or a partial batch is not completion. Do not silently accept an
unreviewed baseline just because earlier documents said KEEP.

## Preparation checks

- Exactly five prompts and five workspaces.
- 296 unique icons, equal to all nine weapon/wand manifests and the full geometry audit.
- No overlap with the six existing non-weapon worker ownership lists.
- All current source/runtime models and icon references exist; current binding lengths are captured.
- No asset, renderer, release setting, Meshy lease or job was changed by this planning handoff.
