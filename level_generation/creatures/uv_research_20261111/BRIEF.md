# UV unwrap and Meshy preparation research (2026-11-11)

Coordinator: session openyamm-61. Research only: nothing here is installed or promoted, no `assets_dev` /
`assets_source` file and no other project's files are changed. Every output stays in this folder.

## Question

What is the most effective, usable way to UV unwrap and prepare a reduced creature mesh for a Meshy retexture
(`enable_original_uv`, multiview HD masters, meshy-7), compared to the current route in
`claude_shared/TEXTURE_QUALITY_PASS.md` and `claude_shared/uv_atlas.py` (xatlas charts, small-chart merge + SLIM,
one texel density with a denser head, xatlas brute-force pack, 2 px margin at 2048, 4K paint downsampled once)?

Current results: Magreeb 54 % atlas, Dragon King 55.9 %, PeasantF3 60 %. Targets: atlas 70 % ideal / 55-60 %
realistic, density spread p90/p10 <= 1.3, fragment surface <= 3 %, stretch p90 <= 1.5.

## Candidates

1. **PartUV** (SIGGRAPH Asia 2025, arXiv 2511.16659, project page zhaoningwang.com/PartUV): semantic part
   decomposition (PartField) + recursive splitting under a distortion threshold, ABF flattening. Claims far fewer
   charts than xatlas/Blender at similar distortion, built for AI-generated meshes. Check code availability and licence
   (research use only is fine here; record it). It addresses why our `charts='bones'` trial failed (spiky segments
   collapsed under SLIM).
2. **Hidden-seam bias**: a visibility/ambient-occlusion cost in the chart cutting or merge step so seams prefer
   underarms, inner legs, under the chin, back of the head, undersides.
3. **Gutter fill / margin**: do Meshy colour returns fill the empty space around islands with the island's own colour
   (dilation)? If not, distant mips mix neighbouring islands at a 2 px margin. Test a dilation step and/or wider margins
   and what each costs in atlas use.
4. **Packing**: anything free that beats our xatlas brute force / fast sweep on the same charts (Blender 5.x packer
   options, other open packers). UVPackmaster is paid: note only.
5. **Paint resolution**: 8K vs 4K retexture (meshy-7 API accepts `texture_resolution: "8k"`; PBR maps stay 4K, no
   emission at 8K), both downsampled to 2K once. Check the credit cost first.
6. **Meshy noise floor**: the same upload painted twice shows how much of a difference between two layouts is just
   Meshy's randomness. Needed before claiming a winner.

Other well-founded candidates found during the research may be added; record why.

## Measurement

`claude_shared/texture_quality.py <glb> --by-bone --heatmap <out>/heat --json <out>/quality.json` on every layout and
every paint: atlas use, equivalent px, density p10/p50/p90 and spread, islands, fragment surface, stretch p90. For
paints also the speckle/blotch measure used in the PeasantF3 redo (see `mm6_mfp_texpass_claude/`) and identical-camera
close-up sheets (face, hands, chest, a seam region) at 2K runtime resolution, plus one distant (mip) view.
Layouts are compared first with zero credits; only layouts that win on the numbers get painted.

## Budget and rules

- Meshy: at most 100 credits in total for this study (a 4K retexture is 10 credits). Run jobs only through
  `tools/creature_meshy.py` (it falls back to the backup account). Keep a ledger in `LEDGER.md` (job, credits,
  purpose, result). Before any job, check its cost; stop and report to the coordinator if the next job would pass 100.
- Test subjects come from session openyamm-b9 (see `SUBJECTS.md` once assigned). Until then, zero-credit layout work
  may use already-finished bodies read-only (e.g. the Magreeb's upload GLB in `mm9_magreeb_claude/`), copied into
  this folder first.
- Blender through `tools/run_creature_blender.sh`. Do not edit `claude_shared/` tools; copy into `scripts/` here
  and change the copy. Never run a `-j` game build while a converter runs; no game build is needed for this study.
- After creating files here, run `python3 level_generation/update_gitignore.py`.
- No `git add/commit/stash/reset`.

## Deliverable

`REPORT.md`: method, every trial with numbers and sheets, credits spent, the winner per question, and a concrete
recommended change to `uv_atlas.py` / `TEXTURE_QUALITY_PASS.md` (as a proposal; do not apply it).
