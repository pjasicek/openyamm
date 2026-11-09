# Unique Sven Svenssen — status

- Project `level_generation/creatures/mm9_sven_claude/`, lease `mm9:sven` (owner claude-townsfolk-sven), budget 60.
- Row: MONSTERS.txt 249 "Sven Svenssen" (Sven.abc, skin sven.dtx, NPCbase.scr, BaseName PeasantMale, Scale 1.25).

## Log
- 23:46 UTC lease claimed; reading references. Credits 0 (backup 3400).
- 00:01 UTC placements: Afterworld `SvenSvenssen0` (no script -> NPCbase, LoopAnim Cower), Arslegard `SvenSvenssen0` (NPC3.scr, no
  animation), The Arena `SvenArena` (SvenArena.scr: walkto, PlayAnim Bless, BaseMelee), Thronheim `Sven` + `SvenProp` on
  **SVEN_ARG.abc** (ARG_Sven.scr: loopanim Sitting, Agree, Applause with Clap keys; PropAnim Sit). SVEN_ARG = the same Sven
  piece and skin plus a ChairPlain chair on its own Bone01, seated bind: covered by carrying its clips (Sit, Agree, Applause).
  The Afterworld/Yorwick `Sven0..26` props are ClanSoldier corpses, not this body; Thjorgard `Sven` is a PeasantMale.
  Skeleton: SVEN.abc = PeasantMale 45 joints + own clips; PeasantMale library from mm9_peasantm1_claude.
- 00:10 UTC HD masters 00-04 accepted (Codex 2 runs, halo removed). Smart Topology body_smart_v1 done (5 cr, backup 3375 before).
  Fit (two sparse-MM9-mesh fixes: centre_band 0.07, Spine3 interpolated; rig reset from SVEN.abc's posed first clip), reduce
  14,951 -> 8,256, MPFB hands at the bracers, head split (cut 0.62). All 13 roles retarget (clips_mm9 `rest_from`: the ARG
  clips use SVEN.abc's standing bind). UVs and Codex head turnaround running. Credits 5.
- 01:15 UTC HD head turnaround accepted; UVs (body atlas 60.8 %, head 54.6 %); body and head 4K retextures (10 + 10, backup 3350 ->
  3340 before). Credits 25 (final unless a rework needs more).
- 02:30 UTC face: Meshy's head read stern (knitted brows, frown furrows, pale full lips, grey chin streak): Codex repaint of
  brows/eyes and mouth/chin by landmarks (warp_face.py undoes Codex's 6-12 px drift, project_face.py with two windows); hands
  hand_clean.py. Wrists: bracer made rigid (bracer_rigid.py), stub tucked (sleeve_tuck.py, reweight from 1.4 cm past the joint),
  toothed bracer rim cut to a clean ring (cuff_trim.py with a long-face fix) -> sleeve_poke 0 mm in every clip. Applause clap
  and Talk R hip: eased constant abductions (clap_spread.py), no jitter. Accessories copy their carrier weights (detached).
- 03:05 UTC built and installed (assets_source/worlds/mm9/models/mm9_sven.glb, LOD0 8,405). Bound under the flock: row 249 -> 520
  in mm9_npc_actor_rows.tsv, tables regenerated (9249 `MM9 249 Sven Svenssen`), actors.yml block mm9_sven_claude (scale 125).
  Gates: arm/hand 0 frames > 1 cm every clip (Applause 0.9 cm palms), jitter 0 fails, sleeve/bracer poke 0 mm all 14 clips,
  floor ok, winding 0, bones 0, detached 0, flat 0.00, body atlas 60.7 %. Viewer 14 switches 0 errors. Belt studs dropped,
  bracer upper-rim skin wedges repainted (texture-only rebuild, reinstall pending regression). README written.
- 03:40 UTC final: regression actors --world mm9 passed 192 / failed 1 (known out05), mm9_actor_models_build_every_binding PASS;
  texture-only reinstall (sha256 3e303710a1f4...) then binding case PASS again (186 descriptors on 79 models), floor ok, viewer
  r2-20261102 14 switches 0 errors. Map placement left to the orchestrator (README "Binding plan"; Thronheim's seated Sven needs a
  chair decoration). SVEN_ARG covered (same body + chair; its Sitting/Agree/Applause clips carried).
- Phase: **done**. Credits **25 / 60**. README is the record. Lease released.
