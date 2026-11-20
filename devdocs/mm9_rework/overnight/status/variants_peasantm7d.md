# variants: PeasantM7d (rows 25 Town PeasantM7d, 27 Shopkeeper PeasantM7c; elf) — owner variants-a

Project `level_generation/creatures/mm9_peasantm7d_claude/` (lease mm9:peasantm7d). Details: its README.md.

## State (2026-11-02): installed and bound
- PeasantM7's body/rig/weights/clips + procedural elf ears (rigid on the head; Meshy's human ears pressed into the skull).
  Own GLB `mm9_peasantm7d.glb` (sha256 07e75223..., v2), tiers pm7d_d (row 25), pm7d_c (row 27).
- Meshy 20 credits (two 4K head retextures, D and C). Body = PeasantM7's paint + new 4-region mask (sleeves split) + ramps.
- Head paint fixes: procedural skin ears, pressed-ear skin, hair edge at the ear roots, neck collar paint -> skin, throat
  panel = PeasantM7's undershirt paint, C/D eye rims softened.
- Gates: arm/hand (Fidget R 2.2 cm = M7's installed with today's gate), jitter 0 fails, sleeve poke 0, floor ok, winding 0,
  bones 0, detached 0, flat 0.00, viewer 20 switches 0 failed; binding regression PASS.
- PeasantM7 untouched (installed sha256 35e99c36... unchanged).
- v2: ear winding was inside out (fixed: recalc normals); linings at the boot tops and the belt seam (PeasantDM2's
  rim_lining.py). See-through worst px v1 -> v2: boots 48/19 -> 4/10, trousers 42 -> 8, torso 19 -> 19 (slit sliver), head
  14 (crown/ear-root specks), sleeves 7/4. Binding regression PASS (198 descriptors / 86 models) on the final install;
  full actors suite 192 pass, 1 known fail (out05).
- LOD0 9,630 triangles (M7 7,313 + ears 588 + linings 1,729).
- Leases released.
