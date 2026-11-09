# Variant PeasantM5 (rows 46 Town PeasantM5b, 48 Shopkeeper PeasantM5a) — owner m45-agent, 2026-11-02

Project `level_generation/creatures/mm9_peasantm5_claude/` (lease mm9:peasantm5, claimed 15:43 UTC, backup 2815).
Worked after PeasantM4.

## Log
- 15:43 lease claimed. meshcmp re-run: M5 shares Markel's and PeasantM1's exact binds (0.00 cm). vs Markel head 1.2, arms 1.6,
  legs 1.1, torso 3.5 cm p90; vs PeasantM1 head 0.9, arms 1.1, legs 1.9, torso 4.7; vs PeasantM3 binds differ 3.1 cm.
- 17:20 Decision: **variant route on Markel** (frozen; read only). Our built Markel's clay is a plain stocky shirt with belt,
  belly, rounded shoulders and rolled boot cuffs (`mm9_peasantm5_claude/review/clay_markel_pm1_pm8_body.png`); signed distance
  of our Markel to MM9 M5 ~ the same as to MM9 Markel (trunk p50 2.1 vs 1.5 cm). PM1 (hood, open jacket, bushy hair) and PM3
  (in review, binds differ 3 cm) rejected. Geometry on a copy of Markel's `hair_v1.blend`: `scripts/hair_raise.py` (full head of
  hair: Markel's sunk crown hair shell raised to ~10 mm, front hairline 3 mm, crown faired; face-shell pokes 64 -> 19, the rest
  Markel's accepted temple ones), `scripts/strip_parts_m5.py` (torc/tie, medallion, lacing plates, belt studs deleted, buckle kept).
  Upload exporter validated: Markel's uploads reproduced byte-exact in corners (`export_uploads_m5.py`). Markel sha256 baseline.
- Tiers: A (row 48 Shopkeeper, bearded auburn) = design; B (row 46 Town, darker shirt, stubble, medallion) = ramps + own head colour
  by Codex repaint (no credits). Codex body master run 1 running.
- 17:50 Codex run 1 failed once (5/5 reconnects), relaunched: 00 selected (stocky auburn-bearded man, tan linen shirt with braided
  V neckline, belt with brass buckle, charcoal ribbed trousers, cuffed boots; Markel's pose). Run 2 (01-04) and the head turnaround
  running. Test build on Markel's textures: gates = Markel's accepted (forearms 1.5-3.8 cm, hands 0 except Fidget R 1.4 cm 4 f),
  jitter 0, sleeve poke 0, detached 0, flat 0 %, winding 0; head-set stretch p90 1.73 (Markel 1.63, the raised crown).
- 17:10 Codex body masters (5) + head turnaround (4) selected and read (review/body_clean_check.png, references_head/selected_views_review.png: warm closed smile, auburn wavy hair, short full beard). Uploads exported from work/strip_m5_v1.blend with Markel's UVs (export_uploads_m5.py). Meshy 4K body retexture (backup 2705 before) and 4K head retexture (2695 before) submitted: 20 cr total. Tier B (row 46) face will be a Codex repaint projected (0 cr).
- 21:30 **Installed** `mm9_peasantm5.glb` (sha256 e545e8a23825...), bound `MM9 46 Town` (pm5_b) and `MM9 48 Shopkeeper` (pm5_a); rows
  46 -> 362, 48 -> 365 in mm9_npc_actor_rows.tsv, tables regenerated (234 rows); binding regression PASS (234 / 103 models); floor ok.
  Paint: chest skin toned to the neck, leopard neckline calmed, under-eye lid fold (geometry, 3 verts 1.5 mm) + sliver normal fixed;
  tier B face = Codex repaint projected (0 cr). Linings (neck cap, belt rim, cuffs) after the see-through gate: sleeves 78 -> 1 px,
  head 30 -> 1, torso 60 -> 36 (lying corpse under the chin) not 0. Gates: arm/hand ok, jitter 0, sleeve poke 0, detached 0, flat 0,
  winding 0. Viewer r5 20 switches 0 failed. Markel sha256 (532 files + 2 GLBs) identical. 20 credits total. README written.
- Lease mm9:peasantm5 released.
- 19:39 Lease re-claimed for the coordinator's body-size fix (user: head reads small on a bulky torso): fit the Markel-based body to MM9 M5's silhouette, 0 credits.
- Body fit r16 (coordinator, user: head reads small on a bulky torso), 0 credits: hip band scaled per height (all layers), torso,
  thighs, boot shafts and upper arms fitted to MM9 M5's surface (offset field from outer-layer sources, despiked), forearms and the
  armpit folds left as built (fitting them opened the sleeve/armpit in the see-through gate). Signed p50/p90 to M5: trunk
  2.5/4.6 -> 0.2/1.8 cm, upper arms 3.1/5.4 -> 0.8/4.0, thighs 1.9/5.3 -> 0.4/1.5; armpit wedge and forearm undersides still 2-4 cm,
  hands/feet pinned. Re-lined, rebuilt, **reinstalled** (sha256 a7e5f69a2ed7...). Gates: arm/hand better (forearms <= 0.9 cm),
  jitter 0, sleeve poke 0, see-through torso 36 -> 7 px, sleeves 1/0; floor ok; binding regression PASS (246/109); viewer r16 0
  failed. Sheets: review/sheet_bodyfit_before_after.png, review/sil_fit_final_red_mm9_m5_green.png. Markel sha256 identical.
- Lease mm9:peasantm5 released (after the body fit).
