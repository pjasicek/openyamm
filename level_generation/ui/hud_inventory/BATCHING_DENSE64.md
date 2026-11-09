# Dense spritesheet batching — approved 2026-09-16

User choice: **at most 64 small targets per imagegen sheet**. This supersedes the old nine-cell default for
the prepared dense portrait/small-icon bundles. Larger cells use fewer slots. Preserve complete character and
state groups when practical. A density setting is not permission to waive native geometry or visual acceptance.

For GUI overlays, determine whether a legacy BMP's backing belongs to a separately restored panel before
packing. Follow [GUI foreground transparency](MATTE_AND_FITTING.md#gui-foregrounds-over-separately-restored-backgrounds):
restore those foregrounds on transparent PNG canvases, preserving native placement. Keep complete backgrounds
opaque, record any session-local compositing override, and pack only compatible output compositing roles together.

## What the tool actually returned

[Five measured generation experiments](experiments/dense_portraits_20260916/README.md) returned approximately
**1.57 megapixels**, distributed according to aspect ratio. Requests for 2K/3K did not increase that budget.
75 portraits passed the strict rectangle size check with almost no margin; 81 did not. All native portraits in
those tests were 59×79. This observed envelope is not a documented tool input limit or a guaranteed future output.

## Maximum width/height for useful 2x results

There is no independent maximum width and height: the **combined native-coordinate sheet area**, including
gutters and empty cells, determines available sampling. Packing must account for the actual returned aspect ratio.

Preparation uses native images enlarged exactly 2×, two native pixels of padding on each side, and no labels.
For native cell `w×h`, grid `c×r` has dimensions `Wn=c*(w+4)` and `Hn=r*(h+4)`, plus any exterior padding.

Predicted generated sampling = `sqrt(1,572,000 / (Wn*Hn))` when output preserves the sheet aspect ratio.
Require **at least 2.15 predicted** to leave modest room beyond the strict 2.0 minimum; validate actual results.
Equivalently, a reference displayed at 2× should occupy **no more than about 1.36 megapixels**.
Use sheet aspect ratios from 1:2 to 2:1. For elongated individual artwork, add exterior padding instead of warping it.

Illustrative upper reference envelopes under that policy (not independent limits):

| Reference shape | Maximum illustrative reference dimensions |
| --- | --- |
| Square | 1166×1166 |
| 3:2 landscape | 1428×952 |
| 2:3 portrait | 952×1428 |
| 2:1 wide | 1648×824 |
| 1:2 tall | 824×1648 |

**64 player portraits:** 8×8 grid of 63×83 native-coordinate cells = 504×664 native sheet,
or **1008×1328 reference pixels**. Each portrait rectangle in that reference is 118×158, with eight reference
pixels between neighboring portraits. Predicted returned sampling is about **2.17×** under the observed envelope.
This 64-cell production preparation is calculated from the measured tests; no separate 64-cell generation was run.

64 native 128×128 icons do NOT fit this policy: reduce their count. Do not shrink individual reference artwork
relative to its native coordinates to force 64 cells into a sheet. Keep each full canvas, margins and anchor.

## Return checks

- **2026-09-16 user correction:** a dense result can clear the pixel budget yet still be an enlarged pixelated
  image. PC-003/S001 did so. A stronger reconstruction prompt improved that same 50-cell sheet. For the local
  run, use `chat_bundles/dense64_20260916/RESTORATION_DETAIL_V2.txt` and the per-output generation gate.
  Inspect both outer contours and interior shading at master resolution; pause on remaining enlarged blocks
  or uncertainty. Recording a defect is not enough reason to keep bulk-generating with the same prompt.
- Retain original full-resolution master, exact prompt, model/tool, actual dimensions and input hashes.
- Check slot count/order and actual portrait/icon boundaries before extraction. Measure sampling per cell.
- Require at least 2 actual generated pixels per native pixel in both axes. Upsampling a smaller raw result
  cannot repair insufficient sampling. Oversized empty margins cannot count as restored subject detail.
- Whole-sheet dimensions are a preliminary guard only. One landscape experiment stretched its last row and
  compressed another below 2x despite apparently sufficient global dimensions.
- Inspect full-resolution detail and final x2 appearance. Canvas dimensions do not prove expression, identity,
  silhouette, internal landmarks or useful reconstructed detail. No automatic visual acceptance.
- Opaque PC/NPC/house artwork retains its complete background. Cutouts need matte/edge review. Key-aware assets
  retain original indexed sources and all consumer-profile contracts; do not flatten incompatible profiles into
  a single RGBA interpretation.

## Preparation, ownership and handoff

`dense_bundles.py` prepares native-reference first passes without generation. It excludes retained attempts,
accepted/deferred/review work, known experiment results and active claims. Exact matching source appearances
become explicit reuse candidates, preserving every target ID; reuse still needs local review and acceptance.

The small-art scope is MM6/MM7/MM8 PC/NPC portraits, inventory icons, legacy small UI/state/panel artwork with
native edges <=256. Full maps/backgrounds, equipped paperdoll parts, large/linked animation, spell-page-dependent
icons and other specialized jobs stay on their own workflows. `catalogue.json` accounts for exclusions by ID.
Original palettes, per-target source hashes, dimensions, timings, native identity context and frozen job contracts
travel with each sheet. State families stay together; complete PC families are kept separate where possible.

New assignments explicitly supersede overlapping unreturned old assignments, with a history and pre-change state
snapshot. Do not run both versions. Keep late older returns for explicit reconciliation; never discard their art.
No existing accepted art, attempts or runtime assets are changed by preparation.

Workers return unchanged `manifest.json`, original `outputs/raw/SNNN` images, exact
`outputs/prompts/SNNN.txt` and `outputs/progress.json`. Raw-only partial returns are supported. No cloud integration
is needed. `catalogue_dense_returns.py` verifies and inventories these returns without executing returned code,
accepting artwork or changing production status. Dense manifests are not old nine-cell importer manifests.

For a returned individual bundle ZIP, run from the repository root:

```sh
python3 level_generation/ui/hud_inventory/catalogue_dense_returns.py \
  --batch-root level_generation/ui/hud_inventory/chat_bundles/dense64_20260916 \
  --output level_generation/ui/hud_inventory/dense_returns \
  /path/to/returned_bundle.zip
```

The tool saves the original ZIP, immutable incoming files, `intake.json` with each source ID, and an `index.html`
raw-sheet gallery. Unreturned targets stay explicit. Subsequent extraction must locate actual returned cell
boundaries and preserve the raw; the nominal input grid is not proof of output alignment. Final PC expression
acceptance still needs an accepted identity seed and cross-expression comparison under the existing queue rules.
