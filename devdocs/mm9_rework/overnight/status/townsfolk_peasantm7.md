# Townsfolk PeasantM7 (human man) — status

- Project `level_generation/creatures/mm9_peasantm7_claude/`, lease `mm9:peasantm7` (owner claude-townsfolk-peasantm7, token in `LEASE_TOKEN.txt`), budget 60.
- Rows naming PeasantM7.abc: 51 Commoner (Peasant Human2 MaleA B, PEASANTM7B), 53 Town (Peasant Human2 MaleB B, PEASANTM7A).
  Skins M7C/M7D belong to PeasantM7d.abc (rows 25, 27), not this body.

## Log
- 20:12 UTC lease claimed; reading references. Credits 0.
- 20:16 UTC HD master 00 accepted (Codex halo removed by scripts/clean_alpha.py); Smart Topology body_smart_v1 done (5 credits, backup 3700 before). Codex run 2 (01-04) running.
- 20:20 UTC fit to the MM9 skeleton (fit_rig.py, Spine3 band fix: centre_interp), reduce 15,100 -> 7,809, MPFB hands grafted, head split (neck cut 0.62, radius 0.105). texpass_uv (uv_atlas) running.
- 20:27 UTC HD masters 01-04 accepted. Body UVs (uv_atlas): body atlas 55.7 %. Body retexture body_retexture_tp submitted (4K, 10 credits; backup 3665 before). Head UVs and Codex head turnaround running. Credits 15.
- 21:01 UTC runtime built (LOD0 7,313 tris), tiers by region mask + ramps, installed as worlds/mm9/models/mm9_peasantm7.glb; viewer check 26 switches 0 failed. Credits 25. Next: binding, regression, sheets.
- 22:05 UTC tiers refit (v1.3-v1.6: fit on class texels only, MM9-A chroma per luminance quantile, hair mask cap + nape);
  binding under the flock: rows 51/53 in mm9_npc_actor_rows.tsv (legacy 368/371), tables regenerated, `MM9 51 Commoner`
  (pm7_b) and `MM9 53 Town` (pm7_a) in actors.yml block `mm9_peasantm7_claude`. Floor audit ok both.
- 22:40 UTC fringe lesson: grey jagged band under the fringe (B) / pale ginger rim (A) found in close-ups; fixed by
  `scripts/fringe_fix.py` (hair-shell rim and forehead band repainted), viewer v1.11, reinstalled. Final regression running.
- Credits 25 (ST 5, body retexture 10, head retexture 10). Map placement left to the orchestrator (README "Binding plan").
- 21:48 UTC final: regression actors --world mm9 passed 192 / failed 1 (known out05), mm9_actor_models_build_every_binding PASS. README written. Lease released. Done.
- 21:54 UTC user review: hands through the sleeves + blotchy hands/dark nails. Lease re-claimed (budget 10). Rollback of the v1.11 install in work/rollback_v1/.
- 00:xx UTC v2.2 wrist fix: stub tucked inside the sleeves (`sleeve_tuck.py`, master `work/texpass_head_tuck.blend`), skin paint
  removed from the sleeves above the cuffs (`sleeve_paint_fix.py`), hands repainted clean (`hand_clean.py`). New gate
  `sleeve_poke_gate.py`: before 5-16 mm in every clip, after 0 mm / 0 frames in all 13 clips, both sides. Arm/hand, jitter (same
  2 known fails), winding 0, detached 0, flat 0, texture, floor ok; regression actors --world mm9 passed 192 / failed 1 (known
  out05), mm9_actor_models_build_every_binding PASS. Reinstalled; viewer v2.2. Meshy 0 credits (total 25). Lease released.
