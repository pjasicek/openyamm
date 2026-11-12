# MM8 Unicorn — m544

> **Installed model reduced (2026-10-18):** the installed runtime is now the triangle reduction from [`../mm8_m544_reduce_claude/`](../mm8_m544_reduce_claude/README.md) (LOD0 11,513 -> 6,906). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m544_reduce_claude/work/mm8_m544_source_pre_reduce.glb`.


Selected production: `export/mm8_m544.glb` and editable `unicorn_master.blend`.
Native descriptors 109–111 (Unicorn A/B/C; Foal, Unicorn, Herd Leader) share palette 544 and the same body.
Their native standing scales are 1.199997, 1.399994 and 1.699997. The original sprites remain unchanged.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m544_claude/review/viewer/) includes
frame stepping, normal/slow playback, native action sheets and exact-frame feedback.
The viewer frames the shared model; tier size differences are exercised in native game captures.

## Production

- Five approved-by-agent HD views, with prompts/input/output hashes in `references_hd/generation_runs.json`.
- Meshy Smart Topology and original-UV multiview retexture: **15 credits** total; receipts and originals retained.
- 11,513 body triangles; colour and shadow LODs 5,752 / 2,872 / 1,432 triangles; four-triangle breath effect.
- Fitted equine rig: 27 deform bones plus horn-release and breath bones; at most four influences per vertex.
  Heat weighting failed on source and voxel proxy, so explicit anatomical weights were used and the upper joints
  smoothed after playback review. Hooves and skull/horn remain rigid.
- Shared 2K coat, 1K normal/material/region maps. Silver dapples, dark mane, tail, horn and hooves match native art.
  The renderer's specular mask occupies the red material channel. Separate baked AO is retained as an authoring map.
- Neutral geometry and UVs survive retexturing; one missing tail-tip chart (0.00975% of surface area) was filled
  from neighbouring tail pixels. Rejected decimation and superseded previews remain in `work/` for provenance.

## Motion and binding

Nine clips at 48 fps: Standing 2 s, Walking 1 s, Running 0.75 s, Attack/Cast 1.5 s, Hit/Fidget 0.625 s,
Death 0.75 s and Dead 1 s. The native walk is a gallop, so both movement clips use a transverse gallop with
0.64 m stride, staggered hind/front contacts and an airborne phase. Rear motion keeps both hind hooves planted;
forelegs fold and recover. Attack release is 1.125 s. The engine retains native combat timing and recovery.
The source family has elemental ranged attacks; the runtime charges at `HornTip` and releases at the horn base (a local offset of `[0, -0.103, -0.05]`).
The offset keeps the largest tier inside the engine's unchanged native projectile-origin envelope. Fidget exhales
through the separate translucent breath mesh. Death ends in the exact Dead pose.

Scale A is `148 native alpha pixels × 1.199997 / 0.6466717534 m = 274.636328358`.
B/C use `scale_reference: Unicorn A` to follow the native sprite-size ratios. All tiers use skin `unicorn`.
Bindings live in `assets_dev/worlds/mm8/models/actors.yml`. The installer owns
`assets_source/worlds/mm8/models/mm8_m544.glb`, its cooked runtime GLB and external textures under `assets_dev`.

## Rebuild and evidence

Claim this creature with `tools/creature_workspace.py`, then from the repository root run:

```sh
level_generation/creatures/mm8_m544_claude/scripts/build_runtime.sh "$CREATURE_3D_TOKEN" --install
```

This rebuilds from the retained UV master and maps; it submits no generation jobs. `rig_unicorn.py`,
`animate_unicorn.py` and `reduce_uv.py` retain the earlier geometry/rig/UV construction. Do not regenerate UVs
without redoing map transfer. `prepare_native_fixture.py` prepares isolated native comparisons without changing
production maps. Runtime screenshots, reports and selected hashes are recorded in `creature_3d_progress.json`.

`work/dense_motion_checks.json` checks half-frame poses, floor contact and planted-hoof travel (including the rear).
`work/export_parity.json` compares the delivered GLB with the master at nine samples per clip.
`review/static_audit.json` verifies triangles, materials, skinning, clips and the unchanged 160 native BMPs/palette.
`review/playback/` records all nine clips at normal and half speed. Native indoor/outdoor comparisons and combat
captures live in `review/ingame/`.

Technical/agent review and user artistic acceptance are tracked separately; user artistic acceptance is pending.
Android and Vulkan were not run for this asset task.

## Final verification — 2026-10-18

- Unicorn regression passes both an isolated family manifest and the full production MM8 manifest.
- All 27 tier/clip viewer selections pass; all nine clips recorded/reviewed at 1× and ½×.
- GLB/master surface difference is at most 0.031 mm. Half-frame planted drift is at most 0.071 mm in gallop
  and 0.005 mm at the rear's hind supports. Worst sampled floor penetration is 0.736 mm during collapse.
- Both native/model comparisons use the prescribed camera positions in MM6 `oute3` and `6d19`.
  Spawn distances were widened to fit this long creature; close comparisons are also retained.
  These explicit fixtures contain only the Unicorn model bindings and preload the foreign native sprites.
- NVIDIA desktop captures confirm tier size, material response, contacts, horn charge/projectile, death and the
  normal loot transition. Each capture folder contains its exact binary hash, settings and game log.
- The broader MM8 actor run recorded **15 passes / 17 failures**. Unicorn passed; unrelated Triton, Dragon and
  Cyclops binding/state checks failed, and later cases encountered a missing cooked texture during concurrent
  asset changes. See `review/mm8_regression.log`. MM6 smoke was **4 passes / 1 failure** in the existing Demon
  tier/standing-sprite scale lookup check. These results are not a clean whole-game regression claim.
- Shared concurrent rebuilds temporarily removed the executable and collided during archive creation. Native
  captures used retained ordinary desktop binaries; the focused/full production checks use the final recorded
  binary. The missing `AssetPackIndex.cpp` source entry was added to `engine/CMakeLists.txt` to unblock linking.

Installed file/texture hashes are in `review/installed.json`. Technical production is complete; artistic
acceptance remains with the user. No commit or staging operation was performed.

## Anim fix (2026-11-11, MM6–MM8 audit)

Hit amplified x4 on neck, head and tail (it read as Standing); Cast stays the Attack (native attack2 = attack).
Details: [mm8_m544_animfix_claude](../mm8_m544_animfix_claude/README.md).
