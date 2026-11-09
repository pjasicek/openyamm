# MM6 BLich (lch) — Codex project

**Review round 2 is partial, not ready for integration.** LOD0 passes the 700px visual gate after accepted-surface rebaking. Far quality and absolute rig criteria remain unmet; read [HANDOFF.md](HANDOFF.md) before using the staged export.

| LOD | Accepted before | Round 1 | Round 2 | % LOD0 | Actor px | Pooled IoU | Min IoU | Min SSIM, all tiers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 16,274 | 7,824 | 6,290 | 100.0% | 700 | 0.992919 | 0.991397 | 0.972880 |
| 1 | 8,135 | 7,787 | 3,466 | 55.1% | 550 | 0.973773 | 0.970297 | 0.883467 |
| 2 | 2,907 | 6,916 | 2,907 | 46.2% | 220 | 0.943076 | 0.939496 | 0.895645 |
| 3 | 897 | 6,710 | 897 | 14.3% | 88 | 0.841303 | 0.816976 | 0.750558 |


Native identity is a crowned skeletal caster with breastplate, bracers, boots and ochre tatters; no added robe, staff or shield. The source restoration project ../mm6_lch/ is read-only. Accepted clips, tiers, sockets and bindings are unchanged. Installation is orchestrator-owned. Budget remains 30/100 credits, no new jobs.

[Method, curves and renders](review/triangle_rebake/README.md), [artifact hashes](review/triangle_rebake/artifact_hashes.json), [bindings](integration/actors.yml), [regression proposal](integration/regression.md), [viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_lch_codex/review/viewer/).

Unattended decisions: honor the user's lower historical count caps despite the differing installed snapshot; preserve accepted cheap LOD2/3 geometry after cheaper trials failed; rebake each selected LOD and fit maps into the existing shared body/head set dimensions; preserve frozen clips and explicitly report failures. No failed threshold is treated as a pass. Round-1 records are archived in review/triangle_rebake/round1_archive/.
