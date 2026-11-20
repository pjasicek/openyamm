# MM8 m400 — Lizardmen Male (Peasant)

Validated offline staging restoration of all 170 native source files: 105 descriptor-referenced frames and 65 unused stored poses, across five stored directions and eight logical viewing directions. Three native variants use palettes 401, 402 and 403. Originals and gameplay assets are unchanged.

Open `viewer.html` locally. It renders the exported atlas and matching material masks and compares them with the native palette image. The stored-pose selector exposes every native file without inventing animation timing. Browser capture should allow 10 seconds of virtual loading time for cold atlas pages.

`manifest.json` contains the 2× runtime atlas placement, native logical sizes, per-step anchors, mirror flags, scale, timing and variant coefficients. `sources.json` retains exact native descriptors and frame-group records, indexed-image hashes and palette provenance. The native attack slots deliberately use walking art; separate unused attack poses remain available. Death consists of two hit poses and four falling poses before corpse hold. Native de/df/dg legacy reptile poses keep their distinct bare scales, tails and head spines.

The six RGBA8 atlas pages and six RGB8 mask pages require 131,405,568 uncompressed bytes including packing. Masks use two material channels and a zero third channel. The base palette bypasses recoloring exactly; alternative variants use fixed native-palette luminance fits. Alpha stays unchanged. Packing uses 16px gutters, 3px matching hidden RGB/mask bleed and no mipmaps.

Runtime size is 2×. Actual generated visible-height ratios range from 1.52× to 2.58× native, with median 1.65×; `registration.json` records each frame's actual generation size and shared sheet scale. The export does not claim uniform 2× new generated detail.

Prompts, all raw imagegen outputs, the accepted standing reference and generation timestamps remain in `prompts/`, `raw/` and `checkpoints/`. The rejected painted-checkerboard identity output remains preserved. Processing settings, exact crop adjustments, material selections and final pale-edge correction are retained in the scripts and JSON reports.

Review evidence is in `review/acceptance.json`, `review/decision.json`, all batch native/restored and variant contacts, six final edge sheets, the five-view death-transition sheet and runtime browser captures. `validation.json` covers complete native-file coverage, exact crop/atlas reconstruction, unchanged source hashes, palette/alpha checks and browser checks: 510 atlas variant decodes, 192 tracks, 888 timing boundaries and 170 stored poses.

To rebuild from retained raw outputs, run each selected batch through `process.py` with its recorded prompt and accepted identity reference; then run `final_edge_cleanup.py`, `package.py`, `upgrade_viewer.py`, `review_contacts.py`, `review_evidence.py` and `browser_checks.py`. Review changed outputs before replacing the accepted decision and invoking `finalize.py`. Finally refresh `inventory_remaining.py`. All commands can use the authorized `/home/pjasicek/Downloads/mm8_creature_restore.py run mm8_m400/<script>.py ...` entry point.
