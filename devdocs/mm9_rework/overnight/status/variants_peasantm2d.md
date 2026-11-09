# variants: PeasantM2d (rows 24 Town PeasantM2c, 26 Shopkeeper PeasantM2d; elf) — owner peasantm2d-agent

Project `level_generation/creatures/mm9_peasantm2d_claude/` (lease mm9:peasantm2d, claimed 2026-11-02 11:29 UTC).

## State
- Started: reading briefs, comparing MM9 PeasantM2d vs PeasantM2. Backup balance 3050 at claim.
- Decision: **variant route** on PeasantM2's body. MM9 M2d vs M2: identical skeleton (bind matrices equal), silhouettes
  overlap apart from the elf ears (front/side/3-4 overlay `review/sheet_sil_m2_red_m2d_green.png`); the rest is a ~2.6 cm rigid
  mesh offset of the torso/head against the skeleton plus <=2 cm hem/sleeve differences, below our Meshy-vs-MM9 fit noise. No warp.
- Ears: PeasantF8/M7d generator on PeasantM2's master (`work/ears_v4.blend`), human ears pressed + smoothed.
- Clips: PeasantM2's chain without Conv1/Conv3/Bow (rows 24/26 scripts: NPCbase/shopkeeper/NPC188/190/193/206); bit-identical to
  PeasantM2's installed clips (`scripts/anim_diff.py`).
- Codex: body masters (skin D design) and the D head turnaround running. Plan: body 4K retexture 10 + head D 4K retexture 10;
  tier C face = Codex repaint projected (0 credits).
- Meshy: body 4K retexture 10 (backup 3035 before), head D 4K retexture 10 (3025 before); 2985 seen after both (other agents too).
  Total 20 / 20. No further paid jobs.
- Head D fixes: mouth strip (dark slot / second-lip band) `scripts/mouth_fix.py`, eye rims + under-eye circles `scripts/eye_fix.py`;
  PeasantM2's head_seam.py dropped (it joined the brows on this paint). Tier C face: Codex repaint running.
- Gates on the geometry build: arm/hand = PeasantM2's (Fidget R 5.3 cm MM9 forehead rub; Talk L 1.1 cm 1 frame), jitter 0 fails,
  sleeve poke 0 mm every clip both sides, winding 0.
- Geometry: mouth slot closed (`mouth_close.py`, positions only + a 2-face lip hole fill), upper tunic lined (`collar_lining.py`).
- **Installed** `assets_source/worlds/mm9/models/mm9_peasantm2d.glb` sha256 af2bba9b...; bound `MM9 24 Town` (pm2d_c), `MM9 26
  Shopkeeper` (pm2d_d); rows 24/26 in mm9_npc_actor_rows.tsv (stand-ins 343/346), tables regenerated (206 rows).
- Gates: arm/hand = PM2; jitter 0; sleeve poke 0; see-through torso 359->88, sleeves 49/40->28/20, head 9; floor ok; detached 0;
  winding 0; binding regression PASS (206 descriptors / 91 models); viewer 20 switches 0 failed.
- PeasantM2 unchanged: sha256 of its installed/runtime GLB, export and master identical before/after (`work/pm2_sha256_*.txt`).
- Lease released. Details: project README.
