# D-86: MAW in Xeen, MX session 2's five choices (2026-11-21, fourth orchestrator's decider)

All five confirmed. Premise correction: FD-01 Alamar Depths is the story map for M39 (not optional); FD-04's band also
passes 100 (105).

1. Gem gear rung 5.375 for tier 5: confirmed. D-84's 4/5/5/6 are Xeen tiers, not rungs; MM9's `rung_by_quality` maps
   tiers 1–4, 6 to 1 / 2.25 / 3.5 / 4.75 / 6, so Ruby 4.75, Emerald and Sapphire 5.375, Diamond 6 at 1.10/1.10/1.10/1.15.
   MX adds the line "D-84's 4/5/5/6 are tiers; rungs 4.75/5.375/5.375/6" to XEEN_SUPPORT §6.
2. Scripted groups take reserve copies, members hidden at the start never do: confirmed (copies keep their group, so
   SetMonGroupBit moves them with the originals; Xeen's group kill checks are "whole group dead" except DD-11C group 30
   "at least 1", unaffected; ActorIdOe unaffected; Castle Kalindra stops at x1.44, acceptable; MM9's Honks rule).
   MX adds a tester check at phase 7: a script-hidden group, then a refill under MAW Nightmare: copies come back hidden.
3. No reserve on the 15 spawn-point dungeons: confirmed (0–18 placed actors each against 258 spawn points; MAW's group
   sizes grow them as on MM6–MM8; a reserve would grow them twice).
4. No per-map density factors: confirmed (MM9 needed them because its regions held a third to a quarter of MM6–MM8's
   counts; Xeen was built to MM6–MM8 counts; X4 at MAW Nightmare 164, within 120–220).
5. Bands above 100 (XD-18 80–112, FD-01 high 103, FD-04 high 105): confirmed. MAW's code has no clamp (`MawMapLevels`
   doubles; `resolveMawMonsterLevels`, drops, experience, chests unclamped; boss rule switches at 100,
   `MawMonsterRules.cpp:370,381`; experience caps its level term at 100, `:700`); one-native maps pin to the low
   (80/74/65), so the high barely matters. MX corrects XEEN_SUPPORT: FD-01 is a story map whose 103 high is nearly
   cosmetic; FD-04's 105 joins the over-100 list.
