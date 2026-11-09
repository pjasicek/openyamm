# Townsfolk PeasantHOM1 (half-orc man) — status: installed and bound, 2026-11-02 ~00:05 UTC

Project `level_generation/creatures/mm9_peasanthom1_claude/` (README has route, rebuild, gates, deviations, binding plan).
Rows 57 Commoner (PeasantHOM1a), 58 Town (PeasantHOM1b), 60 Prisoner (PeasantHOM1a); row 59 is PeasantHOM2 (not this body).
Skeleton: the half-orc male PEASANTHOM1 (35 joints, Pelvis root) with the PEASANTHOMALE library (11 clips, all used);
no earlier project had retargeted it.

- Installed `assets_source/worlds/mm9/models/mm9_phom1.glb` (sha256 927bd9f25682d86b...), LOD0 7,853 tris; tiers
  `phom1_a` (57, 60), `phom1_b` (58) by region masks + ramps (body: vest, sleeves, trousers, border; head: hair, collar).
- Descriptors `MM9 57 Commoner` / `MM9 58 Town` / `MM9 60 Prisoner` (rows in `mm9_npc_actor_rows.tsv` with stand-ins 439/442/447,
  tables regenerated 9057/9058/9060, actors.yml bound under the flock). Map placements still use the stand-ins (binding plan in README).
- Clips: Standing, Walking, Running, Fidget, Talk (conv1), AttackMelee (hattack1, impact 0.5 s), Hit, Death, Dead, Cower,
  CowerStart, CowerStop (NPCbase/BaseRun.inc, ArmWrestle.scr).
- Gates: arm/hand 0 frames > 1 cm in every clip (Fidget L 0.8 cm after arm_clear + new smooth_correction.py; raw 6.0 cm);
  jitter 0 fails; floor OK (walk -1.6..+1.5); winding 0; bones 0; detached 0; flat 0; body atlas 60.2 % / spread 1.07 /
  fragments 0.1 %; head set 46.8 % / spread 3.11 (hands vs head, by design) / fragments 3.1 %; viewer 24 switches 0 errors;
  `mm9_actor_models_build_every_binding` PASS (181 on 74 models); full actors suite 192 pass, 1 known out05 fail.
- Fringe edge: row 58's pale band fixed by head paint (hairline_fix.py) + hair mask; a faint lighter rim remains at fringe zoom.
- Meshy: 25 credits (Smart Topology 5, body 4K 10, head 4K 10). Codex: 3 runs (masters 1, 2, head).
- Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthom1_claude/review/viewer/ (v15-20261101).
- Not checked: playback at speed, in game, LODs by eye, tier B clips beyond Standing.


## Wrist and sleeve fix (orchestrator follow-up, 2026-11-02)
- Lease re-claimed (budget 5); Meshy 0 credits. Rollback of the first install in `work/rollback_v1/`.
- Salmon flare at the cuffs: cuff rim trimmed 2.5 cm and the turned-in lining removed (`cuff_fix.py`), stubs tucked inside the
  sleeves (`sleeve_tuck.py`, M7's), skin/peach paint on the cuff cloth repainted from the cloth (`sleeve_paint_fix.py`, 4,067 texels).
- The "two dark triangles" were see-through holes in Meshy's sleeve mesh (4 loops on the forearms): filled with cloth faces
  (`sleeve_holes.py`). Hands were blotchy with dark nails too: `hand_clean.py`.
- `sleeve_poke_gate.py`: 0 frames over tolerance in all 12 clips, both arms (worst Death L 0.2 mm, sub-tolerance).
  Arm/hand, jitter, floor, winding, bones, detached, flat, texture quality, viewer: all pass (README wrist section).
- Installed sha256 3ec43eb07b106d8b...; sheets `review/sheet_wrist_before_after_{L,R}.png`, `review/sleeve_marks_before_after.png`.
- Full actors suite on the final install: 192 pass, 1 known out05 fail; mm9_actor_models_build_every_binding PASS (181 on 74).
- Lease released.
2026-11-02 ear-sweep fix (owner ear-sweep-fix): the outline round each sideburn came from hairline_fix.py (not the Meshy paint);
MM9 has the sideburn (hair bowl down in front of the ears), so it stays. `scripts/fix_sideburn_phom1.py colour` (hairline_fix
on the fringe only) + `mask` (row 58 hair mask grown over the sideburn border, no brown frame). Only the head colour and head
region mask changed (0.000 mm in every clip). Installed sha 0692f374972b17f5, rollback work/installed_preear.glb. Viewer
v16-20261102, check 24 switches 0 failed. Sheet review/sheet_ear_before_after.png.
