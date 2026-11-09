# Unique Tryggva Ravenlocks — status

- Project `level_generation/creatures/mm9_tryggva_claude/` (README is the record), lease `mm9:tryggva` (owner claude-townsfolk-tryggva), budget 60.
- Row: MONSTERS.txt 250 "Tryggva Ravenlocks" (Tryggva.abc, skin tryggva.dtx, NPCbase.scr, BaseName PeasantMale); stand-in today legacy 607.
- Placements: Frosgard City `TryggvaRavenlocks0` (NPC180.scr: `loopanim Sit`), Thronheim `Tryygva` (ARG_Tryygva.scr: Sit loop,
  Agree, Applause in the Argument scene), Thronheim `TryygvaProp` (PropAnim Sit), Afterworld `TryggvaRavenlocks0` (no script -> NPCbase,
  Cower), corpse props `Tryygva` (PropAnim `Static_die1`) in Afterworld and Yorwick.
- Skeleton: TRYGGVA.abc = the 45-joint PeasantMale skeleton with 5 own clips (Tyrggva bind pose - unused, static_die1, Agree, Applause, sit).
- Phase: **done** (installed, bound, gates run, sheets read, README written).
- Credits: **25 / 60** (Smart Topology 5, body retexture 4K 10, head retexture 4K 10; backup account, 3405 -> 3295 over the session).
- Installed: `assets_source/worlds/mm9/models/mm9_tryggva.glb`; `actors.yml` block `mm9_tryggva_claude` (`MM9 250 Tryggva Ravenlocks`);
  row 250 in `mm9_npc_actor_rows.tsv`, tables regenerated (id 9250). Map placement left to the orchestrator (transcoder switch).
- Clips: PeasantMale library stand1, walk3, run, fidget4, conv2, hattack2, wince1, die1, cower + own sit, Agree, Applause, static_die1.
- Gates: arm/hand 0 cm into the body in every clip (Fidget R 1.1 cm 1 frame; Applause 2.0-2.1 cm is hand against the other hand at the
  claps, 0 against the body); sleeve poke 0 mm every clip both sides (was 27-43 mm R); jitter 0 fails; floor ok (Sit/Agree/Applause
  seated on the floor as Bjarni/Forad, DeadStatic grounded); winding 0; bones 0 stretching; detached 0; flat 0.0 %; texture body atlas
  50.9 % (below 55 % soft target), spread 1.08, fragments 0.4 %; head set 39.1 %.
- Faces (wave-1 lessons): eyeballs removed and sockets relaxed; Codex eye-area + parting repaint projected from the front (one brow pair,
  level open eyes, no band, no red rims); hair rim and face shell above the hair edge repainted as hair; whole neck in the head set (no
  neck seam); hands one clean skin colour; sleeves tucked and the sleeve closure inside the stub removed.
- Regression (final install): mm9 `mm9_actor_models_build_every_binding` PASS, suite 192 passed, 1 known out05 failure.
- Ears (r3, ear sweep 2026-11-02): hair-coloured jagged patches on both ears fixed (`scripts/fix_ear_try.py`, last step of
  `head_chain.sh`; cause: fringe_fix.py repainted the ears' skin as hair, plus Meshy hair paint on the lower ear faces). Sheet
  `review/sheet_ear_before_after.png`; only the head colour/normal images changed. Rollback `work/installed_preear.glb`.
- Viewer r3-20261102, check 14 clips 0 failed. No game run (descriptor not placed yet). No background processes, no Chrome left.
- Open: Applause fingers interleave ~2 cm; body atlas 50.9 %; close-up nostril hook and a lighter jaw edge; fur painted tabby-striped;
  Sit grounded unlike MM9's raised sit (MM9's chairs) - consistent with Bjarni/Forad.

## Log
- 23:27 UTC lease claimed; sources converted; MM9 reference renders; Codex HD master run 1 started. Credits 0.
- 23:33 UTC Smart Topology (5). 23:52 UTC body + head 4K retextures (10 + 10).
- 00:05-00:30 UTC compose, face pass (eye relax, eyeballs dropped, Codex eye repaint, hairline), wrist/cuff fixes, sleeve gate 0.
- 00:31 UTC first install + binding + tables; regression: binding PASS, 192 passed, 1 known out05.
- 00:55 UTC final install (floor ops for Sit/DeadStatic, chin/tear touch); viewer r2-20261102 check 14 clips 0 failed.
- 01:05 UTC lease released.
- 2026-11-02 ear-sweep fix (owner ear-sweep-fix): fix_ear_try.py, rebuild, install r3, viewer r3-20261102 check 14 clips 0 failed.
