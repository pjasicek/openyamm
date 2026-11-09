# variants: peasantgirl (MM9 rows 71, 72, 74) — owner variants-e

Project `level_generation/creatures/mm9_peasantgirl_claude/`. Lease claimed 2026-11-02 09:21 UTC.

- 09:21 lease claimed; backup balance 3295. Reading sources.
- 09:30 sources converted (pg2, pg3, pg1e, pg3e, PEASANTCHILDGIRL lib: 60 joints Bip01, 11 clips). Mesh comparison re-run: girl3 vs girl2
  head max 2.4 cm (hair), girl1e vs girl2 head max 2.3 cm (ears), torso/arms/legs identical. Rows 71/72/74 run NPCbase.scr; DAT placements:
  only row 71 (`CommonerChildHuman2ChildA`, 4 objects: 2 YanmirChild.scr, 1 NPC312.scr, 1 none); 72/74 none. Clips used: stand, walk, run,
  fidget, conv, wince, die1, cower (+Dead). Codex run 1 (three-quarter master) started.
- 10:30 HD masters (Codex, 2 runs) gated; Smart Topology 5 cr (backup 3295 before). One shell for face+dress+skirt; assembled
  (`assemble_pg.py`): head shifted 5.5 mm to the midline, mirrored, lip-to-chest needle dropped, sleeves pulled to MM9's arm (x1.23, 10 deg),
  MPFB child hands (135 mm), level neck seam, skirt lining, procedural elf ears as their own part. Rig on MM9's 60-joint child skeleton +
  30 finger bones + 5 helpers; PEASANTCHILDGIRL clips; `pony_hang.py` (long hair no longer sticks out behind in Hit),
  `skirt_gather.py` (corpse hem). Clay gates: arm/hand 0 frames > 1 cm.
- 10:55 UVs (`uv_pg.py`, body 57.4 %, head 62.3 %), needles dropped before upload. Body retexture 4K 10 cr (backup 3205 before).
  Codex head turnarounds (g2, g3, g1e) running.
- 11:10 head retextures 4K g2, g3, g1e (10 cr each; backup 3155 / 3105 / 3095 before). Credits so far 45 / 60.
  Two GLBs: `mm9_peasantgirl` (tiers pg_g2 row 71, pg_g3 row 72; no ears) and `mm9_peasantgirl1e` (tier pg_g1e row 74, elf ears).
  Face fixes: eyes (lid shading, lower-lid waterline from the lid's own skin, eyeballs 3 mm forward, lower lid opening compressed
  in geometry), mouth slit specks, head normal flattened at eyes/mouth, midline cracks fixed (tiny faces restored), per-tier skin ramp
  (neck/chest/hands match each head), cuff skin wedges repainted. Gates running.
- 12:15 r9 installed (`mm9_peasantgirl.glb` tiers pg_g2/pg_g3, `mm9_peasantgirl1e.glb` tier pg_g1e) and bound under the flock:
  `MM9 71 Commoner Child`, `MM9 72 Townsfolk Child`, `MM9 74 Townsfolk Child` (ids 9071/9072/9074, rows in mm9_npc_actor_rows.tsv).
  Regression every-binding PASS (201 descriptors / 88 models). Floor audit 3 ok (pelvis root lift fixed a 10 cm sink). Waist cap
  against see-through up the skirt. Final see-through + ear views running. README written.
- 12:55 coordinator's boy-family faults checked on the girls: back of head one continuous hairdo (no skin slit; standing, Hit, Cower,
  Death, Dead), hands toned to each girl's face (skin region B), plain bodices for g3/g1e (vest pattern removed), hairline arc lifted,
  chest specks filled, vest-edge slits / apron-side gaps / mouth-corner holes filled (`fill_holes.py`), waist cap. r12 installed,
  regression PASS. **Descriptor height to record: 130 units (1.294 m model, 129.5 measured standing), radius 21**; tables carry 151/51
  (inherited); MM9's rule gives 82/328 (the girl models' dims lie on the wrong axis). Overrides not written.
- 13:15 r13 final (hairline ledge sunk 2.5 mm): installed, both GLBs identical to export; every-binding regression PASS (201 / 88, 0
  failed); floor audit 3 ok; viewer check 27 switches, 0 errors; winding 0. Credits 45 / 60. Lease released. Done; see README.
