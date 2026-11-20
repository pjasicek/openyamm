# MM9 monsters: second-run handoff (stopped 2026-11-01, 99 % weekly quota)

The second run continued [MONSTERS_HANDOFF.md](MONSTERS_HANDOFF.md). Every event, with agent ids, is in
[monsters_ledger.md](monsters_ledger.md) under "## Second run". Each body's own state is in `status/monster_<body>.md`
and its project README. The shared agent rules are in [RUN2_COMMON.md](RUN2_COMMON.md), and they still
apply.

The user's review page is `level_generation/creatures/claude_shared/mm9_overview/index.html`. It is served at
`http://127.0.0.1:8912/...` by `python3 -m http.server 8912 --bind 127.0.0.1` from the repository root.

## State at the stop

- No agent is running. The three that were running were stopped by the orchestrator, and their workspace leases were
  released (`output/creature_3d_locks/`).
- Meshy backup balance: 3860. The stop line is 3785, so 75 credits are usable.
- Regression `mm9_actor_models_build_every_binding --world mm9`: last green run at 158 descriptors on 65 models.
  The whole actors suite has 2 failures that are not ours: the MM6 ogre's Hit blend, and out05 "could not load
  gameplay data". The user has not asked for them to be fixed.
- Nothing is staged or committed.

## Done this run

- **Dropped clips:** every installed MM9 body now carries every MM9 clip. Clip groups A, B and C restored them; group D
  grafted them into the approved imp, skeleton warrior and lich, and gave annud and forad only the clips their scripts
  play. Byte checks passed.
- **Approved by the user, 2026-11-01** (marked ok on the overview page):

  | Body | Build | User's words |
  |---|---|---|
  | Njam | r14 | "ok i guess" |
  | Yanmir | r5 | "good" |
  | Lich King | r13 | "good" |
  | Colloidal Warrior | r9 | "ok" |
- **Follow-ups on bodies the user had already approved:** dwarf r18, half-orc (dookmilitia) r19, lizard-orc r18 and
  bigfoot r9. The remaining gate failures are in the ledger and in each body's `rework:` note on the overview page.

## Open: three bodies, from the user's review of 2026-11-01

### Giant (`mm9_giant_claude`, r21 installed, 35 credits in total)

The user said: "the hammer isn't properly held by the hands, like it's not in the palms but intersects", and "the
hammer itself needs better texture/model". r21 has a palm grip with wrapped fingers (`fist_giant.py solve2`,
`grip_gate.py`) and a new Meshy mallet made from a Codex HD master (`references_mallet/`).

The orchestrator sent it back for the items below. The agent was stopped right after it claimed the lease, so none of
them are done:

1. **Standing frame 0:** the left fingers are open and spread (sheet_mallet `h3_M_grip`). Check the wrap on every frame
   and across the loop seam of Standing, Walking, Running and Aware.
2. **Fidget:** the left hand is 6 cm in the body for 58 frames. Release it the way AttackMelee does, and regrip when the
   hand can reach the shaft.
3. **Corpse:** the mallet head is 4.2 cm into the left thigh in Dead and at the end of Death.
4. **Jitter:** 5 clips fail (Fidget2, Taunt, Aware and AttackMelee2 from the left-grip IK, plus the AttackMelee R upper
   arm).
5. **Tier B's "steel" mallet head** reads as grey wood. Try a region mask with a metal look, without a new paint.

Do these with 0 credits. Then reshoot the grip sheets for both tiers at several frames, including frame 0, and read
the strips and close-ups that were rebuilt on r21.

### Ebora / Concubine (`mm9_ebora_claude`)

The user said: "needs better head texture". The head pass (sha ac7581618509) repainted the face from Codex renders of
our own head clay (`references_head/`, `project_head.py`, landmarks, 2K head). The orchestrator read it: a clear step
up.

The second fix (hairline stub, nose streak, ear cards) was stopped mid-run:

- `mm9_ebora.glb` was **reinstalled at 17:14 by that fix**, so the installed build is unverified. Its regression was
  still running when the agent was stopped.
- **First step on resume:** rerun the gates and the regression on the installed GLB, reshoot `review/sheet_head_full.png`,
  and read it.
- The items it was fixing:
  1. The dark rectangular stub at the centre of the hairline, on every tier.
  2. The bright streak down the nose bridge.
  3. The pointed ears, which read as flat pale cards in the quarter views.

### Lesser Demon (`mm9_stage1demon_claude`, r10 installed, 30 credits)

The user said: "check the neck". Under the jaw sits a dark, featureless bulge that meets the chest in a hard crease.
The user approved a new agent for this.

The neck pass was stopped part way, and **nothing is installed: r10 is still the live build.** What was found and
done:

- **Cause found:** the head shell is pushed into a flat, capped wall. The buried plug and the wall show when the head
  lifts or the jaw drops.
- **Work in progress:**
  - `scripts/neck_pass.sh` runs `neck_weld.py`, `neck_weights.py`, `neck_paint.py` and `grade_regions.py`, and writes
    `work/uv_v4.blend`.
  - Rebuild with `MASTER=work/uv_v4.blend scripts/rebuild.sh`.
  - The r10 export is kept as `work/neck/r10_export.glb`, and the untouched pass-2 textures are in `work/neck_in/`.
  - The agent had just started the head-side rim (the bigfoot `neck_rim.py` approach).
- **Goal:** the jaw underside flows through a short throat into the chest with the scale paint, and the gunmetal
  collar plates wrap round the sides of the neck base, as in MM9.
- **Cap:** 10 credits, only if paint and geometry are not enough.

## After these three

Show the user the Giant, Ebora and the Lesser Demon again on the overview page. Each has a `rework:` note there that
should be replaced by its result.

Bodies with failures recorded but accepted are listed in the ledger. Nothing else is queued from the user's original
request: the four failing bodies were finished, the seven new bodies were built, and no clips are dropped.
