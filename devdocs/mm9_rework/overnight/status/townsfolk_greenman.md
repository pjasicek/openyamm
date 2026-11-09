# Green Man (MM9 row 266, GREENMAN.abc) — status

Worker greenman-20261104, Job 6 of `FINISH_BRIEF_20261104.md`. Project `level_generation/creatures/mm9_greenman_claude/`,
lease `mm9:greenman` (claimed 2026-11-04 07:07 UTC).

- 07:07 lease claimed; reading the MM9 model, scripts and mesh comparison.
- 07:15 `mm9_meshcmp.py` greenman vs 38 built MM9 humanoid bodies: nearest PeasantHOM1 (head p90 10 cm, torso 49, arms 36,
  legs 37 cm after the rigid shift), every other 14-110 cm; skeleton 56 joints (Bip01 biped with five three-joint fingers per
  hand, staff bone Bone01, socket ButterFly) matches none. **New body** (cap 60), humanoid route. 2.07 m to the head joint.
- GREENMAN.abc clips: stand, fidget1, fidget2, walk only (no child model). Placed once: Frosgard `GreenMan0` (NPC221.scr:
  BaseWander, Rude -> Druid promotion; GreenMan.scr: no wince). BaseName PeasantMale: Running/AttackMelee/Hit/Death from the
  PeasantMale library retargeted (`retarget_mm9.py` + root bases, leg ratio 1.654, staff bone follows the R hand), sheet
  `review/retarget/sheet_retarget.png`.
- 08:15 Codex 00 master run 1 good identity, arms too low for the near-T bind pose; run 1b (pose correction) running.
- 08:20 masters: 00 (run 1b, near-T bind pose), 01-04 (run 2) selected, halos cleaned; head turnaround (4 views) good,
  calm warm face. Smart Topology 15k (5 cr, backup 2275 -> 2270): good body, face, leaf hood/beard/kilt as ~600 leaf parts,
  a crown of 9 branches. `sym_meshy.py HEADF=0.82` (Meshy legs stood 11 cm apart in depth); `fit_rig.py` scale by the arm
  underside height (2.62 m incl. crown), legs at our slice centres, Neck/Head pivots moved up 8/14 cm to our neck (MM9's head
  joint sits at shoulder height); reduce 15.5k -> 9.6k; MPFB hands aligned to MM9's hand frame; eyes filled, cups dropped;
  wrist taper (`wrist_blend.py`). Body UV layout (uv_atlas) running.
- 08:40-09:10 body + head 4K retextures (20 cr; backup 2270 -> 2250, total 25 cr). Staff: smooth gnarled tube along MM9's
  staff (Bone01, `staff_build.py`), Codex bark swatch in the head set's free strip; `staff_follow.py` re-keys Bone01 from
  our R hand in every clip. Paint chain (`paint_chain.sh`): body leaves toned to the head set's (`leaf_tone.py`: Meshy's
  body paint was a harsh lime/black camouflage), two straight Meshy paint lines removed from the face (`face_lines.py`),
  per-leaf tone jitter against the mirrored Rorschach hood (`leaf_jitter.py`), twisted-vine wrist bracelets over the hand
  graft seams (`wrist_vine.py`), hands graded to the green forearm. Root offset (MM9 keys Bip01 at standing height),
  closed thin leaves turned outward (`fix_winding.py`: 0 inverted). Viewer r3: face calm/warm, eyes open, one nose, closed
  mouth. Gates running.
- 09:10-09:50 gates and fixes: staff thinner (2.9 cm, worn grip, no knots there) and moved into the fist (`grip_solve.py`),
  R finger curl 85/60 % of MM9's; left shoulder abduction 5 deg on Standing/Fidget (hand into the leaf kilt 3.9 cm -> 0);
  Death re-grounded smoothly (`death_ground.py`: the retargeted fall hovered 0.33 m and sank 0.51 m); Hit raised 4.5 cm.
  Installed `mm9_greenman.glb`, bound `MM9 266 Green Man` (row 266 -> 451), body override 230/51 written by
  `mm9_monster_bodies.py --write-overrides`, tables regenerated, binding regression PASS (251 descriptors on 113 models).
  Open: Walking toes dip 10 cm at push-off (our feet longer than MM9's) -> grounding bobs (lift 6.8 cm, jitter R 2.61 mm/f2 vs 2.0).
  See-through gate (step 6) and detached audit running; face sheets next.
- 10:40 final build installed (`assets_source/worlds/mm9/models/mm9_greenman.glb`, sha256 3042778aff49...): body-shell holes under
  the kilt/mantle filled at export (see-through r2 646 px -> r3 178 px max), leaves follow the skin under them
  (`accessory_weights.py`), blue specks removed, walk `--raise` + 0.10 s smoothing (jitter passes; floor audit walk lift
  +8.3 units FAILS, tolerance 2.5). Binding regression PASS (252 on 114 models). Viewer `final-20261104`, check 9/0/0.
  README has every gate number. Final detached audit running; then lease release.
- 11:30 final: 17 floating slivers dropped (`drop_floaters.py`), reinstalled sha256 9f1a7c7bb473..., gates rerun (README
  "Checks"): arm/hand 0 except Fidget2 L 6.0 cm (beard stroke) and 1.9 cm at frame 0 of three one-shots; staff grip 2.1-2.6 cm;
  jitter 0 fails (Death vs its grounded root); floor walk +8.3 FAIL; see-through max 178 px (leaf edges); detached 87 parts,
  worst 4.4 cm; winding 0; regression PASS; viewer final-20261104b 9/0/0. Lease released. DONE (with the open points above).
- 2026-11-04 second pass (orchestrator pre-screen): lease re-claimed; walk hop (feet), detached leaves, colour toward MM9, lilac specks.
- pass 2 done (0 credits): legs re-shaped onto MM9's knee/ankle line (`leg_align.py`) -> walk floor -1.9..+1.7 ok with no floor op,
  jitter 0 in Walking/Running; leaves take nearest-face skin weights + 43 floating scraps dropped -> detached 16 parts > 1 cm
  (was 39), worst 3.0 cm (was 4.4) - NOT 0; colour graded toward MM9 (skin olive and darker, leaves moss); lilac specks healed.
  Reinstalled (sha256 72e57b0e741c...), regression PASS, viewer pass2-final-20261104 9/0/0. Lease released.
- 2026-11-04: user approved ("green man ok"), pass 2.
