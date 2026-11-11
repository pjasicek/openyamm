# MM9 melee-contact blood effects

Investigated 2026-09-22. **Yes: the native melee-contact path can spawn a blood flash and a
spray of blood particles at the collision point.** This is a hardcoded client effect, not
a named recipe in `SPELLS.fxf`.

This is static binary evidence from the supplied installation, not a live capture of a
party attack. It does not establish that every creature, successful damage roll, or
configuration produces blood. No original binaries or OpenYAMM runtime code were changed.

## Inputs and reproduction

Source root:

```
/run/media/pjasicek/bf1d5926-921e-46b1-a33a-ea3a7b79927d/home/pjasicek/github/OpenMM9/reference
```

| File relative to source root | SHA-256 |
| --- | --- |
| `game/data/cshell.dll` | `678700ff1cc795aeee49fe8427a42e1686d5a20dfdc1617eb46a8ef19f82f7ae` |
| `game/data/object.lto` | `b1271f37e5314281035efe6425dd59051bb8a9b0271de0d75a5926a7bc37f162` |
| `extracted/SPRITES/SPRITES/BLOODHIT1.spr` | `82eac7958928b52124fc81c58a6c403a38cd43bac6ab5d2ad600e04ecf130467` |
| `extracted/SPRITES/SPRITES/BLOODSPRAY1.spr` | `976aee27ec9ebd229b71796c5a7ddec0a3e6fa300c4e23bcc642dad9a64e770f` |
| `extracted/SPRITETEXTURES/SPRITETEXTURES/BLOODHIT1.dtx` | `b3e954b4645c16b7c778bd69694e105b70a1801776078700a7edbd6240200557` |
| `extracted/SPRITETEXTURES/SPRITETEXTURES/BLOODSPRAY1.dtx` | `ff7c3616d41fdbb8c219b05651a46d83b5679e8d36df5fb3976b71226b2d536e` |

Local `mm9/extracted/` copies of the four assets match the external source hashes.
The supplied revision is fingerprinted, not authenticated against retail media.
Runtime patches/settings were not inspected in a running original game.

All addresses below are preferred virtual addresses in the named module, base `0x10000000`.
Rizin disassembly is authoritative; existing RetDec exports were navigation aids only.
Research labels are not recovered C++ symbol names.

Load the accompanying `cshell_678700ff_melee_hits.rz` or
`object_b1271f37_melee_hits.rz` only after checking its module hash. From the repository root,
with `MM9_REFERENCE` set to the source root above:

```bash
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -i re_mm8/mm9_vfx/cshell_678700ff_melee_hits.rz \
  "$MM9_REFERENCE/game/data/cshell.dll"
```

Use `aF @ 0x1006fec0` followed by `pdf @ 0x1006fec0`, for example. Nonrecursive function
analysis helps with virtual functions missed by automatic analysis. The earlier project's
large inferred function boundaries and compressed-switch case labels can be misleading.

## Verified call chain

| Stage | Module and VA | Evidence |
| --- | --- | --- |
| Native class | object `0x101a2910` | Descriptor names `MeleeWeapon`; creator `0x10059a00` calls constructor `0x100578c0`. |
| Melee dispatch | object `0x1016f5ac` | Constructor installs this vtable; slot `+0x244` points to `0x10057900`. |
| Collision query | object `0x10057900` | Calls `0x10059b70`, then contact handler `0x10057c10`; the alternate nearby-target path also performs an intersection query. |
| Contact data | object `0x10059b70` | Segment-intersection result contains position at `+0`, normal at `+0x0c`, object at `+0x1c`, polygon at `+0x20`. |
| Damage and feedback | object `0x10057c10` | Calls damage routine `0x100b9510` at `0x10057cfe`; passes contact position, normal and selector to `0x10059e90` at `0x10057ddc`. |
| Effect packet | object `0x10059e90` | Packs type `0x21` / 33, position, normal and selector into a 32-byte payload; calls common sender `0x100d8be0`. |
| Receive | cshell `0x1006522c` | Actual message 33 handler reads 32 bytes and calls hardcoded effect factory `0x100660d0` at `0x100652f9`. |
| Factory | cshell `0x100661ae` | Effect 33 allocates 120 bytes, calls constructor `0x10067990`, installs vtable `0x100c61b8`. |
| Parameters | cshell `0x1006fe30` | Copies position, normal and selector; derives orientation from the normal. |
| Spawn children | cshell `0x1006fec0` | Selector 1 chooses blood; creates spray effect 5 and sprite effect 15, then returns without retaining the parent. |

