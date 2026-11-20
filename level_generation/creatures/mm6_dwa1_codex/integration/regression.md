# Proposed orchestrator regression: mm6_bdwarf_codex_full

This session did not install assets or execute these tests. Batch rules reserve all game execution for orchestration.

Install `export/mm6_dwa1.glb` and `export/mm6_dwa1_axe.glb` into the MM6 models mount; merge `actors.yml`.
Use world **mm6**, controlled indoor map **6d07.blv**, summoned monster ids **520, 521, 522**.
Also inspect a native encounter in **6d05.blv** (Snergle's Caverns) or **6d09.blv** (Snergle's Iron Mines),
and the same summoned tiers outdoors on **oute3.odm**. Capture front, side, rear and three-quarter views indoors
and outdoors, close attack/hit/fidget sequences, falling/corpse and each LOD transition. Verify the real GPU in logs.

## Size bounds

Use posed mesh height, sole to helmet spike, excluding the held axe. The front native standing PNG has 222 alpha
pixels (canvas 226×256, alpha bbox 57,34,165,256); the sprite scales, not descriptor collision heights, are authoritative.

| Monster id | Descriptor / name | Target engine units | Proposed ±5% bounds |
|---|---|---:|---:|
| 520 | BDwarf A / Dwarf | 144.298668 | 137.083735–151.513601 |
| 521 | BDwarf B / Dwarf Warrior | 155.399334 | 147.629367–163.169301 |
| 522 | BDwarf C / Dwarf Lord | 166.500000 | 158.175000–174.825000 |

LOD0 Standing median is 1.419452369 metres. Scale A = 222 × 0.649994 / 1.419452369 = **101.657985**.
B/C inherit `scale_reference: BDwarf A`, preserving the native sprite scale ratios. All tiers share geometry.
Do not use descriptor collision heights 131/141/181 as visual scale targets.

## Behavioral and rendering assertions

- All three native tiers bind the intended colours: green/teal, blue/purple, red/brown. Leather, skin, hair and dull steel
  remain the same. Confirm no missing maps or unexpected white metal under indoor and outdoor lighting.
- Standing free arm stays relaxed. Walking/Running match movement without an exaggerated crouch. Hit/Fidget move
  both arms and the axe. Every one-shot transitions from Standing and finishes or holds correctly. Dead equals Death's endpoint.
- Both native physical attacks use Attack; secondary attack is not a ranged projectile. No spell or Cast binding is required.
  Confirm actual melee damage coincides with **0.71875 s** in the 1.5 s clip using existing animation timing semantics.
  Gameplay data and native AI/recovery timing must stay unchanged.
- Check the axe's cutting edge leads into the target; the static axe attachment follows `Axe` on the animated skeleton
  through turns, attacks, hit and death. Inspect grip, wrist, shirt/yoke, hem, nape/collar and head clearance.
- Confirm the conservative 25° yaw / 12° pitch look overlay in native use, including worst combinations during Attack.
  Offline contact checks cover exported clips without runtime look blending.
- Check foot contact, corpse grounding, LOD silhouette and shadow transitions. Offline worst sole penetration is
  1.984 mm in Running (within the 2 mm gate); keep a close eye on uneven ground and runtime blending.
- Check save/load preserves tier, animation binding and attachment. Verify affected MM6 paths and existing MM7/MM8
  creature/material/attachment paths; no shared engine change is included in this handoff.

Use the existing focused creature regression mechanism; build/run only during orchestration. No Vulkan authorization
is granted by this handoff. Record native captures and regressions separately from the completed offline asset gates.
