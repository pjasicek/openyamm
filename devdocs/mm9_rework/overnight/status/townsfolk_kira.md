# Unique Kira the Cold — status

- Project: `level_generation/creatures/mm9_kira_claude/` (README is the record), lease `mm9:kira`, owner claude-kira-worker.
- Row: MONSTERS.txt 251 "Kira the Cold" (KIRA.abc, skin KIRAPLATE, NPCbase.scr, Scale 1). Placements: Thronheim City `KiratheCold` x2
  (`NPC239.scr` in her hall; `ARG_Kira.scr` the Argument cutscene), Afterworld `KiratheCold0` (hidden, Six Fires); corpse props `Kira`
  (PropAnim `Static_die1`) in Afterworld and Yorwick.
- Phase: **done** (installed, bound, gates run, sheets read, README written).
- Credits: **25 / 60** (Smart Topology 5, body retexture 4K 10, head retexture 4K 10; backup account, no retries).
- Installed: `assets_source/worlds/mm9/models/mm9_kira.glb` (sha256 22841603a44f...), review root refreshed.
- Binding: row 251 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 255), tables regenerated (id 9251), `actors.yml` block
  `mm9_kira_claude` (`MM9 251 Kira the Cold`). Map placement left to the orchestrator (rebuilt maps still place 255).
- Skeleton/clips: KIRA.abc's own Bip01 skeleton and clips (no shared library): stand, walk, run, fidget1, wattack1, wince1, authored Death
  (wince2 recoil into static_die1), Dead; script clips sit, Applause, ten Sc2_* (ARG_Kira.scr), static_die1.
- Shield: none. MM9 never attaches KIRASHIELD to her (the quest item lying in Thronheim, `mm9_kirashield`); see README. Sword (cutscene only) not built.
- Gates: arm/hand 0 frames > 1 cm in all 21 clips; jitter 0 fails; glove inside vambrace 0.0 mm every clip (3 cm past the wrist the gate
  reads up to 50 mm because the cuff bends with the hand; looked at, no poke); legs through skirt 0 in role clips, seated cutscene clips
  <= 0.4 cm, Sc2_KIRA20_23 1.2 cm; floor ok; winding 0; flat 0.00; bones 0 stretching; texture body 59.6 % / head 56.2 %; detached 2
  (tasset 4 cm in Sc2_KIRA12, skirt off the legs in Running). Regression: mm9 binding PASS (182 descriptors on 75 models, 0 failed),
  suite 192 passed, 1 known out05 failure.
- Viewer `r7-20261102`, check 0 errors. No game run made.
- No background processes, no Chrome left. Lease released 2026-11-02.

## r8 fix pass (2026-11-02, owner kira-fix, user review notes)

- Phase: **done** (installed r8, gates and regression run, sheets read, README "r8 fixes" written). Credits: 0 (no Meshy, no Codex).
- Jaw/cheek shear in Fidget f55 (and every head-turning clip): the lower face carried Neck/Head_h weight (chin-nape plane through the
  chin, relaxed neck band). `face_rigid.py`: jaw-following boundary; lower face 0.00 mm off the Head in every clip (r7 up to 83 mm).
- Chin smudge: UVs of midline slivers on the atlas corner (`uv_slivers.py`), folded chin-rim fans and an unwelded lip twin
  (`chin_fold.py`), grey paint specks under the lower lip (`chin_paint.py`). A small V notch at the lower lip's centre remains.
- Hands: `finger_pose.py` replaces finger_alias (flexion-only curl from MM9's mitten, fingers together, relaxed knuckle curl);
  `armout_jobs.txt` + Sc2_Kira9b R 4 deg.
- Wrist hole: `wrist_fill.py` (glove flares to 0.9 x the vambrace wall under the rim and takes its weights, rim cap ring);
  `subdiv_fingers.py` (one smooth cut of the fingers, +3,436 triangles; LOD0 16,160). Finger texture streaks are paint: not fixed.
- Installed r8 sha256 0afc4ec2a1e9... Rollback: `work/mm9_kira_r7_rollback.glb`. Viewer `r8-20261102` (r7 kept as `kira_r7`), check
  42 switches 0 errors. Gates `review/gates_r8/`: arm/hand 0 frames > 1 cm (worst 0.9 cm), jitter 0, glove in vambrace 0.2 mm, floor ok,
  winding 0, flat 0.00; collapse counts higher in the curled fingers (inside fists), lower at neck/head.
- Regression (r8 installed): mm9_actor_models_build_every_binding PASS (187 descriptors on 80 models, 0 failed); suite 192 passed, 1 known out05 failure. No Chrome left; lease kira-fix released 2026-11-02.
