# Proposed integration checks — not executed by this batch

Install all three round-two GLBs and merge the three descriptor entries in actors.yml together. Their exact hashes
are in ../HANDOFF.md. No game, build or regression suite was run in this project session.

Case: mm6_archer_actor_model_tiers_share_native_height. World mm6, indoor map 6d19.blv; summon
475 Archer / 476 Master Archer / 477 Fire Archer (BArcher A/B/C) on a level floor.
Resolve the body skins arc1_a/b/c and Bow/Arrow attachments. Standing/Walking bounds should be 170–188 world units,
identical between tiers within 0.1; native target 179.199232, current model 180.741.
Keep scale 106.382287 and yaw −π/2. Attack/Cast combined weapon bounds should remain in the 170–215 envelope.
Assert eight clips, 63 joints, three variants, four colour and four shadow LODs, one body primitive per level.
Current body triangles: [9531, 5223, 1904, 620]; bow [2108, 1150, 420, 193]; arrow [92, 40, 5, 4].
The final LOD chain strictly decreases and stays below all installed component counts. Inspect switch transitions,
every shadow quality and real-GPU crowd cost. Additional Attack-release silhouette diagnostics are 0.984 / 0.963 /
0.926 IoU at LOD1/2/3; the calibrated Standing eight-view pooled IoU gate passes at all distances.

Case: mm6_archer_arrows_release_from_the_drawn_bow. Attack a valid target with each tier.
Attack 0.800 s launches from Socket_Arrow_Release, 8 cm ahead of the arrow rest. The arrow is full-sized through
0.800 s and hidden by 0.82222 s while the string snaps back. Check a single projectile handoff, target direction,
repeated-attack pacing and follow-through. The clip lasts 1.15556 s, versus native 1.1875 s.
B/C retain table-owned ArrowF secondary probabilities. The fallback melee role still shares Attack.

Case: mm6_fire_archer_cast_uses_the_bow_shot. Tier C has the table-owned Fireball spell.
The distinct Cast clip is an exact copy of Attack and releases at 0.800 s from Socket_Arrow_Release.
Check that the fireball replaces the arrow projectile without a palm gesture, duplicate missile or delayed FX.
All tiers bind cast: Cast; no palm_right socket alias remains. WorldFxSystem must accept the distinct clip name.
The unused Socket_Palm_Right skeleton node has no event binding.

Case: mm6_archer_relaxed_rest_and_closed_carry. Compare Standing/Fidget with native arc1sta0.
Both feet stay flat; arms hang beside the body; the left fingers and thumb enclose the grip wrap.
The bow hangs vertically with its string inward. Both bracers remain brown leather on all three tiers.
Walking swing soles rise about 9 cm, knees flex about 54–59 degrees, and one support sole stays grounded.
Feet face travel; the free palm faces the thigh. Walking stride_length is 1.02417324 m.
Running intentionally aliases Walking. Check table speeds 140/150/160 for correct pacing and no visible sliding.
Check relaxed two-second Fidget, Attack/Cast/Hit rest entry and return, Death into held Dead, bow/calf clearance,
and head look stopping on death. Collision and combat dimensions remain table-owned.

After integration, run the existing MM6 actor suite and these cases; capture all tiers beside sprites indoors in
6d19.blv and outdoors in oute3.odm. Include draw/release, bow-fireball Cast, bracers, grip, soles, face and corpse.
Check look overlays, engine palette brightness and lighting. Browser tiers bake the runtime ramps for review;
the runtime body uses shared maps and native region ramps.
