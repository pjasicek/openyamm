# monster_nosferatu (overnight-nosferatu)
Done 08:10, 2026-10-31. Installed, bound (MM9 Nosferatu A/B/C), viewer r12, review root refreshed, lease released. Credits 20/40. Project level_generation/creatures/mm9_nosferatu_claude, README there with gates, deviations, open points, not-checked list.
Gates still over: collapse not zero (shoulder 25, Dead robe 141 hidden mostly), AttackRanged L hand 2.1 cm 3 frames, Fidget L 1.2 cm, Taunt L 1.4 cm. Cloth through robe 0 in every clip, jitter 0, detached 0, floor ok, regression PASS.
Rebuild: python3 scripts/tweak_mesh.py; scripts/finish_nos.py; scripts/tier_ramps.py; scripts/rebuild.sh --install (claim a lease and put the token in scripts/env.sh first). Never re-run uv_nos.py.
Background: none.