- 14:00 coordinator pass 2 (0 credits): matte roughness + specular-free sheets, neck blobs and chin tick, hairline taper, chin smoothing,
  lip specks, brighter sockets, shorter shins (robe flags are plane-sign false positives: ray check 0 outside except 2 vertex-frames in
  Death). r14 installed; every-binding regression PASS (202 / 89); floor 3 ok. Sheets: sheet_before_after_r14, sheet_mm9_vs_ours_r14,
  sheet_face_128_r14. Final see-through running.
- 14:45 final see-through r14 (both): living clips <= 15 px, corpse from the feet <= 88 px, party 20 deg <= 14 px; viewer check 0 errors. Lease released.
- 15:40 coordinator pass 3 (0 credits): neck line and ghost flaps were in an intermediate render only (installed r14 and r15 clean); lip specks traced to hole-fill fans with a skin UV, fixed; chart-aware head padding. r15 installed, binding test PASS (214 / 92), floor 3 ok, viewer 0 errors. Sheets sheet_before_after_r15, sheet_viewer_faces_r15. Lease released.
- 16:xx user note r15 (neck seam line, ghost nose): after the PC reboot the installed GLBs were verified = r15 (byte-identical to
  work/rollback_r15); exports were an uninstalled intermediate. Lease still active. Fixes in progress (head_fix_pg / tweak_pg / tiers_pg):
  head neck blended to the tier's ramped body skin, neck normals flattened both sides, seam crease smoothed (welded), nose ghost alae
  repainted, nose base repainted, nose geometry smoothed, lower lid compressed further, dark blobs (lip corners, chin) cleaned,
  nose-tip hole fill re-textured. Clean rebuild r18 running.
- 17:xx user note fixed in r20 (neck seam colour/crease/normals, ghost nose, lid wedges, lip edge, chin dot); installed, binding test PASS (214/92), floor 3 ok, viewer 0 errors. Lease released.
- coordinator r20 follow-up: r23 installed (bridge diamond, chin dimple); binding PASS; lease released.
- face repaint (coordinator / user "if you think repaint meshy is better do that"): r23 backed up (work/rollback_r23). Head-set UVs re-laid
  (`uv_head_pg.py`: the face is ONE chart, no midline / nose / lip seams; was 50 charts; body UVs and paint unchanged; old layout
  work/uv_v1.npz). Geometry: midline V crease (depth-only smoothing + midline normal fade in build_glb_pg), chin-neck fold collapsed.
  Codex paint-over masters of the current head (references_head2/) running; then 3 head retextures (30 cr budget).
- r24 face repaint installed (30 cr: backup 2815/2805/2795 before the 3 jobs); new one-chart head UVs; binding PASS 222/97; gates in README. Lease released.
- r25 paint pass on r24 (0 credits, no Meshy/Codex): forehead/bridge kites (midline normals averaged; paint band blended), cheek blush per
  girl + rosier lips, mouth corners lifted (paint + corner normals), ear-root stubs drawn in under the hair, nostrils smaller and the nose
  underside's normals leaned forward. Installed (export = assets_source byte-identical), binding PASS 229/100, floor 3 ok. Sheets
  review/sheet_before_after_r25.png, review/sheet_viewer_faces_r25.png. Rollback work/rollback_r24. Lease released.
- r26 user note r25 mouth (0 credits): muzzle oval repainted out (front-view harmonic fill), relaxed mouth sculpted into the face
  (tweak_pg), chin dot gone, slit soft rose line, hairline sawtooth band repainted. Installed (export = source), binding PASS 230/101,
  floor 3 ok. Sheets review/sheet_before_after_r26.png, review/sheet_mouth_zoom_r26.png. Rollback work/rollback_r25. Lease released.
- r27 (30 credits: pg_head3_g2/g3/g1e, backup 2510/2500/2490 before, 2475 after): mouth geometry finalised (smooth symmetric lip line,
  corners flow into the cheeks, pocket closed onto the line), fresh Codex masters + Meshy 4K head retexture on it, paint fixes only
  (head_fix3_pg.py). Installed (export = source), binding PASS 238/104, floor 3 ok, see-through both GLBs head <= 3 px, Death <= 41.
  Sheets review/sheet_before_after_r27.png, review/sheet_mouth_zoom_r27.png. Rollback work/rollback_r26. Lease released.
- r28 user note r27 upper-lip patch (0 credits): paint-fix masks moved to the final geometry (headmap_final_pg.py), nose-underside lift
  kept off the lip, muzzle fill + upper-lip band + under-lip streaks repainted from the cheeks; installed (export = source), binding PASS
  240/105, floor 3 ok. Sheets review/sheet_before_after_r28.png, review/sheet_mouth_zoom_r28.png. Rollback work/rollback_r27. Lease released.
