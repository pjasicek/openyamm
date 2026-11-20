# MM6 PeasantM4 / natm — review round 6

Cannibal / Head Hunter / Witch Doctor, male. **50/100 Meshy credits total; zero this round.**

Smoothed the late Attack pelvis surge while keeping foot targets and the accepted arm/spine rotations.
Attack is **1.145833 s** (was 1.187500 s). Two redundant transition frames are removed; the 12-frame (0.25 s)
synchronized recovery is retained at frames 43–55. No multi-frame hold remains.

Impact moves **0.906250 → 0.739583333 s**; all six melee/ranged actor events are updated. Cast is unchanged.
Shared gates, dense shaft probes, bindings and viewer pass. Geometry, materials, textures, other clips and props
remain unchanged. [HANDOFF.md](HANDOFF.md) records files, hashes, counts, measurements and reproduction.

[Attack sheet](review/sheets/Attack.jpg) · [close-ups](review/round6_smoothing.jpg) ·
[speed comparison](review/round6_velocity.png) · [viewer](review/viewer/index.html).

Recorded decision: spread the translation responsible for the jerk instead of changing accepted arm poses;
retain one continuous turnaround interval to ease the offhand direction change, with no held run of frames;
shift the existing recovery intact and bind impact to measured aimed tip speed. No new paid work or texture work.
Native installation, game checks and captures belong to the orchestrator. No build, game launch or commit.
