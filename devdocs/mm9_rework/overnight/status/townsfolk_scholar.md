# MM9 Bembridge Scholars (scholar.abc rows 274 Scholar / 275 Master Scholar) — owner igrid-scholar-agent

Project `level_generation/creatures/mm9_scholar_claude/`, lease `mm9:scholar` claimed 2026-11-02 18:56 UTC.

- 18:56 lease claimed (work starts after Igrid). meshcmp: 6-12 cm from Forad, PeasantM8, Markel; 94-node skeleton: new body.
- Credits: 0 / 50.
- 20:00-21:40 (interleaved with Igrid) Codex HD masters gated (`review/masters_vs_mm9.png`), two-face head turnarounds (`review/head_masters.png`:
  A ginger ~40, B white ~70). Smart Topology 5 cr (backup 2475 before). Route: the Monk's (Bip01 robe on eight cloth chains, beard/hair chains)
  with the Wyrde/Igrid scripts; SCHOLAR.abc's own clips (no script plays any: no DAT object places the Scholars in the extracted maps; rows
  run basecrawl.scr): Standing stand, Walking walk, Running run, Fidget fidget1, AttackMelee Hattack1 (impact 0.35 s), Hit wince1, Death die1,
  Dead, script clip Cower. Assembled (`assemble_sc.py`), clay clips OK, UVs (`uv_sc.py`, never re-run): body 64.0 %, head set 60.5 %.
- 21:45 Retextures 4K: body 10 (backup 2450 before), head A 10 (2440), head B 10 (2430). Credits 35 / 50.
- 22:10 Paints composed; fixes: beard ghost on robe/stole -> cloth, hands clean skin, the ear painted on the hair -> hair, ear tips (poking
  through openings in the hair shell) folded flat under the hair (positions only); tier ramps (robe) from MM9's scholar1/scholar3 blue texels;
  one head colour per tier. Viewer face sheets f1-f6 (both tiers). Gates r1: jitter 0, arm/hand only Fidget (hand on the beard / hip), sleeve
  poke 0 except Death L 22 mm 1 frame; robe gate: the 27 cm Meshy boots pushed through the robe -> boots compressed to low shoes: Walking 49 ->
  0 frames; inner sleeve caps (hollow bell sleeves showed the stub's cut end). See-through r1 running.
- 22:50 Robe ramps fixed (the RGBA mask had lost its R channel in the resize: tier B showed tier A's navy). Linings (rest + posed back faces,
  robe hem band, the hand stubs at the wrist). Inner sleeve caps tried and dropped (they trapped MM9's folded-back Fidget hand inside the
  closed sleeve); forearm stubs stretched x2 into the sleeve instead; Fidget left wrist bend clamped 114 -> 60 deg (the wrist skin tore into
  a dark wedge). See-through r3: torso <= 132 px (Death), head <= 115 (Death), sleeves <= 31. Final build + see-through r4 running.
- 23:40 INSTALLED `mm9_scholar.glb` (r13, sha d07c5ec8bfcd), bound `MM9 274 Scholar` (sc_a) and `MM9 275 Master Scholar` (sc_b) under the flock,
  rows 274/275 in mm9_npc_actor_rows.tsv (fallbacks 292/294), body overrides + tables regenerated (9274/9275: height 184, radius 31). Binding
  regression PASS (248 on 110). Floor ok. Viewer r13 check 0 errors. Credits 35 / 50 (backup 2370 at the end). Open: Fidget L hand on the
  stole (gate 35 f / 5.3 cm with linings, 5 f / 1.5 cm without), shoes under the hem in Cower/Running/Death, Master Scholar reads stern,
  faint ear outline on tier A's hair. README has the gates. Lease released.
- 23:50 Coordinator review round: lease re-claimed (jaw gaps tier B, B's mouth, legs through robe, Fidget L gate check).
- 2026-11-04 06:20 UTC Finishing job (owner igrid-scholar-finish-20261104): lease mm9:scholar claimed. Installed `mm9_scholar.glb` = export
  (sha 716421a7bd93, r21 build of 2026-11-02 23:49 CET, README still names r13 d07c5ec8bfcd); gates after it: arm/hand (Fidget L 24 f 5.5 cm),
  robe (Death 5/32 2.5 cm; Running, Cower 0), sleeve poke (Death L 22 mm 2 f), see-through r5, regression PASS. Meshy: no pending job, backup 2370.
  Face f16 B read zoomed: still a full pink lower lip with level/down corners under the moustache (pout), a bare chin patch where MM9's beard
  covers the chin, grey patches beside the mouth from the moustache fix.
- 06:45 UTC Tier B lower face (`head_fix_sc.py` 1e LOWERA): tier A's facial-hair layout on the same face shell (moustache over the lips,
  beard from the lower lip down, jaw beard) carried onto B in B's white beard ramp, B's skin elsewhere; 1d off; beard-sheet top skin
  texels -> beard. Face sheets f22 (both tiers) read: B now a short white moustache over a slight smile, chin bearded like MM9; no jaw gaps.
  Death legs: `legs_hide.py` ported with Igrid's pull + a separate pull window: Death 5/32 2.5 cm -> 2/32 2.4 cm (0.17-0.21 s, the shins as
  he tips back). Fidget L proof (`work/fidproof/`): same rig and clips, arm gate without linings 0 frames > 1 cm (0.9 cm), with linings
  24 frames 5.5 cm: the lining twins confuse the gate.
- 08:10 UTC r22 INSTALLED (`mm9_scholar.glb` sha 176c7de25696; r21 kept as `work/lf/mm9_scholar_r21_installed.glb`). Also `head_fix_sc.py` 1f:
  the hidden head-shell ears in hair colour and the hair-sheet ear fill with strand detail (tier A's ear outline nearly gone). The rig
  re-run gave a byte-identical half.glb, so the r21 LODs were reused (`scripts/tail_sc.sh`, no Blender). Gates r22: arm/hand 0 except
  Fidget L 24 f 5.5 cm (0 f without linings: gate artefact, proven); robe 0 except Death 2/32 2.4 cm (0.17-0.21 s); sleeve poke 0 except
  Death L 22 mm 2 f; see-through r6 torso <= 32 / head <= 22 except Death torso 132 / head 115 px (a real gap under the beard at the collar
  at 0.5-0.6 s, not fixed); jitter 0; texture 64.0 / 60.5 %; floor ok; viewer check 18 switches 0 errors; regression PASS 248 on 110.
  Credits this round 0 (35 / 55 lease budget). Backup 2275 at the end. README updated. Lease released.
- 2026-11-04: user approved ("scholar ok"), r22.
