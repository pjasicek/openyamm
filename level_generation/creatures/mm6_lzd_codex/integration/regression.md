# Proposed orchestrator regression — mm6_lzd_codex

Case name: `mm6_lizard_archer_codex`. No runtime check has been executed by this batch session.

- Worlds/descriptors: MM6, 571/572/573 (`LizardArch A/B/C`); names Lizard Man, Lizard Archer, Lizard Wizard.
- Outdoor: `outd3.odm` (Castle Ironfist), then `outd2.odm` (Bootleg Bay) for natural geography and terrain slopes.
- Indoor: `6d12.blv` on a clear floor, with summoned 571/572/573 and an unobstructed firing lane; select a safe existing test pose.
- Install only `export/mm6_lzd.glb` and `export/mm6_lzd_bow.glb`; merge the sibling `actors.yml` entries.
- Standing body target: 179.199 game units (native alpha height 256 × 0.699997). Accept 175–185 for body-only
  standing height, excluding a raised bow. Combined attack visual height should stay below 220; corpse below 60.
- Camera comparisons: front, side, rear and three-quarter against native `mm6_lzd/native/` frames; verify short tail,
  broad muzzle, left bow hand, quiver, rust/magenta/blue cloth and unchanged dull steel/green scales.
- Exercise all nine roles, walk/run transitions, recovery and held corpse. Check the stride binding at each tier's
  native movement speed (140/150/160), floating or sliding feet, and indoor/outdoor actor bounds/visibility.
- Verify one projectile at the native 0.75 s action endpoint, from `Socket_Arrow`, synchronized to the string snap.
  The binding marker is model-clip time 0.489583333333 s; the shared runtime fits that wind-up to the native action clock.
  The local held arrow appears at 0.373333333 s and hides at 0.489583333333 s; the live projectile is the shared engine projectile.
  Verify no duplicate arrows after interruption, dying, target loss, save/load or an attack-state transition.
- B retains its table fire-arrow attack; C retains its table spell. All tiers bind a distinct Cast that is an exact
  copy of Attack, launching from Socket_Arrow at 0.489583333333 s. Check the single bow-shot spell release and relaxed
  carry transition. There is no palm-right binding. Attack/Cast now last 1.133333333 s, including recovery to the native rest.
- Check horizontal hip carry with the string above the limbs in Standing/Fidget/Walking/Running/Hit, closed grip at all LODs,
  free palm facing the thigh and forward feet (no toe-out). Inspect string continuity through draw/release at slow speed.
- Check the new body/bow LODs at 550/220/88 pixel actor heights. The local distance silhouette gate uses the assembled
  actor; the far bow is mostly subpixel. Verify native lighting, skin/steel brightness and colour-region isolation.
- Inspect the bow attachment at all four LODs, shadows and colour tiers. Arrow and string remain skinned in the body.
  Validate joint lookup and attachment transforms in both world views; no new renderer hook should be necessary.
- Orchestrator runs the MM6 actor suite and affected MM7/MM8 shared actor checks after registry installation;
  verify save/load, no missing textures/normal maps, no animation event regressions and normal startup/map loading.
- Final native-GPU indoor/outdoor captures and performance checks are orchestration work under the batch rules.

Round 5: Death is 2 s and Dead is unchanged. Inspect Hit layer clearance, late Walking frames 36–38, the faster bow release and preserved corpse floor pose. Install through tools/install_model.py --world mm6; never copy directly into assets_dev.

Round 6 Walking only: inspect frames 13–15 and the loop join, symmetric bob and larger arm counter-swing. Stride, floor-contact intent, all other clips and actors.yml remain unchanged. Review/round6 contains the 48 Hz height diagnostics; the shared runner currently has no translation-jitter gate for pelvis/spine/head.
