# MM6 BArcher arc1 — review round 6

Attack and its exact Cast copy now play 1.5x faster: 1.155556 s duration, 0.800 s release. Staged actor events updated. Accepted poses, meshes, bracers, LODs and textures are preserved; memory remains 53.125 MiB.

All 63 bone transforms match exactly at Walking, Standing and Fidget loop endpoints: 0 mm / 0 degrees. Running aliases Walking. Endpoint heel/toe heights are 3.14–4.48 mm; the last Walking sample before wrap stays below 6.22 mm. No loop pose correction was necessary.

[HANDOFF.md](HANDOFF.md) records files, hashes, counts, decisions and validation. Bindings and all 24 viewer switches pass. Shared gates still report 363 failures (361 in R5); existing contacts are accepted-as-is for this narrow pass, not certified as passing. No game/build/install/commit. Budget 40/100 credits; lease released at handoff.

![Loop endpoints](review/round6/loop_comparison.jpg)

[Attack timing](review/round6/attack_timing_comparison.jpg) · [Shared audit](review/round6/SHARED_AUDIT.md) · [Viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_arc1_codex/review/viewer/).
