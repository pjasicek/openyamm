# Proposed regression — orchestrator owned

Name: `mm6_minotaur_actor_tiers_axe_and_spell_socket`.
World MM6; controlled indoor fixture `6d07.blv`, outdoor fixture `oute3.odm`.
Summon **580, 581, 582**. Native encounter follow-ups: `outb1.odm` (Kriegspire), `6t4.blv` and `cd3.blv`.
Use existing actor-tier fixtures structurally; add no duplicated gameplay implementation.

| Descriptor | Name | Native scale | Expected Standing body height | Proposed bound |
|---|---|---:|---:|---:|
| BMinotaur A | Minotaur | 0.699997 | 186.9 | 178–196 |
| BMinotaur B | Minotaur Mage | 0.799988 | 213.6 | 203–224 |
| BMinotaur C | Minotaur King | about 0.9 | 240.3 | 228–253 |

The native Standing alpha height is **267 pixels**, not the padded 285-pixel canvas. The posed body is
1.851913962 m; A scale is 100.92261513. B/C use `scale_reference: BMinotaur A`.
Exclude the attached axe from height measurements. Check B/A ≈ 8/7 and C/A ≈ 9/7 within 1%, plus the absolute bounds.
Inspect facing (+Z exported forward, yaw offset -π/2), floor contact, body widths and the axe silhouette visually.

Check all nine clips and three skins, four colour and four body shadow LODs, the 82-joint skin and rigid `Axe`
attachment with four LODs. Skin weights and material extensions already pass the offline loader-contract check.
Validate frame interpolation, role transitions, flat Standing/Fidget soles, walk/trot foot sliding, Hit/Fidget prop
reaction, backward collapse, axe release, and exact Death→Dead continuity. Body/weapon base textures are shared
across tiers. Inspect steel under both indoor and outdoor lighting and all shadow qualities.

Melee impact is **0.947917 s** into Attack. The distinct Cast holds its chamber and releases at **1.516667 s**
from `Socket_Axe_Head`. Mage has Lightning Bolt M12 and King Finger of Death N14 (20%); retain existing gameplay
spell logic. Confirm both real spell launches, facing and socket position. The ranged fallback binds Attack with the same impact as melee; only Cast has the launch socket.
Stride is **1.398605 m** from twice the mean Walking foot excursion. Native move speeds are 250/260/300;
A's fitted 0.6 s trot gives approximately 235 units/s before runtime synchronization.

Look limits are a conservative proposed 35° yaw / 20° pitch. Validate them while aiming at the party, since the
authored-pose gates do not exercise procedural runtime look or state transitions. Run existing MM6/7/8 model and
sprite smoke checks to catch shared-registry regressions. Verify native runtime cost on the integration machine.

No build, installation, regression, game launch or GPU game capture was performed in this production session.
These checks are explicitly assigned to the orchestrator by the Batch rules.

Review round 1: inspect the reported feet and frame-28/frame-40 wrist views, heavy wind-up/release/recovery, eight-influence skinning and LOD switches at 550/220/88 projected AABB-diagonal pixels.

## Review round 2

Accepted Attack spatial motion retained; early wind-up shortened by 20%; impact 0.947917 s.
Head/neck curves smoothed; rigid horn weights retained. Death now uses local Two Handed Sword Death:
single backward fall, axe release at 0.18 s, gravity drop and held terminal Dead pose.
Inspect Death at 0.1875, 0.375, 0.75, 1.5 and 2.4 s. Inspect the old Attack 34–39 phase after the timing shift.
Current shared-gate failures and missing head/neck/full-body/axe floor coverage are explicit in HANDOFF.md.
Historical custom gate passes are not evidence for this export. No game checks were run.
