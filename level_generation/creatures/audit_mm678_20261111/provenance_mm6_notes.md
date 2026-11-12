# MM6 3D monster provenance: patterns (2026-11-11)

Companion to `provenance_mm6.csv` (59 models bound under `worlds/mm6/`). Paths below are relative to
`level_generation/creatures/` unless they start with `devdocs/`. The CSV has an extra `shared_passes` column (far-LOD
repair, material pass, texture-pass queue). Shared facts: every MM6 body except aie1, fie1, qfi, rea, sor1 and wel got
the 2026-10-22 far-LOD rebuild (`lod_repair_claude/work/install_list.txt`). **No MM6 model has had the 4K texture
quality pass.** 27 are queued in it: 15 in group A, 12 in group B, plus demon/nobl/rea marked "not a retexture first"
(`claude_shared/texpass_mm678/HANDOFF.md:57-78`).

## Routes
| Rig route | n | Models |
|---|---:|---|
| Source-frame rig with gates (humanoid playbook; Codex batch used it too) | 25 | bar1, gob2, natm, pman_v2, natf, fgt, dru1, ogr, kni, nobl, mer1, mfp, fmp, mep, arc1, dwa1, figc, jak1, lch, lzd, min1, mnk1, sor1, djn, qfi |
| Source-frame hybrid (humanoid upper body + own tail/wings) | 4 | med, gar, wel, ert (Meshy auto-rig converted to 22 bones) |
| Meshy auto-rig, kept (Oct 6-9, before the rig-first route) | 7 | demon, pmn2, gua, cle, thf, ttn, wwf |
| MPFB skeleton/body | 2 | pfem (MPFB skeleton ICP-fitted into a Meshy mesh), fie1 (MPFB body) |
| Own rig, quadruped/creature playbook (heat, rigid or curve weights) | 21 | rat, spi1, bh, bat, bld, wdm, cob, rob1, seas, hyd, ooz, ckt, ske, hrp, drg1, cdr1, rea, drag, aie1, wyrm, gst |

- **Mesh:** 47 are Meshy Smart Topology from Codex HD masters. Four come from restored x2 sprite frames: rat, bat, bld,
  made before the HD-master rule (`mm6_rat_claude/README.md:16`, `mm6_bat_claude/README.md:17`,
  `mm6_bld_claude/README.md:14`), and ert as a user-authorized exception (`mm6_ert_codex/README.md:51`). Demon is Meshy
  image-to-3D from one generated image. wdm, cob, seas and the hyd body are Meshy multi-image-to-3D. rea and aie1 are
  Blender-built. fie1 is an MPFB body.
- **Clips:**
  - About 21 non-humanoids run entirely on authored or procedural clips with no library source: the quadruped/flyer pilots, dragons, serpents, ooze, robot, reactor, elementals, gst and gar's motion. The rat README admits "Procedural motion is generic (no per-frame match to the native sprites)" (`mm6_rat_claude/README.md:37`).
  - Meshy locomotion is still installed on demon, pmn2, gua, cle, thf, ttn, pfem. Pure Mixamo: wwf (Mutant), ske
    (Sword and Shield), wdm, fie1, qfi. The rest mix the local humanoid set and Mixamo.
  - The gait rollout (2026-10-31) appended Walk2/Jog/Run2/Sprint to about 40 MM6 models. Those clips come from the humanoid set or Mixamo for bipeds and are procedural for quadrupeds.
- **Older/cheaper versus later:** built Oct 6-9 with the Meshy auto-rig or pre-HD meshes: demon, rat, bat, bld, pmn2,
  gua, cle, thf, ttn, wwf, ske (several still say "placeholder quality"). The Codex batch (2026-10-12/13,
  `MM6_CODEX_BATCH_GOAL.md`) and Codex-run gar, gst, ert, wel, nobl, fmp follow the playbook, but several went in with
  failing gates (below). Claude rig-first: bar1, gob2, natm, fgt, dru1, ogr, djn, qfi.

## Hands (the main recurring complaint)
- **pfem:** the user called the installed v3 "the body is good, face is terrible", "hands are terrible, especially in standing" (`mm6_pfem_v4_claude/README.md:4`).
  - v4 was rejected; after three arm-fix rounds: "revert the female to original one"
    (`mm6_peasants_fix_claude/README.md:3-8`). The bad hands are still installed.
  - Earlier: v1 MPFB rejected for "limp hands" (`mm6_pfem_claude/README.md:19`); Codex build "not selected or
    installed" (`mm6_pfem_codex/README.md:3`). Four full builds plus one arm-fix series, not six. The v4 README:5
    "Installed" line is stale (the bound GLB is `mm6_pfem.glb`).
- **ttn:** no README says "warped left hand". It records "hands are rigid open hands (no finger chains)" (`mm6_ttn1_claude/README.md:101`, rig at :15).
  - The hook Attack was removed on 2026-10-21, and melee now plays Cast (`mm6_ttn_reduce_claude/README.md:81-84`).
  - The report is Discord OY-27 (2026-10-24, open): "hands look messy in the attack animation" (`devdocs/discord_triage/STATUS.md:146`). The fix proposed there is finger chains or a closed fist (`devdocs/discord_triage/INVESTIGATION_2026-11-07.md:41`).
