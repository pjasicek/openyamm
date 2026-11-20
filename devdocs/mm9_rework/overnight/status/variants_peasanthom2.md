# variants: PeasantHOM2 (row 59 Shopkeeper, skin PeasantHOM2a) — owner variants-a

Project `level_generation/creatures/mm9_peasanthom2_claude/` (lease mm9:peasanthom2). Details: its README.md.

## State (2026-11-02): installed and bound
- Same mesh as PeasantHOM1 (meshcmp 0.0 cm head, 0.1 torso, arms max 2.0). MM9's HOM2a is a different man in different clothes
  -> new tier **`phom2_a` of `mm9_phom1.glb`** with its own body colour+normal and head colour+normal (no ramps).
- Meshy 20 credits (body + head 4K retextures on HOM1's own uploads). Codex masters made as edits of HOM1's masters, aligned
  to HOM1's silhouettes.
- `add_tier.py` appends only; `verify_append.py` OK (every old bufferView/JSON entry identical), `glb_diff.py` 0.000 mm all
  clips, all 8 HOM1 images same; cooked copy keeps the old .oytex URIs. Rollback in `work/rollback/`.
- Installed `mm9_phom1.glb` sha256 d79023f0...; `MM9 59 Shopkeeper` bound (skin phom2_a), row 59 -> 445 in
  mm9_npc_actor_rows.tsv, tables regenerated; binding regression PASS (197 descriptors / 85 models); floor ok.
- Clips: row's scripts play none beyond NPCbase Cower; phom1 carries all 11 clips.
- Open: see-through gate shows HOM1's approved mesh openings (knees in Running, cuffs, hem); not fixed (would change the
  approved tiers). Map placement still the stand-in (orchestrator).
- Lease released.
