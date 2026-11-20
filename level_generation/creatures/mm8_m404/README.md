# MM8 Lizardmen Warrior restoration

> **Installed model reduced (2026-10-19):** the installed body and sword are now the reduction from [`../mm8_m404_reduce_claude/`](../mm8_m404_reduce_claude/README.md) (LOD0 11,229 + 932 -> 8,981 + 660; animation unchanged). This project's exports remain the unreduced production; rollback sources are in `../mm8_m404_reduce_claude/work/`.

> **Walk reworked (2026-10-19):** the installed Walking is the full-body walk from [`../mm8_m404_walk_claude/`](../mm8_m404_walk_claude/README.md) (undamped upper body, 1.45 m stride with heel-toe roll, tail counter-swing; every other clip unchanged), with `stride_length`/`run_stride_length` 1.45 in actors.yml. A re-export from `3d_claude/` brings the old damped walk back unless `../mm8_m404_walk_claude/scripts/author_walk.py` is re-run on it.

The completed rigged 3D warrior is documented in [3D production](3d_claude/README.md), with its [animation viewer](review/viewer/).

Validated staging package for all 160 native unique frames, all native actions, five stored views and eight logical directions with native mirrors. No missing sources, aliases or orphan frames. The original sprites are unchanged; this 2D atlas package remains separate from the installed 3D model.

Open `viewer.html` directly. Palette 405 preserves gray-blue scales, red spines and trim, green mantle, brown leather and the wavy silver sword. Deterministic palettes 406 and 407 reproduce the native blue and red mantle variants. Masks come from enhanced artwork and native palette correspondence; all variants share alpha, geometry and placement. Metadata retains exact native timing, playback, mirrors, logical dimensions and anchors.

The 2× package has seven RGBA8 atlas pages and seven matching R8 mask pages: 120,261,120 decoded bytes (96,208,896 color and 24,052,224 mask), including 30,487,605 bytes of packing overhead. Native 256×256 logical canvases, transparent margins, 16-pixel atlas gutters, three-pixel hidden bleed and no mipmaps are preserved.

All 26 base sheets use built-in imagegen. Exact prompts, all 27 raw generations, native references, accepted identity and registration checkpoints, rejected rear attack and alignment contacts are retained. Rear attack revision 2 corrects front-facing heads in the first three poses. Frozen shared batch transforms and documented lower-row translations correct demonstrated sheet spacing without individual pose fitting. Native coarse RGB plus 0.7× enhanced fine detail preserves tonal weight. Eight-neighbor inverse-fourth-power native palette interpolation performs deterministic recoloring through enhanced-art coverage masks. RGB-only contour correction preserves alpha and measured native chroma allowances.

Visual review covers all 26 registration contacts, 26 native/final atlas contacts, 26 three-palette/mask contacts, magnified light/dark contours and a mirrored rear-side attack in the actual viewer. Browser checks pass 480 variant decodes, 160 stored poses, 192 animation tracks and 1,008 timing boundaries. Export checks verify full source coverage and hashes, exact atlas reconstruction and matching mask placement, base bypass and identical variant alpha. Every audited edge stage has zero excess over measured native allowances.

To revise, reuse retained raw outputs and run `python3 level_generation/creatures/mm8_m404/rebuild.py`. Review changed contacts, run `browser_checks.py` through the authorized offline wrapper, renew `review/decision.json` hashes, run `finalize.py`, then refresh `inventory_remaining.py`. Rebuilding does not accept changed artwork. The acceptance seal verifies reviewed artifacts, not merely manifest existence.
