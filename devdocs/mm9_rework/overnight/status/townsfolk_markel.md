# Unique Markel the Great — status

- Project `level_generation/creatures/mm9_markel_claude/`, lease `mm9:markel` (owner claude-townsfolk-markel), budget 60.
- Row: MONSTERS.txt 248 "Markel the Great" (Markel.abc, skin Markel.dtx, NPCbase.scr, BaseName PeasantMale).
- Placements: Guberland City `MarkeltheGreat0` (NPC127.scr: `loopanim Sit`), Afterworld `MarkeltheGreat0` (no script -> NPCbase,
  hidden), Thronheim `Markel` (ARG_Markel.scr: Sit loop, Sc2_MARKEL02/04/08/10/13/15/21, Applause, Agree, walkto, static_die2;
  Filename property says Kira.abc), Thronheim props `MarkeProp` (PropAnim Sit) and `MarkeProp0` (PropAnim static_die2).
- Phase: **done** (installed, bound, gates run, sheets read, README written; lease released).
- Credits: **25 / 60** (Smart Topology 5, body retexture 4K 10, head retexture 4K 10; backup account, 3350 -> 3325 before the retextures).
- Installed: `assets_source/worlds/mm9/models/mm9_markel.glb` (sha256 be0bcbda7dd0..., hair reshape r3), review root refreshed.
- Binding: row 248 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 579), tables regenerated (id 9248), `actors.yml` block
  `mm9_markel_claude` (`MM9 248 Markel the Great`). Map placement left to the orchestrator (rebuilt maps still place 579).
- Skeleton/clips: MARKEL.abc = PeasantMale 45 joints; library stand1, walk3, run, fidget4, conv2, hattack1, wince1, die1, cower + own sit,
  Applause, Sc2_MARKEL02/04/08/10/13/15, Sc2_markel21, static_die2 (StaticDie). Agree (ARG_Markel.scr) has no source clip. No attachment.
- Face: Meshy's hair cap repainted bald on the crown (bald_crown.py) and sunk under the scalp (crown_shrink.py); cream-fur tail of the
  hair recoloured copper (back_hair.py); lower-lid speck repainted (spot_fix.py); eyes open/blue, one relaxed brow, no pout, no seam.
- Gates (final): arm/hand 0 frames > 1 cm except Fidget R 1.4 cm 4 f, Applause 2.2-2.3 cm (hand against hand at the claps),
  Sc2_MARKEL04 L 3.7 cm 48/578 f (capped push: full push jittered 2.2-6 deg/f), Sc2_Markel08 L 2.4 cm 9 f, Sc2_markel21 R 2.4 cm 7 f;
  sleeve poke 0 mm every clip both sides (was 9-27 mm); jitter 0 fails (was 4); floor ok (walk -0.2..+1.8); winding 0; detached 0
  (was 7); flat 0.0 %; bones: R thigh 11-12 % (MM9 hip slide); texture body 59.3 % / spread 1.06 / fragments 0.1 %, head set 43.8 %.
- Regression (final install): `mm9_actor_models_build_every_binding` PASS (187 descriptors on 80 models), suite 192 passed, 1 known out05.
- Viewer r2-20261102, check 20 clips 0 failed. No game run (descriptor not placed yet). No Chrome or background processes left.
- Open: no rings on the hands (MM9 has gold rings); a small gold facet on the back of the collar and faint mirrored fur in the refilled mantle patch (r3); faint edge of
  the repainted lower-lid triangle in tight close-ups; Sit grounded without a chair (as Bjarni/Tryggva).

## Log
- 00:08 UTC lease claimed; reading references. Credits 0 (backup 3350).
- 00:20 UTC skeleton: MARKEL.abc = the 45-joint PeasantMale skeleton (names identical to pmale.glb) + 11 own clips (Markel, sit,
  Applause, Sc2_MARKEL02/04, SC2_Markel08, Sc2_Markel10/13/15, Sc2_markel21, static_die2). No sockets, no attachment: the book in
  the Argument scene is a separate prop (Prop8). Route = Bjarni's (same skeleton, PeasantMale library from mm9_peasantm7_claude).
- 00:35 UTC HD master 00 accepted (Codex run 1, halo removed by clean_alpha.py); Smart Topology body_smart_v1 done (5 cr, backup
  3330 before). Fit (joint moves <= 6 cm), reduce 15,918 -> 8,612, MPFB hands, head split (parts 1,2,6,10,11: head shell, hair,
  neck, eyes; cut 0.62), fix_flips (2), sleeve_tuck (L 35 / R 31 verts, up to 19 mm). Codex run 2 (01-04) and UVs running. Credits 5.
- 01:00 UTC masters 01-04 and head turnaround accepted; body UVs (body atlas 59.5 %) and head UVs (62.3 %); body and head 4K
  retextures done (backup 3325 before, 10 cr each). Credits 25 (final unless a repaint is needed).
- 01:35 UTC first runtime build (8,292 tris LOD0). Face review: Meshy painted a hair cap with a jagged bald streak where MM9's
  Markel is bald on the crown -> bald_crown.py (crown repainted with forehead skin, feathered strand-noise hairline, normal
  flattened) + crown_shrink.py (hair-shell vertices over the crown sunk under the scalp, positions only); spot_fix.py (beard-brown
  specks at the lower lids); hand_clean.py. Iterating on the hairline.
- 02:10 UTC face settled (bald crown + sunk hair cap, lower-lid speck repainted from 3D neighbours). Gates r1/r2: sleeve poke
  9-27 mm (toothed cuff rim over the stub) -> cuff_trim.py at -2.2 cm, bracer_rigid.py, sleeve_tuck.py (TUCK_DEEP 1.4 cm);
  detached 7 parts -> accessory_weights.py + drop_micro_parts.py (Sven's); jitter 4 fails -> per-clip hand_rest settings and Talk R
  abduction (clap_spread.py). Gates r3 running.
- 02:55 UTC final build installed (wrist fixes, accessory weights, per-clip hand rest, walk smoothing 0.04, back hair), bound under the
  flock, tables regenerated; gates_final, floor audit, viewer check, regression PASS; README written; lease released. Credits 25.
- 03:10 UTC orchestrator review: back hair is a bulbous mass behind the head; lease re-claimed for the hair reshape (0 credits). Rollback work/rollback_r2/.
- 04:20 UTC hair reshape r3 done (orchestrator review): hair shell cut to the nape (136 faces) and pulled to 0.8-1.5 cm off the skull,
  weights from the skull/neck (hair_reshape.py); mantle paint under the old tail refilled (mantle_fix.py); the U-shaped band on the back
  of the head removed (back_hair.py skin recolour + soft zone, pad_head.py). Collar check in 10 clips from back and sides: nothing pokes
  through. Gates: arm/hand unchanged, sleeve 0 mm, jitter 0, detached 0, winding 0, flat 0, floor ok; head set atlas 39.1 %, stretch p90
  1.63 (was 1.30). Installed (sha256 be0bcbda7dd0...), binding regression PASS, viewer r3 check 20/0. Credits still 25. Rollback
  work/rollback_r2/. Sheets: review/sheet_hair_head_before_after.png, sheet_hair_body_before_after.png, sheet_hair_viewer.png,
  hair_clips_1.png/hair_clips_2.png. Lease released.
