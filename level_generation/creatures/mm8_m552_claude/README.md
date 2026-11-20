# MM8 Thunderbird (m552) — 2026-10-18

> **Installed model reduced (2026-10-18):** the installed runtime is now the triangle reduction from [`../mm8_m552_reduce_claude/`](../mm8_m552_reduce_claude/README.md) (LOD0 11,448 -> 6,867). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m552_reduce_claude/work/mm8_m552_source_pre_reduce.glb`.


Rigged bird production from the shared Claude non-humanoid playbook, with Bat as the flight-quality benchmark.
Source identity is **mm8:m552**, merged descriptors **115–117**. Native monster names are **Mist Hawk**, **Storm Eagle**,
and **Thunderbird**; sprite groups m553/m554/m555 use palettes 553/554/555. No native sprites or gameplay tables changed.

## Delivery

- [Editable packed Blender master](work/m552_textured_master.blend)
- [Portable GLB](export/mm8_m552.glb), including all three shared-texture variants and color/shadow LODs
- [Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm8_m552_claude/review/viewer/)
- Runtime source: `assets_source/worlds/mm8/models/mm8_m552.glb`; cooked runtime under `assets_dev/worlds/mm8/models/`.
- Bindings: `assets_dev/worlds/mm8/models/actors.yml`, Thunderbird A/B/C.

| Item | Result |
|---|---|
| Color triangles LOD0 / 1 / 2 / 3 | 11,448 / 5,723 / 2,860 / 1,419 |
| Rig | 62 bones, maximum 3 influences after reduction |
| Maps | Shared 2K base color; 1K normal, specular/roughness/metalness, region mask |
| Materials | One draw material, opaque closed feathers, metallic zero; specular varies by anatomy |
| Meshy spend | **20 / 100 credits**: T2 5, selected T2.5 5, four-view retexture 10 |
| Artistic acceptance | Pending user review; technical review is separate |

## Reference and geometry decisions

Five original Codex HD views are preserved in `references_hd/`, with prompts, input hashes, raw-return paths and
selection decisions in `generation_runs.json`. The initial profile views were corrected before use. Native frame
and timing evidence is in `references/`; the separate `mm8_m552` sprite-restoration project was read only.

The first Smart Topology return had folded feathers and fused toes. T2.5 improved the base shape. Eight residual
folded outer primary shells were locally rebuilt to the measured outlines and thickness; fused toe loops were
replaced by three forward toes and one hallux per foot, each with its own control. The native hooked beak, short
fan tail, body plumage and paired feather wings are present. No equipment is required.

The retained animated mesh is authoritative. Meshy retexture preserves the supplied UV layout at 14,040 of 14,078
exported vertex/UV samples. Its static return drops 38 samples on tiny foot-cut and wing surfaces; all original
geometry and UVs remain in our master. The surrounding material projection was inspected on the exported model.
Head and neck UV islands received 2.5× density before packing. The measured normal convention was flipped once to
OpenGL +Y. Separate AO and a material-class map remain available for editing. MR red stores the engine specular
mask, green roughness, blue zero metalness. Reduced shadow surfaces receive a small 0.3–0.7 mm inward margin,
capped at 1 mm to protect the thin feathers.

Native brown and olive color populations drive two shared region ramps. Unchanged native colors must be included:
the first changed-only fit incorrectly recolored body browns. Final albedo reference gains are 1.45 for body and
1.10 for olive feathers, with the finest texture noise reduced. Eyes, beak and talons are protected from tier ramps.
The beak tip retains the native warm red accent. Browser tiers bake the same ramps for review only; runtime tiers
share all four images.

## Motion and size

| Clip | Seconds | Use |
|---|---:|---|
| Fly | 1.0 | Idle, movement, running and fidget; native eight-frame flight rhythm |
| Attack | 1.208333 | Chest-up strike, talons forward at 0.875 s |
| Cast | 1.208333 | Separate head/body casting motion, release at 0.875 s |
| Hit | 0.75 | Recoil within the native timing |
| Death | 0.625 | Fold wings during the roll, then settle onto the back |
| Dead | 1.0 | Held feet-up corpse, matching Death endpoint |

Motion is procedural and informed by native poses, not an exact reconstruction. Bird-specific shoulder/elbow
motion, return-stroke folding and feather lag replace the bat membrane motion. The death roll folds before rolling
so spread wingtips cannot vault the torso upward; subframe translation clearance prevents between-key floor dips.
The final corpse rests on its body. `HeadSocket` supplies Lightning Bolt glow and release; all three native tiers cast.

Scale **569.03138** comes from mean front silhouette area across all eight native and model flight poses, including
the native frame scale **2.199997**. B/C use A as scale reference. No extra hover translation is added. The flight
upstroke reaches **178.48 game units**, below the native 200-unit collision height. Wings still span beyond the
native cylindrical collision volume: very low flight and close walls can intersect wing tips, as with the existing
flyer workflow. This asset does not add terrain/ceiling avoidance or change native movement.

## Verification

- Original hashes: all 125 sprite frames and three palettes unchanged (`review/native_integrity.json`).
- Final geometry, UVs, materials, weights, all clips and three shared variants pass `review/static_audit.json`.
- Winding: no inverted closed parts. Final 1/8-frame contact sweep and loop/corpse checks are in
  `review/final_deformation_audit.json`; export reimport difference is below **0.009 mm** at sampled poses.
- Browser checks load all 18 tier/clip combinations. Normal and quarter-speed playback is exercised with sampled
  images inspected; see `review/final_playback/`. Head, paired talons and wing views are in `review/details/`.
- Ordinary desktop build passed; no Vulkan build. The Thunderbird binding regression passes with all tiers,
  native flight/simulation state, six clips, fitted wing controls and head release socket.
- Broader MM8 run: **22 passed, 1 failed**, Cyclops presentation. MM6 demon run: **4 passed, 1 failed**, the
  variants/shared-asset count assertion. These families were not changed by this task; logs are retained.
- Native desktop evidence is under `review/ingame/`, with exact cameras, launch records, NVIDIA/Wayland logs and
  isolated copied fixtures. Android was not built or tested.

### Desktop captures

| Location | Final model | Native sprites |
|---|---|---|
| New Sorpigal | [Three tiers](review/ingame/out_3d/tiers.png) | [Same camera](review/ingame/out_sprite/tiers.png) |
| Agar’s Laboratory | [Three tiers](review/ingame/in_3d/tiers.png) | [Same camera](review/ingame/in_sprite/tiers.png) |

[Lightning Bolt and talon strike](review/ingame/combat/lightning.png) ·
[Grounded death](review/ingame/combat/death.png) · [Loot transition](review/ingame/combat/dead.png) ·
[Forced LOD3](review/ingame/out_lod3/tiers.png).

Both comparison runs use the same cameras and spawn positions; ordinary AI remains live, so exact poses and
orientation differ. The indoor quarter-cycle captures check the full wingbeat. Combat retains ordinary hostile AI;
a console-triggered native spell additionally guarantees a Lightning Bolt release sample. The final fixture was
refreshed for a concurrent ground-item installation, and the ordinary review binary was pinned to prevent another
build replacing it mid-run. Exact binary hashes and requested settings are in each `run.json`.

## Rebuild

Claim this creature through `tools/creature_workspace.py`, retaining its canonical state and lease token. Under that
guard, run `scripts/compose_thunderbird.py` for texture composition. `scripts/build_runtime.sh TOKEN [--install]`
exports the selected `work/uv_master.blend`, applies the material contract, prepares the GLB, checks export parity,
builds LODs, applies shadow correction and native ramps, audits the result and refreshes the viewer tiers.
Motion-only edits use `scripts/animate_thunderbird.py --full --uv` through `tools/run_creature_blender.sh`, preserving
the selected UV layout. Run `scripts/final_deformation_audit.py --uv` before exporting changed motion.
