# Townsfolk PeasantF1 (older human woman in a hood) — status

- Project: `level_generation/creatures/mm9_peasantf1_claude/` (README is the record), lease `mm9:peasantf1`, owner claude-townsfolk-peasantf1.
- Rows: MONSTERS.txt 29 (Commoner, F1b, DAT CommonerHumanFemaleA, 11 objects / 10 actors in the rebuilt maps), 33 (Shopkeeper, F1a,
  ShopkeeperHumanFemaleA, 2 objects / 3 actors). No other row names PeasantF1.
- Phase: **done** (installed, bound, gates run, sheets read, README written).
- Credits: **35 / 60** (Smart Topology 5, body retexture 4K 10, head retextures 4K faces B and A 10 + 10; backup account).
- Installed: `assets_source/worlds/mm9/models/mm9_peasantf1.glb`, variants `pf1_b` (row 29), `pf1_a` (row 33).
- Binding: rows 29, 33 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 349 / 355), tables regenerated (ids 9029,
  9033), `actors.yml` block `mm9_peasantf1_claude` (`MM9 29 Commoner`, `MM9 33 Shopkeeper`). Map placement left to the orchestrator.
- Clips: PeasantFemale library, the set the scripts play (as PF8): stand1, Walk, run, Fidget4, Conv1-3, Wince1, Die1, Dead, cower.
- Gates: arm/hand 0 frames > 1 cm; sleeve poke (arm stub through the short sleeve) 0 mm every clip; legs through skirt 0 in all clips;
  jitter 0 fails; floor ok (rows 29, 33); winding 0; flat 0.00 / 0.01; bones 0 stretching; texture body 66.5 % / head 58.5 %; detached 2
  (free legs inside the skirt, by design); collapse worst Hit armpit R 74, waist 67, Death waist 60 (folds, no tear, looked at).
- Wave-1 lessons checked: fringe/hairline (hood painted with the face: no seam), sleeves/hands (0 mm poke, clean skin hands), eyes/brows
  (irises visible, red rims removed, no second brow line).
- Face fix 2026-11-02 (orchestrator review: pout, chin smudge, staring eyes, A not elderly, jagged collar edge, cheek speck), 0 credits:
  Codex head repaint by landmarks per woman (`references_face/`, `scripts/codex_face.sh`, `align_face_pf1.py`, `project_face_pf1.py`):
  warm closed-lip smile, relaxed eyes, clean chin, A clearly elderly; chin/lips smoothed (positions only); the speck was a Meshy hole
  beside each cheek, closed; collar line on the smooth neck-cut plane; even neck skin. Rollback `work/rollback_r12/`. Before/after sheet
  `review/sheet_faces_before_after.png`. Gates re-run on r21: all as before (arm/hand 0, sleeve poke 0, robe 0, jitter 0, floor ok).
- Open: closed smile, not MM9's open smile with teeth; B's eyes still a little wide in lit close-ups (round eyeball geometry); A's head
  is Meshy's slimmer face, not MM9's plump grandmother; tier-A embroidery soft (projected from MM9's 256 px skin).
- Regression (final install r21): mm9 binding PASS (182 descriptors on 75 models, 0 failed), suite 192 passed, 1 known out05 failure.
- Viewer `r21-20261102` (r12 in `review/viewer_before/`), check 0 errors. No game run (descriptors not placed yet). No background processes, no Chrome left. Lease released 2026-11-02.
- Nose/lip fix 2026-11-02 (user: "something wron with her nose + lip? like double textures?"), r22, 0 credits, no Codex run, owner
  f1-nose-fix. Causes: the geometry's nose ends ~6 mm above the painted nose and its forward/down-facing underside shaded dark across the
  painted nostrils (r21 also kept Meshy's first paint on the tip: ringed nostrils, a boundary at the alae; tier A's repaint drew two flaps);
  a flat bridge facet caught the light (pale stripe); midline fins drew a light line; the closed mouth cavity was a folded flat plate (a
  lighter "second lip" inside the lips). Fix: mouth cavity unfolded into one closed surface, nose tip/underside and bridge smoothed, fins
  collapsed (`tweak_pf1.py`, positions only); repaint nose warped onto the geometry (`warp_nose_pf1.py`, A takes B's nose); whole nose
  projected, underside skin + two nostrils, fin texels recoloured, normal map flat on nose/mouth (`project_face_pf1.py`). Ear-sweep spot:
  the clamped ear plate's hood-orange outline removed from the head paint and the plate toned/shaded; a faint plate edge and the hood's
  own shards remain (geometry). Rollback `work/rollback_r21/`. Sheet `review/sheet_nose_lip_before_after.png` (read).
  Installed r22; winding 0; regression mm9 binding PASS (187 descriptors on 80 models), suite 192 passed, 1 known out05 failure; viewer
  check 0 failed, 0 console errors. Not touched: pale crescent under each lower lid, grey speck at the inner brow ends. Lease released.
- Eye area / ear plate pass 2026-11-02 (orchestrator review of r22), r23, 0 credits, owner f1-eye-fix: the pale jagged crescent under each
  lower lid was Meshy's up-facing lid ledge in front of the eyeball (lit from above); the grey brow speck a spike at each socket's upper
  inner corner; the hood-edge patch the clamped ear plate's facet. Fix: corner spikes smoothed, the ball's lower part moved behind a smooth
  lid curve, ear plates smoothed (`tweak_pf1.py`); ledge and ear-plate normals relaxed toward the surrounding surface (`build_glb_pf.py`);
  socket pocket texels filled, lid band toned (`project_face_pf1.py`). Sheet `review/sheet_eyes_nose_r2.png` (read). Installed r23; regression binding PASS (187 on 80 models), suite 192/1 known out05;
  winding 0; viewer check 0 failed. Left: small pale fleck at one inner eye corner, A's ear plate a faint patch in 3/4. Lease released.
