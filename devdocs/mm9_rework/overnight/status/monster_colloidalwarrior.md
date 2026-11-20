# monster_colloidalwarrior (run2-colloidalwarrior, second pass done 2026-11-01)
Phase: DONE (second pass). r9 installed (assets_source/worlds/mm9/models/mm9_colloidalwarrior.glb), bindings unchanged (MM9 Colloidal A/B/C), review root refreshed.
Credits 20 / 30 (second pass 0). Lease released. No Chrome/Blender left.
Regression PASS 158/65/0; viewer check 48/0; floor ok; bones/detached/flat/winding 0.
Fails: jitter 5 strict / 2 relative; Death2 R hand 6.0 cm (7 frames); collapse not zero (Death2 head 93, Hit2 41, AttackMelee R shoulder 55).
Details: level_generation/creatures/mm9_colloidalwarrior_claude/README.md "Second pass".
Rebuild: REV=rN scripts/rebuild.sh [--install] (texture-only: SKIP_EXPORT=1 SKIP_CLIPS=1).
