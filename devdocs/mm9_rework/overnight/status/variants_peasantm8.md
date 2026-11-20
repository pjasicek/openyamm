# Variant PeasantM8 (row 55 Shopkeeper, skin PeasantM8a) — owner peasantm8-agent, 2026-11-02

Project `level_generation/creatures/mm9_peasantm8_claude/` (lease mm9:peasantm8). Details: its README.md.

## State (2026-11-02): installed and bound
- meshcmp peasantm8:foraddarre: head p90 1.0 cm, torso 0.8, arms 1.4, legs 2.5 (= MM9's boot sole 2.6 cm further back; trousers
  +0.5 cm). Variant route on Forad's body/rig/weights/clips; no reshape.
- Own GLB `mm9_peasantm8.glb` (sha256 d4cf7649...): Forad's ponytail, necklace and eye cups removed, nape knot smoothed; rigid chin,
  relaxed fingers (finger_pose.py, two-segment mitten), soft cuffs; own 4K body + head paint; collar and upper-lip paint fixes.
- Clips: Forad's set + Cower + Conv2/Conv3 (Narrator.scr); Conv2 hand rest (6.0 -> 0 cm).
- Meshy 20 credits (backup 3015 -> 3005 -> 2985).
- Bound `MM9 55 Shopkeeper` (row 55 -> 374 in mm9_npc_actor_rows.tsv, tables regenerated); binding regression PASS (202/89).
- Forad unchanged: 972 project files + both installed GLBs byte-identical before/after.
- Gates: arm/hand = Forad's (Talk L 3.3 cm hand on heart); jitter = Forad's 5 accepted fails; sleeve poke not 0 at hard wrist
  bends (Hit R 24.3, Talk L 16.4 mm; Death R 24 -> 3); floor ok; detached 0; winding 0; viewer 12/0 failed.
- See-through (every clip, step 3): head/torso/boots/trousers 0; sleeves only thin cuff-rim slivers (R 22 px Conv2, 17 Conv3,
  12 Running, 9 AttackMelee; L 4 Talk), the same without the soft cuff; Kira's wrist_fill rim cap does not run on Forad's lined
  rims: not fixed. Full actors suite 192 pass, 1 known fail (out05). LOD0 7,168 triangles.
- Lease released.
