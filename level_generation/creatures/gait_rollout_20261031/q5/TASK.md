Package q5 of the 2026-10-31 gait rollout (added 2026-11-06, one model): give the installed MM9 wolf
(`assets_source/worlds/mm9/models/mm9_wolf.glb`: Grey, Red and Black Wolf, MM9 monsters 9114-9116, descriptors
MM9 Wolf A-C) a procedural Trot, install and bind it.

Why (devdocs/mm9_rework/MM9_ANIMATION_AUDIT.md A8 and P5): Walking (stride 1.96, 0.9 s) covers about 87 world units/s
at scale 40, Running (4.18, 0.4 s) about 418; the engine plays one loop per stride, caps at 2x and picks walk, run or
sprint by the least misfit, so the wolf wandering at MM9's WalkVel plays its run in slow motion. Author the trot for
the speeds the AI actually uses (measure them), on the rollout's quadruped method (../README.md, q2, q3's
quad_gait.py) mapped to the MM9 skeleton: same foot at phase 0 as Walking, planted paw headings as Standing/Walking,
the wolf's carriage, floor rules, loop seam, stride measured. Graft onto the installed source with
graft_clips.py (byte check, rollback copy in work/rollback/), install with tools/install_model.py, bind all three
descriptors in assets_dev/worlds/mm9/models/actors.yml under its flock, check in the creature viewer and in the MM9
arenas that use wolves. No Meshy spending.
