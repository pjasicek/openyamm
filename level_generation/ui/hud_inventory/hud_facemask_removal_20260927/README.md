# HUD facemask removal — 2026-09-27

User instruction: “ok then remove it from the hud”.

The shared gameplay HUD no longer loads or draws `FACEMASK`. Its green corners were visible as a
rectangle around the accepted transparent portraits, as shown in `test_img/2068.png`.
The three party-strip bindings in `assets_dev/engine/ui/gameplay/gameplay.yml` are removed.

Rendering and pointer hit tests now share an explicit 60×80 logical portrait viewport in
`GameplayHudCommon`. This preserves the previous viewport, insets, spacing, and selection-ring
placement without deriving geometry from the discarded overlay. The portrait effects and ring
remain in their existing draw order. The port 9100 review also omits the facemask.

All 4,032 accepted portrait PNGs and the 9,920-file accepted index remain unchanged.
The unused facemask artwork is retained as part of the accepted asset history.

## Input reconciliation

`input_reconciliation.json` retains the earlier inventory-grid reconciliation and adds only the
three removed `asset.default: FACEMASK` bindings. `before/gameplay.yml` and `current/gameplay.yml`
retain both exact input versions; `before/viewer.js` retains the old preview implementation.
`ledger_update.json` records the successor receipt pointer. The frozen target contracts and
earlier receipts are preserved. PC acceptance validation checks the successor receipt hash and
its link to the original reconciliation before allowing this explicit ledger update.

## Validation

- `deploy_icons.py --check`: all 9,920 accepted runtime images match; no pending installs.
- `pc_transparent_acceptance_20260927/validate.py`: all 4,032 transparent portrait exports match
  the accepted revision and runtime copies.
- Port 9100 browser check: all 72 family galleries, both ring layouts, guides, offsets, downloads,
  and acceptance status pass. See the sibling regeneration workspace's `browser-check.json`.
- Normal `openyamm` and `openyamm_unit_tests` builds pass. The three focused HUD classification
  and mobile-layout tests pass with 61 assertions.
- [Native capture](runtime.png): the extra mask rectangle is absent; the portrait and gold ring
  retain their placement. The isolated MM6 run completed on OpenGL 3.3 / NVIDIA GeForce RTX 3060 Ti.
  [Validation record](validation.json) retains the executable and screenshot hashes and run location.