The effect position comes from collision data, not an unconditional victim-center position
or a named model bone. This does not prove pixel-/triangle-accurate contact on a skinned
monster: the engine's collision representation still determines the intersection.

## What is visible

The server surface-name lookup `object:0x10044bf0` indexes the table at `0x101a167c`.
Index **1 is `Flesh`**. The client chooses blood when its incoming selector equals 1.

| Component | Verified parameters |
| --- | --- |
| Blood flash | `sprites\\BloodHit1.spr`, selected at cshell `0x1007034a`; position = contact position + normal × 4; normal-derived orientation; lifetime 0.1 seconds, delay 0. |
| Blood spray | `Sprites\\BloodSpray1.spr`, selected at cshell `0x10070385`; contact-position origin; input direction/velocity vector = normal × 100; 10 particles; 1-second lifetime. |
| Non-flesh branch | `sprites\\miss.spr` plus `Sprites\\flareParticle.spr`, with one particle. The filename does not establish that every such case is a missed attack roll. |

Flash lifetime is confirmed by effect-15 init/create/update at cshell `0x1005f3f0`,
`0x1005f5c0`, `0x1005f910`: end time is start time plus the supplied duration.
It is a short-lived sprite, not a persistent wound or ground decal in this path.

Spray effect-5 init/create/update/emission are cshell `0x1007f900`, `0x1007f9d0`,
`0x1007fa10`, `0x1007fac0`. The count byte reaches the particle API call at `0x1007fe76`;
both particle lifetime bounds are the supplied 1.0 seconds. Update uses remaining lifetime
to fade the particle-system alpha. The supplied normal vector is used to construct a
velocity distribution: individual particles do not all travel exactly along that vector.
Additional parameters include 400.0 and -650.0; their complete engine-side size/gravity
semantics and rendering units are not established by this note.

The assets themselves are small:

- `BLOODHIT1.spr`: **one frame**, referencing `SpriteTextures\\BloodHit1.dtx`, a 32×32 texture.
- `BLOODSPRAY1.spr`: **one frame**, referencing `SpriteTextures\\BloodSpray1.dtx`, a 16×16 texture.
- Both SPR headers specify 15 fps, but there is no multi-frame image sequence to animate.
  The visible animation comes from effect timing, particle movement and fading.

Both DTX files are version -5, format id 0, with four mip levels. These headers were read
with `inspect_assets.py`; temporary PNG previews were decoded using
`tools/mm9_import_discovery/convert_effect_dtx.py` and visually inspected. Exact native
blend/depth behavior and perceived sprite dimensions still need renderer-level or live validation.
The server also explicitly preloads both SPRs in `object:0x100d0740`, corroborating their use.

## Limits and implementation relevance

- The supplied configuration contains `BloodSplats=1`, and a Blood Splats UI option exists.
  Its precise gating of this path was **not established**; the hit creator has no direct
  option check. Do not infer that toggling it controls these two components without tracing further.
- After damage processing, `object:0x10057c10` can override the selector with 21 based on
  a damage-state flag at `0x102b8628`. The meaning of that flag remains unresolved. Therefore
  this is not proof that every melee contact or every damage outcome produces blood.
- The native `MeleeWeapon` contact-to-effect chain is established. A complete party-input
  dispatch trace and a live original-game hit capture were not performed.
- This is separate from the `clientfx.fxd` / `SPELLS.fxf` recipe system investigated earlier.
  Importing those spell recipes alone would not reproduce this blood feedback.
- A later OpenYAMM implementation could independently reproduce contact-triggered flash
  and spray using the original assets. It should preserve material/result selection and
  transient world-space positioning rather than attach a permanent splat to the enemy.

