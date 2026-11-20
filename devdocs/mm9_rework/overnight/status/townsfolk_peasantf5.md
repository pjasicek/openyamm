# Townsfolk PeasantF5 (human peasant woman, coif) — status

- Project: `level_generation/creatures/mm9_peasantf5_claude/` (README is the record), lease `mm9:peasantf5`, owner claude-townsfolk-peasantf5.
- Rows: MONSTERS.txt 36 (Commoner, F5b, DAT CommonerHuman2FemaleA, 6 placed), 34 (Shopkeeper, F5a, class ShopkeeperHuman1FemaleB, none placed),
  41 (Shopkeeper, F5a, class ShopkeeperHuman2FemaleB, none placed). The 8 ShopkeeperHuman2FemaleA objects are row 40 (PeasantF3), not this body.
- Phase: **done, face fix applied** (orchestrator review 2026-11-02: pouting mouth, angry brows, glaring eyes, nostril triangle). Mouth geometry
  flattened (3.3 mm), eye creases and nostrils softened, Codex face repaint by landmarks projected per woman; 0 Meshy credits. Rollback of r13 in
  `work/rollback_r13/`. Before/after: `review/sheet_faces_before.png`, `review/sheet_faces_after.png`. Lease released 2026-11-02.
- Credits: **35 / 60** (Smart Topology 5, body retexture 4K 10, head retextures 4K B and A 10 + 10; backup account, 3555 -> 3480 seen before the last job).
- Installed: `assets_source/worlds/mm9/models/mm9_peasantf5.glb` (r17, sha256 4928fb9ea30f...), variants `pf5_b` (row 36), `pf5_a` (rows 34, 41).
- Binding: rows 34, 36, 41 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 356/376/383), tables regenerated (ids 9034,
  9036, 9041), `actors.yml` block `mm9_peasantf5_claude` (`MM9 36 Commoner`, `MM9 34 Shopkeeper`, `MM9 41 Shopkeeper`). Map placement left to the
  orchestrator (maps still place 376 for CommonerHuman2FemaleA).
- Gates: arm/hand 0 frames > 1 cm (Cower L forearm 1.4 cm, 1 frame, under the coif flap); skin poke (stub + sleeve) 0.0 mm all clips; legs through
  skirt 0 in all clips; jitter 0 fails; floor ok x3; winding 0; flat 0.00 body / 0.01 head; bones 0 stretching; texture body 66.6 % / head 65.9 %; detached 7
  (shins + shoes by design, bracelets <= 1.8 cm in 7/838 poses, buckle 1 pose); collapse worst Death waist 80, Hit waist 66 / armpit R 54.
- Regression on the final install: mm9 binding PASS, suite 192 passed, 1 known out05 failure. Viewer `r17-20261102`, check 0 errors.
- No background processes, no Chrome left.
- Nose/lip fix 2026-11-02 (user: "peasantf5 - something wrong on her nose?"), r18, 0 credits, no Codex run, owner f5-nose-fix. Causes: the
  nose's forward/down-facing underside filled with blotchy nearest texels and lifted +30 % under a mismatched mask (dark patch, pale ring);
  the mouth slit still opened into Meshy's cavity (lighter inner band, puckered "O"). Fix (as PeasantF1): cavity unfolded into one closed
  surface, nose tip/underside smoothed, midline fins collapsed (`tweak_pf.py`); underside repainted as skin with two nostrils on down-facing
  texels only, no lift, fin texels recoloured, normal map flat on nose/mouth (`project_face_pf5.py`). The dark neck band is MM9's own
  patterned collar (not a fault); the chin facet line is geometry, not touched. Rollback `work/rollback_r17/`. Sheet
  `review/sheet_nose_lip_before_after.png` (read). Installed r18; winding 0; regression mm9 binding PASS (187 descriptors on 80 models), suite 192 passed, 1 known out05
  failure; viewer check 0 failed, 0 console errors. Lease released.
- Nostril pass 2026-11-02 (orchestrator review of r18), r19, 0 credits, owner f5-eye-fix: nostrils smaller, cool skin-shadow tone instead of
  brown, down-facing texels only; nose tip/underside smoothing up to 3.5 mm. Sheet `review/sheet_eyes_nose_r2.png` (read). Installed r19; regression binding PASS (187 on 80 models), suite 192/1 known out05;
  winding 0; viewer check 0 failed. A soft shadow under the tip remains (the underside faces down). Lease released.