- **wwf:** "hands are rigid open claws (no finger chains)" (`mm6_wfigt1_claude/README.md:89`), and its status is still "placeholder quality, awaiting user review" (:8).
- **cle:** "I want the hands re-done - both look plain bad" (`mm6_cle_claude/README.md:139`), then MPFB hands.
- **lzd:** bow hand turned outward, not fixed (`mm6_lzd_reduce_claude/README.md:80,86`; `REDUCTION_LEDGER.md:53`).
- **Also:** thf "the hands are mittens" (`mm6_thf_claude/README.md:113`); gob2 four fingers, webs stretch
  (`mm6_gob2_claude/README.md:117-121`); bar1 left fingers frozen, fused thumb (`mm6_bar1_reduce_claude/README.md:86-88`);
  mer1 "hands noted as odd, left as is" (`MM6_CODEX_BATCH_GOAL.md:230`); ske "The right thumb hooks over the grip"
  (`mm6_ske_claude/README.md:56`); gua rigid fist, rear elbow flares (`mm6_gua_claude/README.md:80`).

## Installed despite failing gates or open QA
- **lch:** "Review round 2 is partial, not ready for integration." (`mm6_lch_codex/README.md:3`). Attack hyperextension is 14.657° against a 5° limit (`mm6_lch_codex/HANDOFF.md:32`).
- **mer1:** "Review round 3 staged — QA HOLD." (`mm6_mer1_codex/README.md:3`). Club grip gaps reach 75 mm and body penetration 63.6 mm (`mm6_mer1_codex/HANDOFF.md:110,112`).
- **min1:** "not an all-gates-passing or automatic-install handoff" (`mm6_min1_codex/HANDOFF.md:63`). Thigh weights stretch the arm region 3.0-3.3x (`gait_rollout_20261031/h02/README.md:111`).
- **kni:** the Attack elbow-plane deviation was accepted as-is (`mm6_kni_codex/HANDOFF.md:84`), and an armpit edge stretches 4.01x in Sprint (`mm6_sprint_humanoids_claude/README.md:127`).
- **arc1, figc, mep:** shared runner FAIL (`mm6_arc1_codex/HANDOFF.md:36`); figc Running FAIL and a 4.628x arm edge
  in Death (`mm6_figc_codex/HANDOFF.md:33,332`); mep 208 FAIL rows on the faster Death (`mm6_mep_codex/README.md:9`).
- **mnk1:** the round-4 reduction "remains pending artistic acceptance" (`mm6_mnk1_codex/README.md:18`). Walk2's robe panel stretches (:40), and the walk before that was "a 0.46 m procedural shuffle" (:22).

## Other admitted problems
- **No user acceptance recorded:** fie1, "awaiting user review" (`mm6_fie1_claude/README.md:3`); wyrm, approval "not
  recorded" (`mm6_drr1_claude/README.md:3`) and rev 05 still shows a dark green chest diamond (:137); cob, no verdict
  anywhere; ert, "user artistic acceptance remains separate" (`mm6_ert_codex/README.md:5`).
- **djn:** "I dont like the bracer texture on his left hand, but accept this for now." (`mm6_djn_reduce_claude/README.md:60`).
- **demon:** the attack is "not an exact geometric reconstruction", with four claws instead of three (`mm6_demon_meshy_reference_20261004/attack_animation/README.md:99-100`). Tiers B/C lost their own paint (`mm6_demon_meshy_reference_20261004/regions_20261008/README.md:9`).
- **pmn2:** in the attack the raised arm still touches the hair (`mm6_pmn2_claude/README.md:95,153`).
- **ske:** "Status: placeholder quality" (`mm6_ske_claude/README.md:8`). The pose-audit gate was not run (:57), and the corpse drifts 0.5 m (:59).
- **dru1, cle, gob2:** "Known faults / Remaining faults (placeholder quality)" sections at `mm6_dru1_claude/README.md:177`, `mm6_cle_claude/README.md:236` and `mm6_gob2_claude/README.md:117`.
- **fgt:** revision 3 "artistic acceptance is pending" (`mm6_fgt_claude/README.md:12`). The Standard chase plays outside the gait window by the user's choice (`gait_rollout_20261031/h01/README.md:120`).
- **bar1:** the staged Running correction is not all-pass and still awaits acceptance (`mm6_bar1_claude/TEST_DRIVE.md:545,557`).
- **nobl, rea:** UV stretch p90 8.25 and 7.9 (`claude_shared/texpass_mm678/HANDOFF.md:69`); nobl was "good enough
  accepted" (`mm6_nobl_reduce_claude/README.md:101`).
- Fidgets cut short by the native length: spi1, bld, ske, rob1, ckt (`CLIP_TIMING_AUDIT_20261010.md:75-76`). Discord
  OY-28 (fmp): head-follow aims too high (`devdocs/discord_triage/INVESTIGATION_2026-11-07.md:42`).
- Nothing open recorded for pman_v2, bh, med, drag (apart from the texture-pass queue). Most models went through the
  2026-10-13/14 `*_reduce_claude` pass (`REDUCTION_LEDGER.md:9-57`; figc's body unreduced by the user's choice, :29).
