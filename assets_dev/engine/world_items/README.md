# Isolated ground-item models (WIP)

Restored 2026-10-18 from `assets_legacy/rollback_3d_20261016/items/` without changing the archive.
911 icon bindings; editable sources are under `assets_source/engine/world_items/models/`.
The models and `models/textures/` are cooked runtime outputs. Do not edit them directly.

Every item on the ground draws its model; an item without one draws `models/missing_item.glb`, a magenta and black
placeholder (GROUND_ITEMS_3D_BEHAVIOUR.md). Each binding carries `bounds`, the model's box at game scale: run
`python3 tools/item_model_shapes.py` after installing or replacing a model (`--check` lists stale entries). This
whole subtree is still excluded from desktop/Android release packages and default model cooks/verification.
Explicitly target WIP with `--only engine/world_items/models/<file>.glb`.

Install: `python3 tools/install_model.py <source-export.glb> --world-items --name item_<icon>.glb`.
Keep per-icon bindings stable while workers replace models. Never blanket-reinstall old relief families over new art.

Six-worker prompts and exact ownership:
`level_generation/props/items_claude/parallel_20261018/README.md`.
The source-assets repository and runtime tree are separate Git scopes; nothing was staged or committed.
