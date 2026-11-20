# MM8 Couatl (m408) — Claude playbook production

Built and installed on 2026-10-18. This is the ground-travelling winged serpent: a travelling body wave, restrained
feather-wing beats, raised neck, opening jaw, paired head fins and a tail fan. The rig and motion are authored locally;
no humanoid animation or paid rigging job was used. User artistic acceptance remains pending.

## Deliverables

- [Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m408_claude/review/viewer/): all three tiers,
  nine clips, fixed cameras, native source frames and frame feedback.
- [Portable GLB](export/mm8_m408.glb), with shared textures, palette ramps and colour/shadow LODs.
- [Editable Blender master](work/m408_textured_master.blend), with packed textures, the full rig and nine actions.
- [Selected UV/animation master](work/uv_master_v3.blend) (Attack v2; `uv_master_v2.blend` holds Attack v1), [motion specification](motion_spec.json),
  [delivery checks](review/delivery_checks.json) and [canonical progress](creature_3d_progress.json).
- Source: `assets_source/worlds/mm8/models/mm8_m408.glb`; cooked runtime:
  `assets_dev/worlds/mm8/models/mm8_m408.glb`; binding: `assets_dev/worlds/mm8/models/actors.yml`.

Native source family **m408** maps to merged descriptor IDs **7–9**, named `Couatl (winged snake) A/B/C`, with sprite
groups **m409/m410/m411**. The unrelated merged Swordsman m408 group must not receive this model. Palettes are
408, 410 and 411. All 155 original frames and all three palettes were hash-verified unchanged after installation.

## Model and motion

The selected mesh has **12,952 triangles**, a 36-bone deformation rig plus `MouthSocket`, and at most four influences.
Colour LODs contain **12,952 / 6,473 / 3,236 / 1,614** triangles; separate shadow copies use the same levels with the
reduced casters inset. One primitive and four shared images serve each colour LOD: 2K base colour, 1K normal,
1K material response and 1K RGBA region mask. Only ramp data differs between runtime tiers.

| Clip | Duration | Behaviour |
|---|---:|---|
| Standing | 2.000 s | Subtle motion over the native held pose |
| Walk | 0.875 s | Travelling ground wave and small wingbeats |
| Run | 0.625 s | Faster wave; movement-driven playback |
| Attack | 1.250 s | Rears up on the lifted fore-body, gapes upward, strikes forward and down to the ground, recovers (v2) |
| Cast | 1.250 s | Distinct head-up release |
| Hit | 0.750 s | Recoil and recovery |
| Fidget | 1.125 s | Tail-fan lift and oscillation |
| Death | 0.875 s | Recoil, forward collapse and folded head fins |
| Dead | 1.000 s | Exact held endpoint of Death |

Attack and Cast mark impact/release at 0.9 s; the engine fits that lead-in to the native 1.0 s action and retains
0.35 s of follow-through. Both ordinary attacks use Attack; spellcasting uses the distinct Cast clip. Missiles and
spells release from the mouth. Native simulation, damage, collision and loot rules are unchanged. In normal gameplay
the fallen body transitions to the existing loot satchel; the portable model also contains the held Dead pose.

Standing height is calibrated from `m408sa2`'s **115-pixel** silhouette and the evaluated 0.966352634 m model height:
scale **119.004177086**, identical for all three native frame scales of 1. The fixed yaw offset is −π/2. The body and
hidden feather structure are a 3D interpretation; the tail projects longer in profile than the flat source. This is
native-informed motion, not an exact reconstruction of every held bitmap.

