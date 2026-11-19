# New Sorpigal storage behind the tavern (2026-11-19)

Two native wooden containers stand on the level grass behind the tavern's east wall.
Approach from the south through the gap in the town fence; there is room to pass the sign.

| Model | Position (native units) | Event | Chest id | Refill |
| --- | --- | --- | --- | --- |
| 90 StorageSouth | -6880, -9248, 160 | 501 | 2 | Preserved |
| 91 StorageNorth | -6880, -8992, 160 | 502 | 3 | Preserved |
| 92 StorageSign | -6880, -9536, 160 | 503 | — | — |
| Original bridge model 28 | Unchanged | 76 | 0 | Ordinary loot |
| Original bridge model 27 | Unchanged | 77 | 19 | Ordinary loot |

Storage retains ids 2/3, so inventories in existing saves appear at the new containers without
editing saves or transferring items. For new games they start empty and untrapped.
The previously unused chest definitions 0/19 now contain the original bridge loot definitions.
Existing saves acquire that ordinary bridge loot on their next normal map refill.

`oute3_storage.lua` explicitly overrides the bridge handlers and their interaction metadata,
and registers the new containers and sign. The generated EVT Lua is unchanged.
`oute3.scene.2.yml` continues to preserve only ids 2/3. All original 90 models, terrain,
decoration records and the remaining chest definitions are unchanged.

The final sign uses MM6's native `sign128` texture with unreadable painted marks, matching other
in-world signs. Its translated `Storage` hint supplies the readable name through ordinary interaction.
The earlier readable Russian sign artwork was superseded before this checkpoint.

`tools/place_sorpigal_storage.py` records the one-time installation and supports `--check`.
It requires PyYAML and Pillow. Run installation only on the original 90-model map.

## Bake and validation

Full production bake: Blender 5.3.0, CPU Cycles, existing `mm6_oute3.yml` profile, 64 samples,
315° azimuth, 45° elevation. Installed the matching `.lighting` and `.bake.json` pair.
Version 5, 93 models, 3198 face receivers, 3 direct-sun pages.
Lighting SHA-256: `943068575ef6d7940ca70919fe0059059f818117e0246592376045032d87af5c`.

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tools/lighting/bake_outdoor.py -- \
  --profile tools/lighting/baked_outdoors/profiles/mm6_oute3.yml \
  --output output/sorpigal_storage_final
```

Verified with the existing Windows executable, without a game build:

- `app_sorpigal_storage_chests_survive_refill_and_save_roundtrip`: passed.
- `--headless-open-event oute3.odm` for 76/77: ordinary loot opens in ids 0/19.
- The same check for 501/502: empty storage opens in ids 2/3; sign event 503 opens no container.
- Original map bytes checked: only three appended models, no existing geometry/entity changes.
- Stale-bake check: New Sorpigal is current. The unrelated Bracada scene dependency was resolved
  by a full production rebake at the commit checkpoint; the repository-wide check reports zero stale bakes.
- Native screenshot inspected: `output/sorpigal_storage.png`; isolated logs in `output/storage_visual/`.
  The Windows launcher terminates its owned process after capture (exit code 1 on forced termination).
  The game loaded, rendered and captured successfully before that termination.

No game or Vulkan builds were run.
