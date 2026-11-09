# MM9 Sigmund the Stressed — status (owner dboy-sigmund-agent)

- Project: `level_generation/creatures/mm9_sigmund_claude/`, lease `mm9:sigmund`.
- Row 247 (unique, skin SIGMUND). SIGMUND.abc lists `sigmund_child.ABC` as its LithTech child model (stand, fidget, walk on the
  same 49-joint skeleton): included as the clip source. Skeleton: an `FHP` (female-human-peasant naming) biped with hair and
  mail-skirt bones (XCOM_skirt, x*), not PeasantMale.
- Own clips: Sit, Agree, Applause, Sc2_Sigmund1b/1c/3b, static_die1 (+ bind `sigmond`).
- Phase: **installed and bound** (2026-11-02 ~22:00). `assets_source/worlds/mm9/models/mm9_sigmund.glb` (sha256 4846e11dce17...);
  `MM9 247 Sigmund the Stressed` (actors.yml block mm9_sigmund_claude, script clips sit/agree/applause/sc2_sigmund1b/1c/3b/static_die1);
  row 247 -> 403 in mm9_npc_actor_rows.tsv; tables regenerated; body override 174 / 31 (MM9 rule).
- Gates: arm/hand 0 frames > 1 cm in all 15 clips; jitter 0; see-through worst 10 px (head under the hair in Death), sleeves <= 4,
  torso 2, boots 2; sleeve poke 0 mm (no rim found on the bracers); winding 0; bones 0; flat 0.00; floor ok; LOD0 13,236; body atlas
  65.1 %, head set 39.2 %; viewer 15 switches 0 errors; `mm9_actor_models_build_every_binding` PASS (246 on 109). Detached audit
  reports the two boot shells (4.7 mm off the calf: a boot around the leg).
- Credits: 25 / 50 (Smart Topology 5, body 4K 10, head 4K 10); backup 2640 -> 2520 over both models' jobs (shared).
- Open: brows heavy/worried as painted; seated cutscene clips sit on an invisible chair; retargeted run/attack/hit/death keep the
  hair and skirt joints at rest. Map placement left to the orchestrator.
