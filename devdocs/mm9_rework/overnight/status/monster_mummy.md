# monster_mummy status

- Phase: HD masters (Codex). Lease owner `overnight-mummy`, token 0e9e7aaaf86748e995603f365300a6b0, project level_generation/creatures/mm9_mummy_claude
- Credits 40/40 committed (body ST 5, head ST 5, retexture A/B/C 30). No more Meshy.
- Facts: MUMMY.abc, 32 joints (Bip01 + Bone01-02 arm strip, Bone04-08 long hip-to-wrist band, Bone24 thigh strip), no finger bones, MM9 hands differ (R mitten, L thumb + 3). Skins differ in design (A all wrapped + face; B torn, brown flesh, skull; C dark flesh, skull).
- Plan: build in raw (mirrored) ABC space, `mirror_glb.py` last. Clean tight-wrapped Meshy body; loose strips are our own ribbons on MM9's bones with a Codex swatch in reserved atlas space. Tier A own colour image, B/C share (doc: separate base colour allowed for a different pattern/face, reason in README).

## 2026-10-30 ~23:00
- Credits 40/40 committed (body ST 5, head ST 5, retexture A/B/C 30). No more Meshy.
- Mesh: `work/joined.blend` from scripts step1_clean, step2_sym, step3_head, step4_join (symmetric A pose, head grafted over a neck tube).
- Paint plan: bodies 3 Meshy 4K retextures (30 cr), heads free projection bake of Codex busts. Per-tier images, reason: tiers differ in pattern and face.
- Next: rig (IBM bind in A pose, clips as MM9 local rotations), strips, UVs, paint, runtime.

## Orchestrator note (tiers)
Per-tier images are a deviation: use the committed paints, keep colour-only differences out of the images (ramps or material factors), record why and the extra memory in README + final report, confirm the runtime binds them per tier. Credits 40/40 spent, no Meshy left.
Layout: paint layout L1 (use 29 %, my mistake, seen after submit) -> runtime layout L2 by chart repack and transfer from the 4K paints, no repaint.

## 23:25
- Credits 40/40. Built, not installed yet. `scripts/rebuild.sh` works end to end; viewer r3. Body grain replaced by linen (`scripts/linen.py`), band is a rope solve (`scripts/band_sim.py`), heads are Codex projections (`scripts/head_project.py`).
- Next: final sheets, README, release lease. Installed; binding in actors.yml (cast clip added after the regression and game log showed Mummy C refused).

## Done 2026-10-30 23:55
Installed, bound, regression PASS, in game 3 tiers, README written, review root refreshed. Lease released. Credits 40/40.

## Second pass (2026-10-31), 0 credits
Orchestrator list: thigh strip on the leg, collapse (half-joint helpers, band with more knots), jitter on corrected clips, head island, frame strips B/C, orientation, band vs torso, playback. Lease re-claimed by overnight-mummy.

## Second pass done 2026-10-31 01:00
Installed (viewer r10-20261031), regression PASS 95 descriptors 0 failed, floor ok, 3 tiers in game, review root refreshed, sheets redone, README updated, lease released. Credits 40/40, none spent this pass.
Still open, with numbers in the README: jitter 5 fails (1.48 deg/f), arm gate AttackMelee 2.2 cm 4 frames, band through chest 9.4 cm 5/37 in AttackMelee2. Second serious attempt: stop here.