**Attack v2 (2026-10-18, user review of the reduction: "he stands up, then attacks, then goes back down").** The v1
clip barely rose and bit at head height. v2 follows `m408aa`-`ah`: the fore-body lifts from Tail_06 and the neck turns
near vertical (head joint 0.53 -> 0.84 m, top 0.97 -> 1.12 m, jaws open upward) by 0.35 s, holds to 0.6 s, arcs
forward and down to the impact marker (mouth socket 4.6 cm above the ground, 4 cm ahead of the held mouth at 0.9 s)
and is back in the held pose by 1.2 s. `animate_couatl.py` (`ARC_*` profile, `arc()`) rebakes only Attack into
`work/uv_master_v3.blend` (`COUATL_BASE=work/uv_master_v2.blend COUATL_OUT=work/uv_master_v3.blend
COUATL_CLIPS=Attack`); Cast and the other clips rebake bit-identically, and the rebuilt export differs from the installed
one only in Attack (geometry, skin, LODs and variants identical). Native comparison:
`../mm8_m408_reduce_claude/review/attack_v2/sheet_native_new_installed.png`. Installed 2026-10-18 with the reduced
model (`../mm8_m408_reduce_claude/`, 7,122 triangles; the installed source is no longer this project's export). Rebuild note: Blender 5.2's bundled Python has no PIL, so
`export_glb.py` stops at `material_contract.finish`; run that step with the system Python and continue the
`build_runtime.sh` chain from `prepare_actor_glb.py`.

## Materials and corrections

Five selected HD masters and their exact generation provenance are in [references_hd](references_hd/).
Smart Topology cost **5 credits** and the four-view retexture **10 credits**, total **15 Meshy credits**.
Original job returns and hashes are retained; a rebuild does not submit another paid job.

Local corrections slimmed the body, added bend support, split and capped the closed mouth, made upper-lip weights
rigid to the skull, folded the paired fins for death, and removed a changing phase from the held corpse. The final
native comparison corrected an initial scale based on the reared attack instead of the standing silhouette.

Meshy removed 74 small mouth-region triangles from its static return. Of 10,776 upload vertices, 10,716 retain exact
position/UV correspondence after uniform registration; the remaining 60 are confined to the mouth. The original
geometry and UVs remain authoritative, with locally painted interior surfaces and corrected lip weights.

`compose_couatl.py` derives four recolour regions from the native palettes, pads their masks across UV gutters,
protects eyes/teeth/interior and writes `m408_material_classes.png`. Class 11 denotes feathers and the tail fan.
AO is retained separately and contributes gently to the base colour. The current engine contract uses material-map
**R for specular, G for roughness, B for metallic**, with metallic zero. `material_contract.py` preserves these bytes
and removes Blender's unsupported specular extension. Normal-map orientation measured −0.985 before the green-channel
correction and +0.985 afterwards.

## Verification and native comparisons

- Half-frame motion checks: finite geometry, ground contact, exact loop joins, stationary Dead and zero Death/Dead
  endpoint difference. [Deformation audit](review/deformation_audit.json).
- Reimported export against the master: nine clips, worst sampled surface difference **0.012 mm**.
  [Parity record](work/export_parity.json). Final topology, weights, UVs, materials and winding checked.
- Browser: all **27 tier/clip combinations** load without errors; all nine clips exercised at 1× and ¼× playback,
  with sampled images inspected. [Playback evidence](review/final_playback/playback.json).
- Ordinary desktop build passed. The Couatl actor regression passes, including the shared tiers, unchanged native
  state, rig/clips and mouth release bounds. The MM6 demon model/simulation regression also passes.
- The broader MM8 actor subset passed four cases and failed the unrelated Serpentman case because its binding is
  absent from the current MM8 manifest. This task did not alter that family. Android was not built or tested.
- Native NVIDIA/Wayland checks cover both chosen locations, three tiers, combat, recoil/death, the normal loot-satchel
  transition and forced LOD3. Logs and launcher receipts accompany the captures.

| Location | Models | Original sprites |
|---|---|---|
| New Sorpigal | [Capture](review/ingame/out_3d/tiers.png) | [Same camera](review/ingame/out_sprite/tiers.png) |
| Agar's Laboratory | [Capture](review/ingame/in_3d/tiers.png) | [Same camera](review/ingame/in_sprite/tiers.png) |

[Mouth effects in combat](review/ingame/combat/release.png) · [Fallen bodies](review/ingame/combat/death.png) ·
[Loot transition](review/ingame/combat/dead.png) · [Forced lowest LOD](review/ingame/out_lod3/tiers.png).
Comparisons use identical cameras and spawn commands. Ordinary AI remains live, so orientation and poses can differ.
The isolated fixture preloads foreign sprite families; production maps were not edited.

## Rebuild

From the repository root, claim this creature through `tools/creature_workspace.py`, then run
`bash level_generation/creatures/mm8_m408_claude/scripts/build_runtime.sh LEASE_TOKEN [--install]`.
This starts from the selected `uv_master_v2.blend`, exports materials/actions, checks parity, builds LODs, applies
shadow correction and native ramps, validates the GLB, and refreshes the viewer tiers. Add `--install` only when the
result is ready for runtime. Texture changes begin with `scripts/compose_couatl.py` under the same workspace guard.
