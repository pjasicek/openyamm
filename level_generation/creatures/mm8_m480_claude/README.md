# MM8 Troll peasant — m480

Complete and installed: three native tiers, eight animation roles, separate bone club, colour/shadow LODs,
editable Blender master and portable GLB. Canonical technical status and hashes are in
[creature_3d_progress.json](creature_3d_progress.json). User accepted this version: “ok good enough”.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m480_claude/review/viewer/)
uses the existing repository server. [Recorded playback](review/playback/playback.json) covers all eight roles
at normal and half speed. Viewer/portable colours are baked from the same native palette ramps used by the game.

The exact descriptors are **Troll Pesant A/B/C (61–63)**, with m481/m482/m483 aliases. The unrelated Treant
records mentioning m480 are not bound. Native brown/olive skin, green/grey/red wraps, brown/grey/black crests
and grey/blue/gold mottled backs share one geometry/animation asset.

## Selected delivery

| Asset | Location |
| --- | --- |
| Editable, packed, 60 fps master | [export/mm8_m480.blend](export/mm8_m480.blend) |
| Portable standard glTF, tier A with club | [export/mm8_m480_portable.glb](export/mm8_m480_portable.glb) |
| Runtime body / bone attachment | `export/mm8_m480.glb`, `export/mm8_m480_club.glb` |
| Runtime binding | [export/actor_binding.yml](export/actor_binding.yml) |
| Maps, native masks and tier ramps | `textures/` |
| Installed sources | `assets_source/worlds/mm8/models/mm8_m480{,_club}.glb` |
| Cooked runtime and bindings | `assets_dev/worlds/mm8/models/` |
| Original observations and HD references | `references_native/`, `references_hd/`, `ANIMATION_STUDY.md` |

Body triangles: **9,744 / 4,869 / 2,424 / 1,205**. Club: **1,668 / 834 / 416 / 208**.
LOD0 totals 11,412 triangles, under the 15,000 silhouette budget. There are 52 fitted body bones plus a dedicated
Club child of the right hand, at most four normalized influences, one merged body primitive per LOD and three
palette variants. Runtime shadow meshes receive the existing bounded inward correction.

## Fit and movement

The human source frames were fitted to the troll's rounded belly, stooped neck, long arms, large hands,
three fingers plus thumb, and three toes. Height-normalized upper arms are 1.47x and hands 1.44x the source;
the neck/head span is 2.03x. Mesh-measured finger contact follows the irregular meat-covered bone grip.
The resting free arm is carried outward; the run needs a stronger outward correction to clear the upper belly.

| Role | Duration | Adaptation |
| --- | ---: | --- |
| Standing | 2.000 s | Subtle heavy-body idle, held club |
| Walking | 0.800 s | Long arms, grounded feet, native-speed stride calibration |
| Running | 0.833 s | Stored Mixamo run, corrected loop and free-hand belly clearance |
| Attack | 1.733 s | Source-speed cut; maximum club reach at the native 1.000 s impact |
| Hit | 0.600 s | Fits the native 0.625 s window |
| Death | 1.433 s | Backward fall with smooth arm transition |
| Dead | 1.000 s | Held Death endpoint |
| Fidget | 1.333 s | Brings meat across the mouth |

These are fitted 3D motions, not exact reconstructions of every sprite frame. Native peasant Wimp fleeing is
preserved. The melee test uses an explicitly isolated aggressive fixture, leaving production gameplay data intact.
The engine's existing corpse dissolve/loot presentation follows the brief resting pose.

## Verification and limits

- All eight reduced-mesh clips pass a 120 Hz limb/club contact screen with a 2 mm threshold.
  The final run correction fixes the left claw entering the upper belly; the check now fails on any finding.
- Standing/walk/run endpoint surface errors are below 0.06 mm; Death and Dead agree exactly.
  Source-relative angular continuity has no flags. Export parity is within 0.021 mm.
- The upper wrap intentionally extends under the belly; its visible hem stays clear. Maximum cloth stretch is
  1.83x. The source-speed attack has local arm p99 stretch up to 2.12x; close views and playback frames were reviewed.
- All 24 tier/clip combinations load without browser errors. Six sampled frames per recorded clip/speed and
  targeted head, hand, attack, fall and running close views were visually inspected alongside dense motion checks.
- Native OpenGL/NVIDIA indoor/outdoor captures compare all tiers with original sprites. Forced LOD1–3, native
  fleeing, isolated melee/hit/fall and corpse presentation were checked. These are visual checks, not performance tests.
- Ordinary `openyamm` build passed. The focused Troll peasant regression passes after final installation;
  the MM6 goblin baseline passes. The broader MM8 actor suite reports **48 passed, 2 failed**: unrelated Cleric
  Attack clip/timing and incomplete Dragon Turtle tiers. See `review/ingame/actors_*.log`.
- Original 160 BMP frames, three palettes, original Troll descriptor fields, gameplay table and original indoor scene are
  unchanged. The shared descriptor file's overall hash changed during concurrent workspace work; four appended schema fields leave the original 19 Troll descriptor fields unchanged.

The pre-correction native lineup/combat/LOD captures remain valid for unchanged geometry, materials and seven
unchanged clips. `review/ingame/running_final/` and refreshed viewer playback cover the delivered running correction.
`review/ingame/run_records/` retains launch settings, logs and exact camera/run records.

## Reproduce

Use a claimed workspace lease and `tools/run_creature_blender.sh`; production steps live in `scripts/`.
`repair_running_contact.py` rebuilds authored motion from retained local sources, then checks the selected reduced
textured mesh. It preserves the corrected geometry and maps. The 60 Hz polish requires fresh 30 Hz authored input.

Export order: `export_runtime.py` → `tools/prepare_actor_glb.py` → `build_lods.py` →
`postprocess_runtime.py` → `verify_runtime.py` → `export_parity.py` → `viewer_tiers.py`.
Install body and club with `tools/install_model.py --world mm8`; retain the existing three binding entries.
Use `tools/run_creature_review.py` for viewer checks, close views and actual normal/half-speed recordings.

Five completed Meshy jobs consumed **45 / 100 credits**. Original service returns and generation receipts are retained.
No additional animation purchase, engine behaviour change, Vulkan build or commit was made for this creature.

## Texture quality pass (2026-10-31)

[mm8_m480_texpass_claude](../mm8_m480_texpass_claude/README.md) gives the body new UVs (`claude_shared/uv_atlas.py`)
and repaints it: Meshy 4K body and head retextures on that layout, **20 credits**. The 2080×1024 body | head atlas
(18.9 % used, 0.40 M texels, 748 islands, 9.4 % fragments) becomes one 2048² atlas: 56.4 % used, 2.36 M texels,
238 islands, 1.9 % fragments, stretch p90 1.91 → 1.17. The head is ×1.8 and the hands ×1.3. Colours are tone-matched
to the approved look, so every tier's ramps hold.

Mesh, rig, clips, materials, variants and bindings are unchanged; the shared MM7 copy `mm7_m461` gets the same maps.
Not installed yet: it waits for the gait rollout's h20/h10 reinstall, then that project's `scripts/merge_install.sh`.
